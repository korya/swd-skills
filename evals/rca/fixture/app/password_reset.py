"""Password-reset flow — also looks up by email."""

from app import db


class ResetError(Exception):
    pass


def request_reset(email: str) -> str:
    user = db.find_by_email(email)
    if user is None:
        raise ResetError("no such user")
    return f"reset-token-for-{user.id}"
