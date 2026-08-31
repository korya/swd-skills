# Surfaces: test as the real user

Loaded from `SKILL.md` step 1. The single most important decision of the run: who is the
product's user, and through what do they use it? Everything else follows from answering
that honestly. Identify the surface from what the product *is*, state it, and stay on it.

| Product | User | Surface — and nothing less |
|---|---|---|
| Web app | end user at a screen | a real browser: clicking, typing, scrolling, reading |
| CLI tool | shell user | the built binary invoked in a shell, as installed docs say |
| Library / SDK | integrating developer | small consumer programs written against the public API |
| HTTP / RPC service | API client author | requests built from the public API docs alone |

A product can have several users (a web app with an admin UI and a public API): test each
surface the change touches, as its own persona.

## Web app — the browser persona

- Interact as a person does — click the actual button, type into the actual field, read
  what actually renders. Injected scripts and direct fetches bypass exactly the layer
  being tested; use them only to diagnose a failure already observed, never to produce a
  verdict.
- **Visual validation is part of the job**: buttons, colors, borders, spacing, alignment,
  truncation, and the states users hit — hover, disabled, loading, empty, error. A wrong
  border is a finding with a screenshot, not a footnote.
- **UX inconveniences count**: dead ends, unclear labels, missing feedback after an
  action, steps that feel needless. Report them as gaps even when the function passes.
- Manage the system through the product's own UI where a user or admin would — creating,
  updating, deleting the entities scenarios need. Reach for a seed script or API only for
  state the UI genuinely cannot produce, and say so in the report.

## CLI — the shell persona

- Run the binary the way the docs install and invoke it — not the source tree's dev
  entry point, unless that is what users get.
- Cover the shell contract: `--help` and its accuracy, exit codes, stdout vs stderr
  separation, behavior in a pipe, garbage and missing arguments, interrupted runs.
- Error messages are UI. An unhelpful or misspelled one is a finding.

## Library / SDK — the developer persona

- **Write programs.** Small, out-of-tree consumer programs in a scratch directory,
  installing the package the way the README says and using only the public, documented
  API — the experience of a developer integrating it for the first time.
- Follow the docs literally; every place they lied, omitted a step, or assumed unstated
  context is a finding, even when the code itself works.
- Exercise the advertised entry points, realistic composition of them, and the error
  behavior a consumer will hit (bad input, misuse, missing config).

## Service / API — the client persona

- Build requests from the public API documentation alone, as an external client author
  would; undocumented behavior needed to succeed is a finding.
- Check contracts, not just 200s: response shapes, error bodies, status codes, auth
  failures.

## Readiness and fail-fast

Before executing cases, start the product the documented way and smoke-check the surface:
the page renders, the binary answers `--help`, the package installs clean, the API
answers a trivial request.

- Surface won't come up — browser won't start, app won't boot, install fails? **Stop.**
  Everything depending on it is BLOCKED; report immediately with what you tried. Do not
  push through, and do not slide sideways to a lesser surface — curl instead of a
  browser, importing internals instead of installing the package. That tests a different
  product and its verdicts are worthless.
- **Environment gate.** Name the environment you are pointed at. Clearly dev or local →
  mutate freely through the surface. Anything else — shared staging, demo, anything
  prod-like — get the user's explicit confirmation before the first mutation; without it,
  mutation cases are BLOCKED, not quietly run.
