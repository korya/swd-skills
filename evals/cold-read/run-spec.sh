#!/usr/bin/env bash
# Run one reviewer on one seeded spec and save its report.
# Usage: run-spec.sh <brief-file> <patch-file> <out-dir>   (out-dir is wiped)
# The patch is a `git diff` of the spec draft against the fixture, see specs/.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BRIEF="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
PATCH="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
OUT="${3:?usage: run-spec.sh <brief-file> <patch-file> <out-dir>}"
REQUEST='Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first.'

rm -rf "$OUT"; mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
bash "$HERE/../spec/make_fixture.sh" "$OUT/repo" >/dev/null
git -C "$OUT/repo" apply "$PATCH"

PROMPT="$(python3 - "$BRIEF" "$OUT/repo" "$REQUEST" <<'PY'
import sys
brief, repo, request = sys.argv[1:4]
doc = (f'{repo}/docs/product-specs/tickets.md (the section "Overdue tickets") and '
       f'{repo}/docs/product-specs/cli.md (the status note, CLI-001, CLI-006, and CLI-010 to CLI-012). '
       'The spec is a draft and is not committed. `git diff` shows every change.')
text = open(brief).read()
for old, new in (("Document: <path>", "Document: " + doc), ("Repository: <path>", "Repository: " + repo),
                 ("Request, in the user's words: <request>", "Request, in the user's words: " + request)):
    assert old in text, old
    text = text.replace(old, new)
print(text)
PY
)"

cd "$OUT/repo"
# The reader may run the product, so it gets Bash. The repo is a throwaway copy.
claude -p --model sonnet --output-format json --settings '{"disableAllHooks":true}' \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --allowedTools Read Grep Glob Bash --max-budget-usd 3 \
  -- "$PROMPT" < /dev/null > "$OUT/result.json"

python3 - "$OUT" <<'PY'
import json, pathlib, sys
out = pathlib.Path(sys.argv[1])
r = json.loads((out / "result.json").read_text())
report = r.get("result") or ""
(out / "report.md").write_text(report)
print(f"{out.name}: ${r['total_cost_usd']:.2f}, {r['duration_ms'] / 1000:.0f} s, {len(report.split())} words")
PY
