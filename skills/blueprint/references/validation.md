# Hypothesis and assumption validation

Loaded from `SKILL.md` step 2. Covers steps 2, 3 and 4 — the falsifiable hypothesis, the
load-bearing assumption list, and the cheapest validation for each assumption type.

## 2. Form a hypothesis

Propose a concrete candidate solution given current knowledge. It should be specific enough to be wrong:

- The components/files that change, at the directory level
- The data flow / control flow at a sketch level
- The key APIs, libraries, or system behaviors it relies on
- The 2-4 load-bearing assumptions ("this works *if* X behaves like Y")

If you cannot articulate a hypothesis at all, the problem is not yet understood — go back to step 1.

If multiple candidate approaches are plausible, note them and pick one to validate first based on simplicity, risk, or fit. The others are fallbacks if validation kills the primary.

**Then write down what would prove the hypothesis itself wrong** — not its individual assumptions (those come in step 3), but the *shape* of the solution. Examples:

- "If reads dominate writes by 100×, a read-through cache is the wrong shape — a write-aside would be."
- "If library X requires a long-lived TCP connection, treating it as a stateless RPC is the wrong shape."
- "If the failure happens before request routing, anything I add in the handler is the wrong shape."

A hypothesis you can't even imagine disproving isn't a hypothesis — it's a vibe with file paths. If you can't write the falsifier, the hypothesis isn't specific enough; sharpen it. Carry the falsifier into step 4 and test it alongside the assumptions.

## 3. Enumerate load-bearing assumptions

Write them down explicitly. An assumption is load-bearing if the plan **stops working** when the assumption is false. Examples:

- "Library X exposes method Y that returns Z"
- "The `customers` table has column `phone_e164` and it is unique per org"
- "This endpoint is reachable from the agent server without new auth"
- "The hatchet runner can hold this much state per task"

For each assumption, classify:

- **Verified** — already known true from reading current code/docs
- **Plausible** — best-guess; needs cheap validation
- **Risky** — the change pivots on this and a wrong answer kills the plan

Risky and plausible assumptions go into step 4. Verified ones get a citation (file:line or doc reference) and move on.

## 4. Validate assumptions

For each unverified assumption, pick the cheapest validation that produces real evidence:

| Assumption type | Validation |
|---|---|
| API behavior | Write a 10-30 line script, run it, capture the output. Or read the library source. |
| Library capability | Read the library docs *and* the code; docs lie, code does not |
| Internal code behavior | `grep` / `Read` the actual implementation on `HEAD`; do not trust memory |
| Schema / data shape | Query the dev DB (read-only) or read the migration files |
| System / infra behavior | Read the relevant config, IaC, or runtime docs; if cheap, run a probe |
| Performance / scale | Back-of-envelope first; only benchmark if the math is too close to call |
| External service | Read the vendor docs *and* check if there's already an integration in-repo to crib from |

Record each result as **confirmed**, **refuted**, or **partial**. For refuted assumptions, return to step 2 with new information — do not patch around the refutation.

For batched investigation (multiple parallel reads, broad searches), delegate to a read-only search subagent if your host provides one, rather than draining the main context.
