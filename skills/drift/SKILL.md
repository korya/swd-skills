---
name: drift
description: Find where a product and its specs disagree — run every acceptance criterion in the spec set against the product through its real surface, inventory the product for behaviour no criterion covers, and report both directions per spec ID with the run that shows each one, without fixing anything. Use when the user says "/drift", "drift check", "spec drift report", "do the specs still match the product", or asks whether the product still does what its specs say.
---

# Drift: where the specs and the product disagree

The point is not to test a change. The point is to find out whether the product still does
what its specs say, and whether it does things no spec says. `/e2e-test` tests a change
through the front door. `/drift` tests the whole spec set the same way, then reads the
product's surface back against the specs. The deliverable is a report. Which side changes,
the spec or the product, is the user's decision.

Never edit specs, code, config, or tests. Propose no fix. A drift is a fact about the
product and its contract, and this skill records the fact.

## Required references

Paths are relative to this file. `<plugin root>` is two directories above it. Read each
file at the step named.

| File | Read at | Holds |
|---|---|---|
| `../e2e-test/references/surfaces.md` | step 2 | the surface and persona per product type, the fail-fast rule |
| `../e2e-test/references/cases.md` | step 3 | how a criterion becomes cases |
| `references/verdicts.md` | step 3 | MATCH, DRIFT, BLOCKED, OPEN, and the evidence each needs |
| `references/inventory.md` | step 5 | what counts as a behaviour, and UNCOVERED |
| `references/report.md` | step 6 | the report shape |
| `../../assets/writing.md` | step 6, before writing the report | the writing rules for every text a person reads |
| `references/rationalizations.md` | when tempted to decide, skip, or read instead of run | why each shortcut fails |

## Running as a subagent

Another skill may run this one in a subagent. The work is running commands and comparing
output, so the subagent may be a smaller, faster model than the one that wrote the specs.

## Side effects

Driving the product's own surface is testing, not fixing. Creating, updating, and
deleting records through it is fine in a dev or local environment. Any other environment
needs the user's explicit confirmation before the first mutation. Without it, the cases
that mutate are BLOCKED. Work in a scratch directory outside the repo, and keep what you
create. The report lists it.

## Workflow

1. **Scope.** Read the conventions doc, `AGENTS.md` or its equivalent, and the docs index.
   Find the spec set and how the product is run. The default scope is every feature
   criterion, each `PREFIX-NNN` heading. Invariants are checked only where a feature
   criterion makes them observable. A prefix or a file in the request narrows the scope.
   State the scope and the count of criteria before anything runs.
2. **Surface and persona.** Read `../e2e-test/references/surfaces.md` now. Name the
   product's real user, their surface, and the target environment. Stay on that surface.
3. **Case list.** Read `../e2e-test/references/cases.md` and `references/verdicts.md` now.
   For each criterion, write one or more cases from its text alone, each with the outcome
   the text promises. A criterion whose text carries an open TODO is OPEN. Its settled part
   may still get cases. The list is the contract for the run.
4. **Readiness and execution.** Start the product the documented way and smoke-check the
   surface. If it will not come up, stop and report. Run every case from scratch, through
   the surface only. Keep an evidence log tagged by criterion ID, with every command and
   what the surface showed. A verdict comes from what the user would see. A DRIFT does not
   stop the run.
5. **Inventory.** Read `references/inventory.md` now. Enumerate what the product does, from
   its help output and from the runs: commands, options, output lines, files it writes,
   exit codes, error paths. For each behaviour, name the criterion that covers it or
   report it as UNCOVERED, with the run that shows it.
6. **Report.** Read `../../assets/writing.md` and `references/report.md` now. Write the
   report, run `<plugin root>/scripts/prose-lint.py` on it, and fix every finding. Deliver
   it and stop.

## Definition of done

- [ ] Scope stated with the criterion count. Surface, persona, and environment stated.
- [ ] Case list written before execution, every criterion present.
- [ ] Every criterion carries exactly one of MATCH, DRIFT, BLOCKED, or OPEN.
- [ ] Every verdict earned at the surface. No MATCH by reading code.
- [ ] Every DRIFT and UNCOVERED item carries the exact command, the exact output, and the
  spec text. Every BLOCKED names the observation that would settle it.
- [ ] The inventory ran, and every behaviour maps to a criterion or an UNCOVERED item.
- [ ] Zero repo files modified. No fix proposed. Artifacts listed.
- [ ] The report passes `prose-lint.py` with no findings.

## Related skills

`/e2e-test` tests a change, not the whole contract. `/spec` amends the criterion when the
user decides the spec was wrong. `/rca` finds the cause when the user decides the product
was wrong.
