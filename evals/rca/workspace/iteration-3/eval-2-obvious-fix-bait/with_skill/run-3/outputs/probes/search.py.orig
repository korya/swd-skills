"""Public user-search endpoint."""

from app import db


def search_by_email(email: str) -> dict:
    user = db.find_by_email(email)
    if user is None:
        return {"status": "not_found"}
    return {"status": "ok", "id": user.id, "email": user.email, "name": user.name}
