import time


class DeliveryError(Exception):
    def __init__(self, response):
        super().__init__(f"delivery failed with status {response.status}")
        self.response = response


class Sender:
    """Post messages to the gateway, retrying a fixed number of times on 5xx."""

    def __init__(self, client, retries=3, delay=1.0, sleep=time.sleep):
        self.client = client
        self.retries = retries
        self.delay = delay
        self.sleep = sleep

    def send(self, message):
        last = None
        for _ in range(self.retries):
            response = self.client.post(message)
            if response.status < 500:
                return response
            last = response
            self.sleep(self.delay)
        raise DeliveryError(last)
