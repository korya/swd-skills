"""Team-invite flow — checks whether an invitee already has an account."""

from app import db


def is_already_member(email: str) -> bool:
    return db.find_by_email(email) is not None


def send_invite(email: str) -> dict:
    if is_already_member(email):
        return {"status": "already_member"}
    return {"status": "invite_sent", "to": email}
