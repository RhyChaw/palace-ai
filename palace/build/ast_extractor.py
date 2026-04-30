from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from tree_sitter import Language, Node as TSNode, Parser
import tree_sitter_javascript
import tree_sitter_python
import tree_sitter_typescript


@dataclass(frozen=True)
class ImportRef:
    module: str
    line: int


@dataclass(frozen=True)
class SymbolDef:
    name: str
    signature: str | None
    line: int
    kind: str  # function|class|const


@dataclass(frozen=True)
class CallSite:
    name: str
    line: int


@dataclass
class AstExtraction:
    imports: list[ImportRef]
    exports: list[SymbolDef]
    calls: list[CallSite]
    implements: list[str]

    def to_json(self) -> dict[str, Any]:
        return {
            "imports": [i.__dict__ for i in self.imports],
            "exports": [e.__dict__ for e in self.exports],
            "calls": [c.__dict__ for c in self.calls],
            "implements": list(self.implements),
        }


def _line(node: TSNode) -> int:
    return int(node.start_point[0]) + 1


def _text(src: bytes, node: TSNode) -> str:
    return src[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _walk(node: TSNode) -> Iterable[TSNode]:
    yield node
    for ch in node.children:
        yield from _walk(ch)


def _python_extractor(src: bytes, root: TSNode) -> AstExtraction:
    imports: list[ImportRef] = []
    exports: list[SymbolDef] = []
    calls: list[CallSite] = []
    implements: list[str] = []

    for n in _walk(root):
        if n.type in {"import_statement", "import_from_statement"}:
            txt = _text(src, n)
            m = re.search(r"(?:from\s+([A-Za-z0-9_\.]+)\s+import|import\s+([A-Za-z0-9_\.]+))", txt)
            mod = (m.group(1) or m.group(2)) if m else txt.strip()
            imports.append(ImportRef(module=mod, line=_line(n)))

        if n.type == "function_definition":
            name_node = n.child_by_field_name("name")
            params_node = n.child_by_field_name("parameters")
            name = _text(src, name_node) if name_node else "unknown"
            params = _text(src, params_node) if params_node else "()"
            exports.append(SymbolDef(name=name, signature=f"{name}{params}", line=_line(n), kind="function"))

        if n.type == "class_definition":
            name_node = n.child_by_field_name("name")
            name = _text(src, name_node) if name_node else "unknown"
            exports.append(SymbolDef(name=name, signature=name, line=_line(n), kind="class"))
            supers = n.child_by_field_name("superclasses")
            if supers:
                implements.append(_text(src, supers).strip())

        if n.type == "call":
            fn = n.child_by_field_name("function")
            if fn is None:
                continue
            # identifier | attribute
            if fn.type == "identifier":
                calls.append(CallSite(name=_text(src, fn), line=_line(n)))
            elif fn.type == "attribute":
                attr = fn.child_by_field_name("attribute")
                if attr:
                    calls.append(CallSite(name=_text(src, attr), line=_line(n)))

    return AstExtraction(imports=imports, exports=exports, calls=calls, implements=implements)


def _js_like_extractor(src: bytes, root: TSNode) -> AstExtraction:
    imports: list[ImportRef] = []
    exports: list[SymbolDef] = []
    calls: list[CallSite] = []
    implements: list[str] = []

    for n in _walk(root):
        if n.type in {"import_statement"}:
            source = n.child_by_field_name("source")
            if source:
                imports.append(ImportRef(module=_text(src, source).strip("\"'"), line=_line(n)))

        if n.type in {"call_expression", "new_expression"}:
            fn = n.child_by_field_name("function")
            if fn is None:
                fn = n.child_by_field_name("constructor")
            if fn is None:
                continue
            if fn.type == "identifier":
                calls.append(CallSite(name=_text(src, fn), line=_line(n)))
            elif fn.type == "member_expression":
                prop = fn.child_by_field_name("property")
                if prop:
                    calls.append(CallSite(name=_text(src, prop), line=_line(n)))

        if n.type == "function_declaration":
            name_node = n.child_by_field_name("name")
            params_node = n.child_by_field_name("parameters")
            if name_node:
                name = _text(src, name_node)
                params = _text(src, params_node) if params_node else "()"
                exports.append(SymbolDef(name=name, signature=f"{name}{params}", line=_line(n), kind="function"))

        if n.type == "class_declaration":
            name_node = n.child_by_field_name("name")
            if name_node:
                name = _text(src, name_node)
                exports.append(SymbolDef(name=name, signature=name, line=_line(n), kind="class"))
            sup = n.child_by_field_name("superclass")
            if sup:
                implements.append(_text(src, sup).strip())

        if n.type == "lexical_declaration":
            # const foo = ...
            for decl in n.children:
                if decl.type == "variable_declarator":
                    name_node = decl.child_by_field_name("name")
                    if name_node and name_node.type == "identifier":
                        exports.append(
                            SymbolDef(
                                name=_text(src, name_node),
                                signature=_text(src, name_node),
                                line=_line(decl),
                                kind="const",
                            )
                        )

    return AstExtraction(imports=imports, exports=exports, calls=calls, implements=implements)


def extract_ast(language: str, content: str) -> AstExtraction:
    src = content.encode("utf-8", errors="replace")
    if language == "python":
        ts_lang = Language(tree_sitter_python.language())
    elif language == "javascript":
        ts_lang = Language(tree_sitter_javascript.language())
    elif language == "typescript":
        # treat TSX as TS for now; we parse TypeScript grammar
        ts_lang = Language(tree_sitter_typescript.language_typescript())
    else:
        raise ValueError(f"Unsupported language: {language}")
    parser = Parser()
    # tree-sitter Python bindings changed API (0.25+)
    try:
        parser.set_language(ts_lang)  # type: ignore[attr-defined]
    except AttributeError:
        parser.language = ts_lang
    tree = parser.parse(src)
    root = tree.root_node
    if language == "python":
        return _python_extractor(src, root)
    if language in {"javascript", "typescript"}:
        return _js_like_extractor(src, root)
    raise ValueError(f"Unsupported language: {language}")

