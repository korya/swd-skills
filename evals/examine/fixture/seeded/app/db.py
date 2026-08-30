"""Tiny in-memory store standing in for a database."""


class NotFound(KeyError):
    pass


class Store:
    def __init__(self):
        self.users = {}      # id -> dict
        self.discounts = {}  # code -> dict
        self.charges = []    # list of dicts

    def find_user_by_email(self, email: str):
        for u in self.users.values():
            if u["email"] == email:
                return u
        return None


STORE = Store()
