import json
import time
from pathlib import Path


class EventStore:
    """Append-only JSON lines log. Events are never edited or deleted.

    The current state of every ticket is rebuilt by replaying the log, so the log is the
    single source of truth. A corrupt line stops the replay with an error rather than
    being skipped.
    """

    def __init__(self, path, clock=time.time):
        self.path = Path(path)
        self.clock = clock

    def append(self, event):
        record = dict(event)
        record["at"] = self.clock()
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
        return record

    def replay(self):
        if not self.path.exists():
            return []
        events = []
        for lineno, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{self.path}:{lineno}: corrupt event: {exc}") from exc
        return events
