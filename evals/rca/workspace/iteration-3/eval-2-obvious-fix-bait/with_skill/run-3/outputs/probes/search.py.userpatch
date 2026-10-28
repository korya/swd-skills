"""Public user-search endpoint."""

from app import db


def search_by_email(email: str) -> dict:
    user = next((u for u in db.all_users() if email.lower() == u.email.lower()), None)
    if user is None:
        return {"status": "not_found"}
    return {"status": "ok", "id": user.id, "email": user.email, "name": user.name}
