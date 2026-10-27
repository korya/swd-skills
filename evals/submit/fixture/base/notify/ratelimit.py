import time


class FixedWindowLimiter:
    """Allow at most `limit` sends per tenant in each `window` seconds."""

    def __init__(self, limit=100, window=60.0, clock=time.monotonic):
        self.limit = limit
        self.window = window
        self.clock = clock
        self._counts = {}

    def allow(self, tenant):
        now = self.clock()
        start, count = self._counts.get(tenant, (now, 0))
        if now - start >= self.window:
            start, count = now, 0
        if count >= self.limit:
            self._counts[tenant] = (start, count)
            return False
        self._counts[tenant] = (start, count + 1)
        return True
