from .db import STORE


def record(event: str, **fields) -> dict:
    """Append an audit entry. Callers pass ids, never raw emails."""
    entry = {"event": event, **fields}
    STORE.audit.append(entry)
    return entry
