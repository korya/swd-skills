"""In-memory user store. Case-sensitive lookups by email."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: int
    email: str
    name: str


_USERS: list[User] = []
_NEXT_ID = 1


def reset() -> None:
    global _USERS, _NEXT_ID
    _USERS = []
    _NEXT_ID = 1


def insert(email: str, name: str) -> User:
    global _NEXT_ID
    user = User(id=_NEXT_ID, email=email, name=name)
    _NEXT_ID += 1
    _USERS.append(user)
    return user


def find_by_email(email: str) -> Optional[User]:
    for u in _USERS:
        if u.email == email:
            return u
    return None


def all_users() -> list[User]:
    return list(_USERS)
