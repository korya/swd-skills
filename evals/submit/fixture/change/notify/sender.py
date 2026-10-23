import random
import time

RETRYABLE = {429, 500, 502, 503, 504}


class DeliveryError(Exception):
    def __init__(self, response):
        super().__init__(f"delivery failed with status {response.status}")
        self.response = response


class Sender:
    """Post messages to the gateway with exponential backoff.

    Each retry waits base * 2**attempt seconds plus up to `jitter` seconds, capped at
    `max_delay`. A Retry-After header on 429 or 503 overrides the computed delay.
    """

    def __init__(self, client, retries=5, base=0.5, max_delay=16.0, jitter=0.0,
                 sleep=time.sleep, rand=random.random):
        self.client = client
        self.retries = retries
        self.base = base
        self.max_delay = max_delay
        self.jitter = jitter
        self.sleep = sleep
        self.rand = rand

    def send(self, message):
        last = None
        for attempt in range(self.retries):
            response = self.client.post(message)
            if response.status not in RETRYABLE:
                return response
            last = response
            if attempt == self.retries - 1:
                break
            self.sleep(self._delay(attempt, response))
        raise DeliveryError(last)

    def _delay(self, attempt, response):
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            return float(retry_after)
        delay = min(self.base * (2 ** attempt), self.max_delay)
        return delay + self.rand() * self.jitter
