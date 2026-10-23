import unittest

from notify import FixedWindowLimiter
from tests.fakes import FakeClock


class FixedWindowTests(unittest.TestCase):
    def test_blocks_after_limit(self):
        clock = FakeClock()
        limiter = FixedWindowLimiter(limit=2, window=60, clock=clock)
        self.assertTrue(limiter.allow("t1"))
        self.assertTrue(limiter.allow("t1"))
        self.assertFalse(limiter.allow("t1"))

    def test_resets_after_window(self):
        clock = FakeClock()
        limiter = FixedWindowLimiter(limit=1, window=60, clock=clock)
        self.assertTrue(limiter.allow("t1"))
        clock.now += 61
        self.assertTrue(limiter.allow("t1"))
