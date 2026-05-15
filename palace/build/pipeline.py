from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from palace.build.ast_extractor import extract_ast
from palace.build.edge_weighter import final_weight
from palace.build.git_analyzer import cochange_edges
from palace.build.llm_extractor import extract_semantics
from palace.build.network_serializer import Edge, Node, Room, build_network_json
from palace.build.room_classifier import classify_rooms
from palace.build.room_writer import write_rooms_and_palace
from palace.utils.cache import ensure_output_dirs, load_json, sha256_bytes, write_json
from palace.utils.language_detect import detect_language
from palace.utils.token_counter import approx_token_count


DEFAULT_IGNORES = {
    ".git",
    "palace-out",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".cache",
}

EXCLUDE_PATTERNS = (
    "docs_src/",
    "docs/",
    "examples/",
    "cookbook/",
    ".github/",
)


def _is_ignored(path: Path) -> bool:
    parts = set(path.parts)
    return any(p in parts for p in DEFAULT_IGNORES)


def _is_documentation_file(rel_id: str) -> bool:
    rid = rel_id.replace(os.sep, "/")
    return any(pat in rid for pat in EXCLUDE_PATTERNS)


def _iter_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if _is_ignored(p):
            continue
        # Skip docs/examples-heavy trees (FastAPI has hundreds of docs_src fixtures)
        try:
            rel = str(p.relative_to(root)).replace(os.sep, "/")
        except Exception:
            rel = str(p).replace(os.sep, "/")
        if _is_documentation_file(rel):
            continue
        lang = detect_language(p)
        if lang is None:
            continue
        files.append(p)
    return sorted(files)


def _read_text(p: Path) -> str:
    return p.read_text("utf-8", errors="replace")


def _file_hash(p: Path) -> str:
    data = p.read_bytes()
    return f"sha256:{sha256_bytes(data)}"


def _rel_id(root: Path, p: Path) -> str:
    return str(p.relative_to(root)).replace(os.sep, "/")


def _read_cached_ast(cp, file_hash: str) -> dict[str, Any] | None:
    cache_path = cp.extractions_dir / f"{file_hash.replace(':', '_')}.json"
    cached = load_json(cache_path, default=None)
    if not cached or "ast" not in cached:
        return None
    return cached["ast"]


def _read_cached_llm(cp, file_hash: str) -> dict[str, Any] | None:
    cache_path = cp.extractions_dir / f"{file_hash.replace(':', '_')}.json"
    cached = load_json(cache_path, default=None)
    if not cached or "llm" not in cached:
        return None
    return cached["llm"]


def _write_cached_llm(cp, file_hash: str, llm_obj: dict[str, Any]) -> None:
    cache_path = cp.extractions_dir / f"{file_hash.replace(':', '_')}.json"
    cached = load_json(cache_path, default={"hash": file_hash})
    cached["hash"] = file_hash
    cached["llm"] = llm_obj
    write_json(cache_path, cached)


def _resolve_import(from_path: str, module: str, all_files: set[str], language: str) -> str | None:
    # JS/TS relative imports: ./foo, ../bar, or bare package (ignore)
    if language in {"javascript", "typescript"}:
        if module.startswith("."):
            base = Path(from_path).parent / module
            candidates = [
                str(base.with_suffix(ext)).replace(os.sep, "/")
                for ext in [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]
            ]
            candidates += [
                str((base / "index").with_suffix(ext)).replace(os.sep, "/")
                for ext in [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]
            ]
            for c in candidates:
                if c in all_files:
                    return c
        return None

    # Python: pkg.mod -> pkg/mod.py or pkg/mod/__init__.py
    if language == "python":
        mod = module.strip()
        if mod.startswith("."):
            return None
        parts = mod.split(".")
        cand1 = "/".join(parts) + ".py"
        cand2 = "/".join(parts) + "/__init__.py"
        if cand1 in all_files:
            return cand1
        if cand2 in all_files:
            return cand2
        return None
    return None


