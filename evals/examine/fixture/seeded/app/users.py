import itertools
import time

from .db import STORE

_ids = itertools.count(1)


def create_user(email: str, name: str, source: str = "web") -> dict:
    user = {
        "id": next(_ids),
        "email": email.strip(),
        "name": name,
        "plan": "free",
        "source": source,
        "created_at": time.time(),
    }
    STORE.users[user["id"]] = user
    return user
