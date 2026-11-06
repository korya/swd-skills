# Review of plan.md (overdue tickets)

Verdict: the direction (derive overdue at read time, no new event) is sound, and it keeps INV-001/002/005 intact. But the code in step 2 would not work as written, and several claims are wrong. Findings are ordered by severity.

## Critical

### 1. `now()` reads an attribute that does not exist
- Plan step 2 (`plan.md:86-88`) calls `self.store._clock()` and cites `ticketdesk/store.py:16` as holding the private `_clock`.
- `ticketdesk/store.py:14-16` stores the clock as the public `self.clock`. There is no `_clock`.
- Result: every `list` and `overdue` call raises `AttributeError`. The plan's own convention table (`plan.md:187`) says `store.clock()`, so the plan contradicts itself.
- The claim at `plan.md:97` ("private attribute") is also wrong, and the supposed encapsulation concern behind it does not exist.
- Fix: use `self.store.clock()`.

### 2. `Ticket.is_overdue` ignores the closed state
- `plan.md:81-83` returns `now > self.due_at` only. Its docstring and TKT-014 (`plan.md:57-58`) say a closed ticket is never overdue.
- `overdue()` (`plan.md:93`) uses `is_overdue` as its only filter, so `ticketdesk overdue` would list closed tickets that closed late.
- The plan's own test (`plan.md:203`) would fail against the plan's own code.
- The A3 evidence claims "after close it is not" overdue. That cannot be true for this code, and `scratch/exp2_fake_clock.py` was not run against it (see finding 7).
- Fix: `return self.state != "closed" and now > self.due_at`.

### 3. CLI-010 says exit code 1 on empty, the test plan says 0
- `plan.md:71` specifies "prints nothing and exits with code 1" for no overdue tickets.
- `plan.md:213` expects exit 0 for `overdue` on a missing log, and the e2e at `plan.md:229` only works on success.
- Exit 1 conflicts with CLI-008 (`docs/product-specs/cli.md:54-56`), where success is 0 with nothing on stderr. It is also the traceback exit code that CLI-007 (`cli.md:50-52`) lists as the defect to fix.
- A "nothing overdue" result is not an error. Scripts could not tell it apart from a crash.
- Nothing in `cli.py` would produce 1 anyway, since `main()` returns 0 or 2 (`cli.py:33-34`).
- This is also a spec text that goes to the user for sign-off, so it must be consistent before then.

## High

### 4. The overdue rule is duplicated in the CLI, against architecture and the plan's own claim
- Step 3 (`plan.md:106`, `plan.md:110`) writes `t.state in ("open","assigned") and now > t.due_at` inside `_line` "so display does not depend on a service method".
- `docs/architecture.md:36-38` says the CLI holds no ticket rules, and `plan.md:186` claims compliance.
- The plan then has two implementations of TKT-014: `Ticket.is_overdue` (already buggy, finding 2) and the formatter. They can drift. `plan.md:110` cites the architecture lines as support when they say the opposite.
- Fix: `_line` calls `t.is_overdue(now)`. Boundary and closed behavior then have one owner and one test.

### 5. Wrong arithmetic in the tie-break test and in A6
- Test plan (`plan.md:205`): "Create a P2 ticket, move the clock 12 hours, then create a P1 ticket" to get equal due times. P2 is due at a+24h. P1 created at a+12h is due at a+16h (`ticketdesk/sla.py:3`, TKT-005). They are not equal. The P1 must be created 20h later.
- A6 (`plan.md:151`) says "P1 at a+12h equals P2 at a". That is false by the same arithmetic. "P1 created 10 hours ago and P2 created 22 hours ago are both due 6 hours ago" is also false: they are due 6h ago and 2h ago.
- As written, the TKT-015 tie test never exercises a tie, so it would pass without testing the tie-break. A6 ("Confirmed") is not reliable evidence.

### 6. Architecture doc edits are treated as needing no sign-off
- `plan.md:127` says step 6 edits "need no sign-off, because `AGENTS.md:93` limits the confirmation rule to product specs".
- `AGENTS.md:93` says: "Doc changes need user confirmation. Do not silently rewrite specs or architecture." `docs/README.md:36-39` repeats it for "a spec or an architecture doc".
- Step 6 edits `docs/architecture.md` at lines 12, 68-69 and 103, and the step also runs inside the commit the plan calls "signed-off" (`plan.md:139`).
- Fix: put the architecture and AGENTS.md edits in the step 1 gate and the sign-off list.

