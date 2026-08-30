"""Tiny in-memory store standing in for a database."""


class NotFound(KeyError):
    pass


class Store:
    def __init__(self):
        self.users = {}      # id -> dict
        self.discounts = {}  # code -> dict
        self.charges = []    # list of dicts
        self.audit = []      # append-only audit trail

    def find_user_by_email(self, email: str) -> dict:
        for u in self.users.values():
            if u["email"] == email:
                return u
        raise NotFound(email)


STORE = Store()
