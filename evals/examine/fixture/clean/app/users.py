import itertools
import time

from . import audit
from .db import STORE
from .util import normalize_email

_ids = itertools.count(1)


def create_user(email: str, name: str) -> dict:
    email = normalize_email(email)
    user = {
        "id": next(_ids),
        "email": email,
        "name": name,
        "plan": "free",
        "created_at": time.time(),
    }
    STORE.users[user["id"]] = user
    audit.record("user.created", user_id=user["id"])
    return user
