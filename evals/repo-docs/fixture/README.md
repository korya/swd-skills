# ticketdesk

A command-line help desk for a small support team. Agents create tickets, assign them,
and close them with a resolution note. Every change is appended to an event log in a JSON
file, so the history of a ticket is never lost.

Run `make test` before you push and `make lint` for a syntax pass. CI runs both.
