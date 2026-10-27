import unittest

from notify import TokenBucketLimiter
from tests.fakes import FakeClock


class TokenBucketTests(unittest.TestCase):
    def test_burst_then_block(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=1.0, burst=3, clock=clock)
        self.assertEqual([limiter.allow("t1") for _ in range(4)], [True, True, True, False])

    def test_refills_at_rate(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=1.0, burst=1, clock=clock)
        self.assertTrue(limiter.allow("t1"))
        self.assertFalse(limiter.allow("t1"))
        clock.now += 1.0
        self.assertTrue(limiter.allow("t1"))

    def test_tenants_are_independent(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=1.0, burst=1, clock=clock)
        self.assertTrue(limiter.allow("t1"))
        self.assertTrue(limiter.allow("t2"))
