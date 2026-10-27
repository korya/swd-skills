#!/usr/bin/env bash
# The spec eval reuses the blueprint fixture: ticketdesk with agent docs, one commit on main.
# Usage: make_fixture.sh <target-dir>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
exec bash "$HERE/../blueprint/make_fixture.sh" "$@"
