# Hypothesis and assumption validation

Loaded from `SKILL.md` step 2. Covers steps 2 to 4.

## 2. Form a hypothesis

Write a candidate solution specific enough to be wrong. Name the files and flows that
change, the APIs and system behaviors it relies on, and its two to four load-bearing
assumptions. If several approaches are plausible, pick one on simplicity, risk, or fit, and
keep the others as fallbacks. If you cannot write a hypothesis at all, go back to step 1.

**Then write the falsifier: the observation that would prove the shape wrong.** It is
about the whole solution, not one assumption. For example: "If reads dominate writes by 100
to 1, a read-through cache is the wrong shape." A hypothesis you cannot imagine disproving
is not specific enough. Sharpen it, and test the falsifier in step 4 alongside the
assumptions.

## 3. List the load-bearing assumptions

An assumption is load-bearing if the plan stops working when it is false. An example is
"the `customers` table has a `phone_e164` column, unique per org". Classify each one:

- **Verified.** Known true from the current code or docs. Cite `file:line` and move on.
- **Plausible.** A best guess that needs a cheap check.
- **Risky.** The plan pivots on it, and a wrong answer kills the plan.

## 4. Validate

Validate every Plausible and Risky assumption with the cheapest thing that produces real
evidence:

- **Behavior of code, a library, or an API.** Run a 10 to 30 line script and capture the
  output, or read the implementation on `HEAD`. Docs describe intent, code shows behavior.
- **Data shape or infrastructure.** Read the migrations, the config, or the IaC, or run a
  read-only query or probe.
- **Performance or scale.** Do the back-of-envelope math first. Benchmark only when the math
  is too close to call.

Record each result as **confirmed**, **refuted**, or **partial**. Validate the risky one
first, even when it is the uncomfortable one. One careful read of the load-bearing function
beats a shallow read of 40 files. Delegate batched reads to a read-only search subagent
when the host has one.
