# Hypothesis and assumption validation

Loaded from `SKILL.md` step 2. Covers steps 2, 3 and 4: the falsifiable hypothesis, the
load-bearing assumption list, and the cheapest validation for each assumption type.

## 2. Form a hypothesis

Propose a concrete candidate solution given current knowledge. It should be specific enough
to be wrong:

- the components and files that change, at the directory level
- the data flow and control flow, at a sketch level
- the key APIs, libraries, or system behaviors it relies on
- the two to four load-bearing assumptions ("this works if X behaves like Y")

If you cannot articulate a hypothesis at all, the problem is not yet understood. Go back to
step 1.

If several candidate approaches are plausible, note them and pick one to validate first.
Choose on simplicity, risk, or fit. The others are fallbacks if validation kills the primary.

**Then write down what would prove the hypothesis itself wrong.** Not its individual
assumptions, which come in step 3, but the shape of the solution. Examples:

- "If reads dominate writes by 100 to 1, a read-through cache is the wrong shape. A
  write-aside would be right."
- "If library X requires a long-lived TCP connection, treating it as a stateless RPC is the
  wrong shape."
- "If the failure happens before request routing, anything I add in the handler is the
  wrong shape."

A hypothesis you cannot imagine disproving is not a hypothesis. It is a vibe with file
paths. If you cannot write the falsifier, the hypothesis is not specific enough. Sharpen it.
Carry the falsifier into step 4 and test it alongside the assumptions.

## 3. Enumerate load-bearing assumptions

Write them down explicitly. An assumption is load-bearing if the plan stops working when
the assumption is false. Examples:

- "Library X exposes method Y that returns Z."
- "The `customers` table has column `phone_e164` and it is unique per org."
- "This endpoint is reachable from the agent server without new auth."
- "The background-job runner can hold this much state per task."

For each assumption, classify:

- **Verified.** Already known true from reading current code or docs.
- **Plausible.** A best guess that needs cheap validation.
- **Risky.** The change pivots on this, and a wrong answer kills the plan.

Risky and plausible assumptions go into step 4. Verified ones get a citation (`file:line` or
a doc reference) and move on.

## 4. Validate assumptions

For each unverified assumption, pick the cheapest validation that produces real evidence:

| Assumption type | Validation |
|---|---|
| API behavior | Write a 10 to 30 line script, run it, capture the output. Or read the library source. |
| Library capability | Read the library docs and the code. Docs lie, code does not. |
| Internal code behavior | Grep or read the actual implementation on `HEAD`. Do not trust memory. |
| Schema or data shape | Query the dev DB read-only, or read the migration files. |
| System or infra behavior | Read the relevant config, IaC, or runtime docs. If cheap, run a probe. |
| Performance or scale | Back-of-envelope first. Benchmark only if the math is too close to call. |
| External service | Read the vendor docs, and check whether an integration already exists in the repo to crib from. |

Record each result as **confirmed**, **refuted**, or **partial**. For a refuted assumption,
return to step 2 with the new information. Do not patch around the refutation.

Delegate batched investigation to a read-only search subagent if your host provides one.
Many parallel reads or broad searches drain the main context otherwise.
