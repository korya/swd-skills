import unittest

from notify import DeliveryError, Sender
from tests.fakes import FakeClock, ScriptedClient


class SenderTests(unittest.TestCase):
    def test_returns_first_non_5xx(self):
        client = ScriptedClient([503, 200])
        clock = FakeClock()
        response = Sender(client, sleep=clock.sleep).send("hi")
        self.assertEqual(response.status, 200)
        self.assertEqual(client.calls, 2)

    def test_raises_after_retries(self):
        client = ScriptedClient([503])
        clock = FakeClock()
        with self.assertRaises(DeliveryError):
            Sender(client, retries=3, sleep=clock.sleep).send("hi")
        self.assertEqual(client.calls, 3)
        self.assertEqual(clock.now, 1003.0)
