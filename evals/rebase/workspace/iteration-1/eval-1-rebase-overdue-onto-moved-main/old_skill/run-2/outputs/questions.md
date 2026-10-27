# Questions I would have asked (nobody was available; assumptions recorded)

Rebase of `feature/overdue` (curr `eebcce1`, old_base `a131d95`) onto `main` (new_base `d6f87f7`).

## Preflight (step 0)

**Q0.** The tree had an untracked `debug_notes.md` ("notes while debugging the due-time math;
delete before merge"). Is it related to the rebase, and do you want it kept?
**Assumption:** unrelated scratch notes; stashed under `swd-rebase-preflight-20261027-082920`
with `--include-untracked`, restored after the rebase, left untracked for you to delete.

## Risk gate (step 5)

**Q1. INV-006 vs commit `976e4b3` (service `overdue()`).** The commit reads `time.time()`
inside the service. `main` added INV-006: "A command that depends on the current time reads
it from the store's clock, never from the system clock directly." The original approach is
invalidated, not just stale. Options:
  a. Read `self.store.clock()` and drop the `now=None` parameter (strictly INV-006; no caller
     passes `now`; tests inject a clock into the store as `tests/test_tickets.py` already does).
  b. Keep `now=None` as an override but default to `self.store.clock()`.
  c. Keep the commit as authored and ask for an INV-006 exemption.
**Assumption / chosen:** (a). It is the only option that cannot be read as "time from the
caller" (architecture.md: "never from the caller"). (c) is off the table: AGENTS.md says
breaking an invariant needs explicit user confirmation, which I cannot get.

**Q2. CLI-001 still says "one of four subcommands" on `main`**, even though `main` added
`export` without touching CLI-001 or adding a CLI spec for it. Adding `overdue` makes it six.
Should CLI-001 be updated in the spec commit?
**Assumption:** no. Spec edits need your sign-off (docs/README.md, guidelines.md), the drift
pre-dates this branch, and the branch never touched CLI-001. Flagged in the report instead.

**Q3. Should TKT-014 cross-reference INV-006** ("the current time comes from the store clock")?
**Assumption:** no edit; TKT-014's "current time" wording is compatible with INV-006 as is,
and spec wording changes need your confirmation. Flagged in the report.

## Plan (step 8)

**Q4. Tests.** `main`'s new guideline (docs/guidelines.md "CLI tests") requires a subprocess
test per subcommand in `tests/test_cli.py`; the branch ships none for `overdue`. The older
"every module ships with tests" rule was already unmet by commit 1 (no service test). Add:
  - `tests/test_tickets.py::test_overdue_*` in commit 1 (it also proves the clock now comes
    from the store, which is the whole point of the INV-006 edit), and
  - `tests/test_cli.py::test_overdue_*` in commit 2.
Would you rather have the tests as a separate fourth commit?
**Assumption:** fold each test into the commit whose code it covers (skill step 9: edits that
preserve the original intent stay in the same commit), reference TKT-014 / CLI-010 / INV-006.

**Q5. Line format sharing.** Commit 2 duplicated the `list` format string; `main` extracted
`_line(t)`. Make `overdue` call `_line` (CLI-010: "in the `list` line format")?
**Assumption:** yes; it is what the spec says and avoids the format drifting in two places.

**Q6. Commit message amendments.** Commit 1 and 2 bodies get a sentence on the INV-006 /
`_line` adjustments and the spec IDs (guidelines.md "Reference spec IDs"). OK to reword?
**Assumption:** yes, bodies only; subjects kept.

## Plan summary

| Commit | Action |
|---|---|
| `976e4b3` feat(tickets): overdue detection | replay-with-edits: `self.store.clock()`, drop `now`, drop local `import time`, add service tests |
| `64bfd34` feat(cli): overdue subcommand | replay-with-edits: resolve conflicts with `export`/`_line`, use `_line(t)`, add CLI subprocess tests |
| `eebcce1` docs(specs): TKT-014, CLI-010 | replay as-is |

Backup of the pre-rebase branch: `backup/feature-overdue-pre-rebase` (= `eebcce1`). Nothing pushed.
