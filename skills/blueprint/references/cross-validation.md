# Cross-validation: specs, architecture, conventions, codebase

Loaded from `SKILL.md` step 5. Covers steps 5 to 7.

## 5. Check the product specs

Find the specs and the invariants the change touches. For each affected requirement, name
it and the plan step that satisfies it. Citing a spec without that link is theatre.

- A violated invariant means the plan is not ready. Change the plan, or flag the spec as
  wrong. A spec change needs the user's review before code work begins.
- A new command, field, or behavior the spec does not mention means a spec update. Flag it.
- No spec for the area is a signal, not an exemption. Propose one or flag the undocumented
  behavior.

## 6. Check the architecture and the conventions

**6a. Architecture.** The change goes through the documented boundaries and seams, not
around them. Name every new risk it brings:

- new attack surface
- unbounded cost or fan-out
- async work outside the job platform
- a failure nobody would see in production

**6b. Conventions.** The most common plan failure is a default from training data. Examples
are `pnpm` where the repo uses yarn, port 3000 where the API runs on 9100, and `jest.mock`
where the codebase injects dependencies. Reading the repo prevents it.

Read the conventions on `HEAD`. The conventions doc comes first: the root `AGENTS.md` or
`CLAUDE.md`, and the docs of each component the plan modifies. Cite it. The lockfile, the
task runner, the test and lint config, and sibling files confirm what the doc says. They
do not replace it. Cover every category the plan touches:

- package manager, and the build, test, and run entry points
- test framework and mocking policy, lint and format
- migrations, ports and URLs, async machinery
- existing patterns to reuse

Record them in the plan under "Project conventions to follow", one bullet each:

> - **[`file:line`]** Convention: *what the doc says.* **Reflected in plan:** *which plan
>   steps follow it, and how.*

When a category does not constrain this plan, say so with a one-line reason. Silent
omission is the failure the format prevents. If you think a convention is wrong here, raise
it as a separate question. Never deviate silently.

## 7. Sweep the codebase

This step looks for conflicts that no single assumption captures. A check that one file
exists or one signature holds belongs in step 3 instead.

- **In-flight work.** Run `git log` on the touched area. Someone may be doing this already.
- **Duplicate logic.** Similar code elsewhere that the plan should reuse or consolidate.
  Confirm an existing pattern still fits before you copy it.
- **Callers of a changed contract.** Grep for callers, schemas, fixtures, and mocks.
- **Test infrastructure.** The layer of test the plan needs exists here, or the plan builds
  it.
