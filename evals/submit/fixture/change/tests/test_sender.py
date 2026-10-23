import unittest

from notify import DeliveryError, Sender
from tests.fakes import FakeClock, ScriptedClient


class SenderTests(unittest.TestCase):
    def test_returns_first_non_retryable(self):
        client = ScriptedClient([503, 200])
        clock = FakeClock()
        response = Sender(client, sleep=clock.sleep).send("hi")
        self.assertEqual(response.status, 200)
        self.assertEqual(client.calls, 2)

    def test_backoff_doubles(self):
        client = ScriptedClient([503])
        clock = FakeClock()
        with self.assertRaises(DeliveryError):
            Sender(client, retries=5, base=0.5, sleep=clock.sleep).send("hi")
        self.assertEqual(client.calls, 5)
        # 0.5 + 1 + 2 + 4 = 7.5 seconds across four waits
        self.assertAlmostEqual(clock.now, 1007.5)

    def test_retry_after_overrides_backoff(self):
        client = ScriptedClient([(429, {"Retry-After": "3"}), 200])
        clock = FakeClock()
        Sender(client, sleep=clock.sleep).send("hi")
        self.assertAlmostEqual(clock.now, 1003.0)

    def test_4xx_other_than_429_is_not_retried(self):
        client = ScriptedClient([400])
        clock = FakeClock()
        response = Sender(client, sleep=clock.sleep).send("hi")
        self.assertEqual(response.status, 400)
        self.assertEqual(client.calls, 1)
