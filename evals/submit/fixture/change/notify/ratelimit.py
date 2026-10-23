import time


class TokenBucketLimiter:
    """Allow a sustained `rate` of sends per second per tenant, with a `burst` of extra.

    Replaces the fixed window, which let a tenant send its whole minute's quota in one
    second and then nothing. The default sustained rate is 60 per minute with a burst
    of 20.
    """

    def __init__(self, rate=1.0, burst=20, clock=time.monotonic):
        self.rate = rate
        self.burst = burst
        self.clock = clock
        self._buckets = {}

    def allow(self, tenant):
        now = self.clock()
        tokens, last = self._buckets.get(tenant, (float(self.burst), now))
        tokens = min(float(self.burst), tokens + (now - last) * self.rate)
        if tokens < 1.0:
            self._buckets[tenant] = (tokens, now)
            return False
        self._buckets[tenant] = (tokens - 1.0, now)
        return True
