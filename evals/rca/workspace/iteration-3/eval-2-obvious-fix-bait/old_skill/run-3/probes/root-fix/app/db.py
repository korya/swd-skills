"""In-memory user store. Email lookups and uniqueness are case-insensitive."""

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


def normalize_email(email: str) -> str:
    """The one place that defines email identity."""
    return email.casefold()


class DuplicateEmail(Exception):
    pass


def insert(email: str, name: str) -> User:
    global _NEXT_ID
    if find_by_email(email) is not None:
        raise DuplicateEmail(email)
    user = User(id=_NEXT_ID, email=email, name=name)
    _NEXT_ID += 1
    _USERS.append(user)
    return user


def find_by_email(email: str) -> Optional[User]:
    key = normalize_email(email)
    for u in _USERS:
        if normalize_email(u.email) == key:
            return u
    return None


def all_users() -> list[User]:
    return list(_USERS)
