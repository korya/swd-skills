#!/usr/bin/env bash
# Run one reviewer on one seeded plan and save its report.
# Usage: run.sh <brief-file> <plan-file> <out-dir>   (out-dir is wiped)
# Needs the `claude` CLI. The reviewer is a fresh headless session on Sonnet.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BRIEF="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
PLAN="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
OUT="${3:?usage: run.sh <brief-file> <plan-file> <out-dir>}"
REQUEST='tickets that pass their due time should show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` subcommand should list only overdue tickets, oldest due first.'

rm -rf "$OUT"; mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
bash "$HERE/../blueprint/make_fixture.sh" "$OUT/repo" >/dev/null
# The plans cite the fixture commit as @HEAD@. Each build of the fixture has its own hash.
sed "s/@HEAD@/$(git -C "$OUT/repo" rev-parse --short HEAD)/g" "$PLAN" > "$OUT/repo/plan.md"

PROMPT="$(python3 - "$BRIEF" "$OUT/repo/plan.md" "$OUT/repo" "$REQUEST" <<'PY'
import sys
brief, plan, repo, request = sys.argv[1:5]
text = open(brief).read()
text = text.replace("Document: <path>", "Document: " + plan)
text = text.replace("Repository: <path>", "Repository: " + repo)
text = text.replace("Request, in the user's words: <request>", "Request, in the user's words: " + request)
print(text)
PY
)"

cd "$OUT/repo"
claude -p --model sonnet --output-format json --settings '{"disableAllHooks":true}' \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --allowedTools Read Grep Glob Write --max-budget-usd 3 \
  -- "$PROMPT" > "$OUT/result.json"

# The control brief writes review.md. The others return the report as their reply.
python3 - "$OUT" <<'PY'
import json, pathlib, sys
out = pathlib.Path(sys.argv[1])
result = json.loads((out / "result.json").read_text())
review = out / "repo" / "review.md"
report = review.read_text() if review.exists() else (result.get("result") or "")
(out / "report.md").write_text(report)
print(f"{out.name}: ${result['total_cost_usd']:.2f}, {result['duration_ms'] / 1000:.0f} s, {len(report.split())} words")
PY
