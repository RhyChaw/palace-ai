from __future__ import annotations

from datetime import datetime, timezone

from palace.memory.schemas import utc_now_iso


def apply_confidence_decay(patterns: list[dict], *, days_stale: int = 30, decay: float = 0.05) -> list[dict]:
    """Reduce confidence for patterns not updated recently (v2 polish)."""
    now = datetime.now(timezone.utc)
    out: list[dict] = []
    for p in patterns:
        updated = p.get("last_updated") or p.get("first_seen")
        if not updated:
            out.append(p)
            continue
        try:
            ts = updated.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_days = (now - dt).days
            if age_days >= days_stale:
                p = dict(p)
                p["confidence"] = max(0.1, float(p.get("confidence") or 0.5) - decay)
                p["last_updated"] = p.get("last_updated") or utc_now_iso()
        except ValueError:
            pass
        out.append(p)
    return out
