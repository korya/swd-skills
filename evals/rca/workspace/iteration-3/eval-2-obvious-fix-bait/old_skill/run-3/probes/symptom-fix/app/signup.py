"""Signup flow. Stores email as the user typed it."""

from app import db


class SignupError(Exception):
    pass


def signup(email: str, name: str) -> db.User:
    if not email or "@" not in email:
        raise SignupError("invalid email")
    if db.find_by_email(email) is not None:
        raise SignupError("email already registered")
    return db.insert(email=email, name=name)
