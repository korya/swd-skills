"""Service-level targets by priority. Hours until a ticket is due."""

SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}


def due_at(created_at, priority):
    if priority not in SLA_HOURS:
        raise ValueError(f"unknown priority {priority!r}; expected one of {sorted(SLA_HOURS)}")
    return created_at + SLA_HOURS[priority] * 3600
