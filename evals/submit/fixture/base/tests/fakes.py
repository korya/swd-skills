class Response:
    def __init__(self, status, headers=None):
        self.status = status
        self.headers = headers or {}


class ScriptedClient:
    """Returns the scripted responses in order, then repeats the last one."""

    def __init__(self, statuses):
        self.statuses = list(statuses)
        self.calls = 0

    def post(self, message):
        self.calls += 1
        index = min(self.calls - 1, len(self.statuses) - 1)
        status = self.statuses[index]
        if isinstance(status, tuple):
            return Response(status[0], status[1])
        return Response(status)


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds
