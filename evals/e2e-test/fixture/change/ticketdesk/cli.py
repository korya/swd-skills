import argparse
import os
import sys

from .store import EventStore
from .tickets import TicketError, TicketService

DEFAULT_LOG = os.environ.get("TICKETDESK_LOG", "tickets.jsonl")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ticketdesk", description="Manage support tikets from the shell.")
    parser.add_argument("--log", default=DEFAULT_LOG, help="path of the event log")
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create"); c.add_argument("title"); c.add_argument("--priority", default="P3")
    a = sub.add_parser("assign"); a.add_argument("id", type=int); a.add_argument("assignee")
    x = sub.add_parser("close"); x.add_argument("id", type=int); x.add_argument("resolution")
    sub.add_parser("list")
    args = parser.parse_args(argv)
    svc = TicketService(EventStore(args.log))
    try:
        if args.cmd == "create":
            t = svc.create(args.title, args.priority); print(f"#{t.id} {t.state} {t.title}")
        elif args.cmd == "assign":
            t = svc.assign(args.id, args.assignee); print(f"#{t.id} {t.state} -> {t.assignee}")
        elif args.cmd == "close":
            t = svc.close(args.id, args.resolution); print(f"#{t.id} {t.state}")
        else:
            for t in svc.list():
                print(f"#{t.id} {t.state:<8} {t.title}")
    except TicketError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