### 7. Cited experiments cannot be reproduced
- The plan relies on `scratch/exp1_prototype.py`, `scratch/exp2_fake_clock.py`, and `exp1` output (`plan.md:147-153`, `plan.md:237`). There is no `scratch/` directory in the repo, and `git status` shows only `plan.md` untracked.
- The sorted-output line at `plan.md:163` and the "all confirmed" results cannot be checked. Several have been shown wrong above (findings 2 and 5), so "Confirmed" is suspect throughout.
- The plan says the retroactive SLA risk was "shown" by experiment (`plan.md:237`), but I could not verify it.

## Medium

### 8. The `list` output change hides state, and the spec edits do not cover consequences
- `OVERDUE` replaces `open` or `assigned` in `list` (`plan.md:22`). An assigned ticket looks the same as an open one when overdue, and the CLI offers no other way to see the assignee (`get` has no command).
- The plan itself admits that this loses information (`plan.md:22`). It claims the choice keeps column count stable, but the title column is also a free-text field, so a script splitting on whitespace cannot tell states apart by count anyway.
- TKT-014 says "overdue is not a state", while CLI-006 (`cli.md:41-42`) names that column `<state>`. The CLI-006 edit needs wording that makes the column a display label, or it contradicts TKT-001 (`tickets.md:17-18`).
- Keeping the state and adding a separate marker, or appending `OVERDUE`, deserves a recommendation, not a default. The plan marks this as open question 1, but it is also the central decision, and it is the same as the headline's "blocking decision".

### 9. `list` and `overdue` are no longer pure functions of the log
- LOG-009 (`event-log.md:56-59`) and the plan's claim at `plan.md:19` hold only for replay. The output of `list` now varies with wall-clock time.
- The plan relies on that, and so do its tests. It should say so in the TKT-014 or CLI-006 text. It is a new kind of output for this repo, and CLI tests with a real clock (step 5) will rely on very old fixture dates, as the plan notes. A date-dependent flake is impossible only because the fixtures are in the past.

### 10. Product spec README is not in the edit list
- `docs/product-specs/README.md` has the feature index and prefix table (`README.md:60`), and TKT-014/15 and CLI-010 are new IDs. The plan's six spec edits do not check whether the index needs updating.
- The plan also says "six spec edits" in the headline (`plan.md:8`), but step 6 and `AGENTS.md:102-114` add further edits that are not counted.

### 11. CLI tests are broader than needed and are fragile
- Step 5 shells out with `cwd` at repo root (`plan.md:120`). Running from any other cwd, or against an installed package, behaves differently. An in-process `main(argv)` call with captured stdout would also work, because `main` takes `argv` (`cli.py:11`).
- The plan says `main()` needs no clock seam (`plan.md:122`), but CLI tests cannot then cover the boundary or a "fresh" open ticket without depending on real time. The "open ticket created by the test" case (`plan.md:211`) depends on the real clock being less than 72h from creation, which is fine in practice.

## Low

### 12. Plan text drift and small inconsistencies
- `plan.md:13-14` says `now()` and `overdue(now)` are added. Step 2 declares `overdue(self, now=None)`, so the signature differs.
- `plan.md:127` says "AGENTS.md:93", but the AGENTS.md lines it cites for the count change (`AGENTS.md:102`, `AGENTS.md:116`) need checking against the final test count. The count after the plan adds tests is not stated.
- `plan.md:233` asks for a manual check through the installed entry point, which needs `pip install`, and that step is not in the plan.
- Open question 9 asks for approval, while the plan says implementation must not start without it. That is consistent, but the assumption "yes, as drafted" should not be recorded as an answer.

## Recommended changes before implementation
1. Fix `_clock` → `clock`, add the closed check to `is_overdue`, and have `_line` call it (findings 1, 2, 4).
2. Decide empty-result exit code as 0 and fix the CLI-010 text (finding 3).
3. Correct the tie test to a 20h gap and re-derive A6 (finding 5).
4. Move architecture/AGENTS.md edits into the sign-off gate (finding 6).
5. Re-run and commit the experiments, or drop the "Confirmed" claims (finding 7).