def build_palace(repo_path: Path, *, use_git: bool, use_llm: bool, model: str | None) -> None:
    repo_path = repo_path.resolve()
    palace_out = repo_path / "palace-out"
    cp = ensure_output_dirs(palace_out)

    manifest = load_json(cp.manifest_path, default={"files": {}})
    prev_files: dict[str, str] = manifest.get("files", {})

    source_files = _iter_source_files(repo_path)
    file_ids: list[str] = []
    nodes: dict[str, Node] = {}

    # hash + node population (deterministic)
    for p in source_files:
        fid = _rel_id(repo_path, p)
        file_ids.append(fid)
        content = _read_text(p)
        lang = detect_language(p)
        h = _file_hash(p)
        nodes[fid] = Node(
            id=fid,
            type="file",
            room_id=None,
            subtree_id=None,
            label=p.stem.replace("_", " "),
            summary=None,
            symbols=[],
            language=lang,
            size_tokens=approx_token_count(content),
            activation=0.0,
            hash=h,
        )

    # Ensure AST cache exists for every file (read back)
    # We write extraction cache in our own format for determinism.
    # If changed, write extraction JSON.
    for p in source_files:
        fid = _rel_id(repo_path, p)
        lang = detect_language(p)
        content = _read_text(p)
        h = nodes[fid].hash or _file_hash(p)
        cache_path = cp.extractions_dir / f"{h.replace(':', '_')}.json"
        if not cache_path.exists() or prev_files.get(fid) != h:
            extraction = extract_ast(lang, content)
            write_json(
                cache_path,
                {
                    "hash": h,
                    "ast": {"language": lang, **extraction.to_json()},
                },
            )

        ast = _read_cached_ast(cp, h)
        if ast:
            nodes[fid].symbols = [s["name"] for s in ast.get("exports", []) if isinstance(s, dict) and s.get("name")]

    all_file_set = set(file_ids)

    # Optional LLM pass (cached by file hash)
    if use_llm:
        to_extract: list[tuple[str, str]] = []
        for p in source_files:
            fid = _rel_id(repo_path, p)
            h = nodes[fid].hash
            if not h:
                continue
            llm_cached = _read_cached_llm(cp, h)
            if llm_cached and isinstance(llm_cached, dict) and llm_cached.get("summary"):
                continue
            to_extract.append((fid, _read_text(p)))

        if to_extract:
            try:
                max_conc = int(os.environ.get("PALACE_LLM_CONCURRENCY", "1"))
                llm_results = extract_semantics(files=to_extract, model=model, max_concurrency=max_conc)
            except Exception as e:
                print(f"LLM extraction skipped: {e}")
                llm_results = {}

            for fid, obj in llm_results.items():
                h = nodes[fid].hash
                if not h:
                    continue
                # normalize and cache
                summary = str(obj.get("summary") or "").strip()
                room_suggestion = str(obj.get("room_suggestion") or "other").strip()
                sem_edges = obj.get("semantic_edges") or []
                if not isinstance(sem_edges, list):
                    sem_edges = []
                _write_cached_llm(
                    cp,
                    h,
                    {
                        "summary": summary,
                        "room_suggestion": room_suggestion,
                        "semantic_edges": sem_edges,
                    },
                )

    # Load summaries into nodes
    if use_llm:
        for fid in file_ids:
            h = nodes[fid].hash
            if not h:
                continue
            llm_obj = _read_cached_llm(cp, h)
            if llm_obj and isinstance(llm_obj, dict):
                if llm_obj.get("summary"):
                    nodes[fid].summary = str(llm_obj["summary"])

    # Build imports + calls edges
    edges: list[Edge] = []

    # Symbol index for call resolution
    symbol_to_files: dict[str, set[str]] = {}
    for fid, node in nodes.items():
        for sym in node.symbols:
            symbol_to_files.setdefault(sym, set()).add(fid)

    for fid in file_ids:
        h = nodes[fid].hash
        if not h:
            continue
        ast = _read_cached_ast(cp, h)
        if not ast:
            continue
        lang = ast.get("language")

        for imp in ast.get("imports", []):
            if not isinstance(imp, dict):
                continue
            target = _resolve_import(fid, str(imp.get("module", "")), all_file_set, lang)
            if not target:
                continue
            edges.append(
                Edge(
                    from_=fid,
                    to=target,
                    type="imports",
                    weight=1.0,
                    evidence=f"imports {target} at {fid}:{imp.get('line')}",
                    source="ast",
                )
            )

        for call in ast.get("calls", []):
            if not isinstance(call, dict):
                continue
            name = call.get("name")
            if not name:
                continue
            for target in sorted(symbol_to_files.get(str(name), set())):
                if target == fid:
                    continue
                edges.append(
                    Edge(
                        from_=fid,
                        to=target,
                        type="calls",
                        weight=1.0,
                        evidence=f"{name} called at {fid}:{call.get('line')}",
                        source="ast",
                    )
                )

        # Semantic edges from LLM cache
        if use_llm:
            llm_obj = _read_cached_llm(cp, h)
            if llm_obj and isinstance(llm_obj, dict):
                for se in llm_obj.get("semantic_edges", []) or []:
                    if not isinstance(se, dict):
                        continue
                    to = se.get("to")
                    etype = se.get("type") or "inferred"
                    w = float(se.get("weight") or 0.5)
                    evidence = str(se.get("evidence") or "")
                    if not to or to not in all_file_set:
                        continue
                    edges.append(
                        Edge(
                            from_=fid,
                            to=str(to),
                            type=str(etype),
                            weight=w,
                            evidence=evidence,
                            source="llm",
                        )
                    )

    # Git co-change edges (optional, cached only in final network)
    if use_git:
        try:
            co = cochange_edges(repo_path, file_ids=all_file_set)
            for e in co[:2000]:
                evidence = f"co-changed in {e.commits_together} commits (raw {e.raw_score:.3f})"
                # undirected → store both directions
                edges.append(
                    Edge(
                        from_=e.a,
                        to=e.b,
                        type="co-changes",
                        weight=e.raw_score,
                        evidence=evidence,
                        source="git",
                    )
                )
                edges.append(
                    Edge(
                        from_=e.b,
                        to=e.a,
                        type="co-changes",
                        weight=e.raw_score,
                        evidence=evidence,
                        source="git",
                    )
                )
        except Exception as e:
            print(f"Git analysis skipped: {e}")

    # Final edge weights per spec (Phase 6). Keep weak edges in network.json; visualizer filters by threshold.
    # Degree penalty: edges touching hub ("god") files are discounted to avoid weight clustering.
    deg_counts: dict[str, int] = {fid: 0 for fid in file_ids}
    out_deg_counts: dict[str, int] = {fid: 0 for fid in file_ids}
    for e in edges:
        if e.from_ in deg_counts:
            deg_counts[e.from_] += 1
            out_deg_counts[e.from_] += 1
        if e.to in deg_counts:
            deg_counts[e.to] += 1
    max_degree = max(deg_counts.values()) if deg_counts else 1
    max_out_degree = max(out_deg_counts.values()) if out_deg_counts else 1

    weighted_edges: list[Edge] = []
    for e in edges:
        raw = None
        if e.type == "co-changes":
            raw = e.weight
        w = final_weight(
            edge_type=e.type,
            source=e.source,
            from_degree=deg_counts.get(e.from_, 0),
            to_degree=deg_counts.get(e.to, 0),
            max_degree=max_degree,
            from_out_degree=out_deg_counts.get(e.from_, 0),
            max_out_degree=max_out_degree,
            raw=raw,
        )
        weighted_edges.append(
            Edge(
                from_=e.from_,
                to=e.to,
                type=e.type,
                weight=w,
                evidence=e.evidence,
                source=e.source,
            )
        )

    # Room classification (LLM or heuristic). Ensures every node has room_id.
    nodes_payload: list[dict[str, Any]] = []
    for fid in file_ids:
        n = nodes[fid]
        room_suggestion = None
        if use_llm and n.hash:
            llm_obj = _read_cached_llm(cp, n.hash)
            if llm_obj and isinstance(llm_obj, dict):
                room_suggestion = llm_obj.get("room_suggestion")
        nodes_payload.append(
            {
                "id": n.id,
                "language": n.language,
                "summary": n.summary,
                "symbols": list(n.symbols or []),
                "room_id": "other",
                "room_suggestion": room_suggestion,
            }
        )

    edges_payload = [we.to_json() for we in weighted_edges]
    file_to_room, classified_rooms = classify_rooms(
        repo_path=repo_path,
        nodes=nodes_payload,
        edges=edges_payload,
        model=model,
        use_llm=use_llm,
    )
    for fid, rid in file_to_room.items():
        if fid in nodes:
            nodes[fid].room_id = rid

    rooms: list[Room] = []
    for r in classified_rooms:
        rooms.append(
            Room(
                id=r.id,
                label=r.label,
                color=r.color,
                files=r.files,
                subtrees=r.subtrees,
                cross_room_refs=r.cross_room_refs or [],
                summary=r.summary,
                file=f"palace-out/rooms/{r.id}.md",
                token_count=None,
            )
        )

    # Serialize network (pre-room-files) so room writer has inputs
    network = build_network_json(repo_name=repo_path.name, nodes=nodes.values(), edges=weighted_edges, rooms=rooms)

    # Room writer + PALACE.md (Phase 5)
    updated_rooms, _palace_md = write_rooms_and_palace(repo_path=repo_path, model=model, use_llm=use_llm, network=network)
    network["rooms"] = updated_rooms

    # god_files + surprising_edges
    deg: dict[str, int] = {fid: 0 for fid in file_ids}
    for e in network.get("edges", []):
        if float(e.get("weight") or 0) >= 0.2:
            if e.get("from") in deg:
                deg[e["from"]] += 1
            if e.get("to") in deg:
                deg[e["to"]] += 1
    top = sorted(deg.items(), key=lambda kv: kv[1], reverse=True)[:5]
    network["god_files"] = [
        {"id": fid, "degree": d, "reason": "High connectivity in the dependency/association network."} for fid, d in top
    ]
    nodes_by_id = {n["id"]: n for n in network.get("nodes", []) if n.get("id")}
    surprising = []
    for e in network.get("edges", []):
        if float(e.get("weight") or 0) < 0.6:
            continue
        a = nodes_by_id.get(e.get("from"))
        b = nodes_by_id.get(e.get("to"))
        if not a or not b:
            continue
        if a.get("room_id") != b.get("room_id"):
            if e.get("type") in {"shares-schema", "co-changes", "inferred"}:
                surprising.append(
                    {
                        "from": e.get("from"),
                        "to": e.get("to"),
                        "type": e.get("type"),
                        "weight": e.get("weight"),
                        "reason": e.get("evidence") or "",
                    }
                )
    network["surprising_edges"] = surprising[:8]

    write_json(palace_out / "network.json", network)

    # update manifest last
    manifest["files"] = {fid: nodes[fid].hash for fid in file_ids if nodes[fid].hash}
    write_json(cp.manifest_path, manifest)
    # Visualizer output
    try:
        from palace.visualizer.builder import build_visualizer

        build_visualizer(repo_path)
    except Exception as e:
        print(f"Visualizer build skipped: {e}")

    # Token reduction ratio (definition-of-done metric)
    try:
        raw_tokens = sum(int(n.size_tokens or 0) for n in nodes.values())
        palace_tokens = 0
        palace_md_path = palace_out / "PALACE.md"
        if palace_md_path.exists():
            palace_tokens += approx_token_count(palace_md_path.read_text("utf-8"))
        rooms_dir = palace_out / "rooms"
        if rooms_dir.exists():
            for p in rooms_dir.glob("*.md"):
                palace_tokens += approx_token_count(p.read_text("utf-8"))
        if palace_tokens > 0:
            ratio = raw_tokens / palace_tokens
            if ratio >= 1.0:
                print(f"Token reduction ratio: {ratio:.1f}x (raw {raw_tokens} vs palace {palace_tokens})")
            else:
                print(
                    f"Palace size: {palace_tokens} tokens vs {raw_tokens} raw source tokens. "
                    "Try a larger repo for meaningful reduction (often 10–42× on medium codebases)."
                )
    except Exception:
        pass

