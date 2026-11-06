#!/usr/bin/env bash
# Run one author session that applies "Use the result" from assets/cold-read.md to a seeded spec.
# Usage: author.sh <first-read-report> <patch-file> <out-dir>   (out-dir is wiped)
# Saves the fixed draft as after.patch, the author's reply as author.md.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPORT="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
PATCH="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
OUT="${3:?usage: author.sh <first-read-report> <patch-file> <out-dir>}"
REQUEST='Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first.'

rm -rf "$OUT"; mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
bash "$HERE/../spec/make_fixture.sh" "$OUT/repo" >/dev/null
git -C "$OUT/repo" apply "$PATCH"

PROMPT="$(python3 - "$REPORT" "$OUT/repo" "$REQUEST" "$HERE/../../assets/cold-read.md" <<'PY'
import pathlib, sys
report, repo, request, rules_file = sys.argv[1:5]
rules = pathlib.Path(rules_file).read_text().split("## Use the result")[1].strip()
print(f"""You wrote the draft spec for overdue tickets in this repository: {repo}. The draft is
the uncommitted change under docs/ and in AGENTS.md, and `git diff` shows it.

The request, in the user's words: {request}

Before you present the spec, one reader with a fresh context and none of your reasoning
reviewed it. That was the cold read. The reader's report is below. Use the result as
these rules say. Step 1 is done. You cannot start a subagent in this run, so do not run
a second read yourself.

--- RULES ---
{rules}
--- END OF RULES ---

Nobody is available to answer questions. An ASK goes to the open questions of the spec.
Change only the spec files under docs/ and AGENTS.md. Do not commit.

End your reply with three things: the verdict for each finding in one table, the
cold-read note, and one last line that reads `SECOND READ: yes` or `SECOND READ: no`
with the rule that decides it.

--- THE READER'S REPORT ---
{pathlib.Path(report).read_text()}
""")
PY
)"

cd "$OUT/repo"
claude -p --model sonnet --output-format json --settings '{"disableAllHooks":true}' \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --allowedTools Read Grep Glob Edit Bash --max-budget-usd 4 \
  -- "$PROMPT" < /dev/null > "$OUT/result.json"
git -C "$OUT/repo" diff -- docs AGENTS.md > "$OUT/after.patch"

python3 - "$OUT" <<'PY'
import json, pathlib, sys
out = pathlib.Path(sys.argv[1]); r = json.loads((out / "result.json").read_text())
(out / "author.md").write_text(r.get("result") or "")
print(f"{out.name}: ${r['total_cost_usd']:.2f}, {r['duration_ms'] / 1000:.0f} s")
PY
