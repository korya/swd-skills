from dataclasses import dataclass, field

from .sla import due_at

STATES = ("open", "assigned", "closed")


class TicketError(Exception):
    pass


@dataclass
class Ticket:
    id: int
    title: str
    priority: str
    created_at: float
    state: str = "open"
    assignee: str | None = None
    resolution: str | None = None
    due_at: float = field(default=0.0)


class TicketService:
    """Create, assign, and close tickets. Every change is one event in the store."""

    def __init__(self, store):
        self.store = store

    def _tickets(self):
        tickets = {}
        for ev in self.store.replay():
            kind = ev["kind"]
            if kind == "created":
                t = Ticket(ev["id"], ev["title"], ev["priority"], ev["at"])
                t.due_at = due_at(ev["at"], ev["priority"])
                tickets[t.id] = t
            elif kind == "assigned":
                tickets[ev["id"]].assignee = ev["assignee"]
                tickets[ev["id"]].state = "assigned"
            elif kind == "closed":
                tickets[ev["id"]].resolution = ev["resolution"]
                tickets[ev["id"]].state = "closed"
        return tickets

    def list(self):
        return sorted(self._tickets().values(), key=lambda t: t.id)

    def get(self, ticket_id):
        try:
            return self._tickets()[ticket_id]
        except KeyError:
            raise TicketError(f"no ticket {ticket_id}") from None

    def create(self, title, priority):
        if not title.strip():
            raise TicketError("title is required")
        due_at(0, priority)  # validates the priority
        next_id = max(self._tickets(), default=0) + 1
        ev = self.store.append({"kind": "created", "id": next_id, "title": title, "priority": priority})
        return self.get(ev["id"])

    def assign(self, ticket_id, assignee):
        t = self.get(ticket_id)
        if t.state == "closed":
            raise TicketError(f"ticket {ticket_id} is closed")
        if not assignee.strip():
            raise TicketError("assignee is required")
        self.store.append({"kind": "assigned", "id": ticket_id, "assignee": assignee})
        return self.get(ticket_id)

    def close(self, ticket_id, resolution):
        t = self.get(ticket_id)
        if t.state == "closed":
            raise TicketError(f"ticket {ticket_id} is already closed")
        if len(resolution.strip()) < 10:
            raise TicketError("resolution note must be at least 10 characters")
        self.store.append({"kind": "closed", "id": ticket_id, "resolution": resolution})
        return self.get(ticket_id)
