# Surfaces: test as the real user

Loaded from `SKILL.md` step 1. This is the single most important decision of the run. Who
is the product's user, and through what do they use it? Everything else follows from
answering that honestly. Identify the surface from what the product is, state it, and stay
on it.

| Product | User | Surface, and nothing less |
|---|---|---|
| Web app | end user at a screen | a real browser: clicking, typing, scrolling, reading |
| CLI tool | shell user | the built binary invoked in a shell, as the install docs say |
| Library or SDK | integrating developer | small consumer programs written against the public API |
| HTTP or RPC service | API client author | requests built from the public API docs alone |

A product can have several users, such as a web app with an admin UI and a public API.
Test each surface the change touches, as its own persona.

## Web app: the browser persona

- Interact as a person does. Click the actual button, type into the actual field, read
  what renders. Injected scripts and direct fetches bypass exactly the layer being tested.
  Use them only to diagnose a failure already observed, never to produce a verdict.
- **Visual validation is part of the job.** Check buttons, colors, borders, spacing,
  alignment, truncation, and the states users hit: hover, disabled, loading, empty, error.
  A wrong border is a finding with a screenshot, not a footnote.
- **UX inconveniences count.** Dead ends, unclear labels, missing feedback after an action,
  steps that feel needless. Report them as gaps even when the function passes.
- Manage the system through the product's own UI where a user or admin would. Create,
  update, and delete the entities the scenarios need there. Reach for a seed script or API
  only for state the UI cannot produce, and say so in the report.

## CLI: the shell persona

- Run the binary the way the docs install and invoke it. Do not use the source tree's dev
  entry point, unless that is what users get.
- Cover the shell contract: `--help` and its accuracy, exit codes, stdout against stderr,
  behavior in a pipe, garbage and missing arguments, interrupted runs.
- Error messages are UI. An unhelpful or misspelled one is a finding.

## Library or SDK: the developer persona

- **Write programs.** Small, out-of-tree consumer programs in a scratch directory. Install
  the package the way the README says and use only the public, documented API. That is the
  experience of a developer integrating it for the first time.
- Follow the docs literally. Every place they lied, omitted a step, or assumed unstated
  context is a finding, even when the code itself works.
- Exercise the advertised entry points, a realistic composition of them, and the error
  behavior a consumer will hit: bad input, misuse, missing config.

## Service or API: the client persona

- Build requests from the public API documentation alone, as an external client author
  would. Undocumented behavior needed to succeed is a finding.
- Check contracts, not just 200s: response shapes, error bodies, status codes, auth
  failures.
- [`http-assert`](https://github.com/korya/http-assert) automates this persona well. It
  makes curl-style requests with built-in assertions, is scriptable per case, and can wait
  for the service to come up ready, without a hand-rolled client.

## Readiness and fail-fast

Before executing cases, start the product the documented way and smoke-check the surface.
The page renders, the binary answers `--help`, the package installs clean, the API answers
a trivial request.

- The surface will not come up: the browser will not start, the app will not boot, the
  install fails. **Stop.** Everything that depends on it is BLOCKED. Report at once with
  what you tried. Do not push through. Do not slide sideways to a lesser surface, such as
  curl instead of a browser or importing internals instead of installing the package.
  That tests a different product and its verdicts are worthless.
- **Environment gate.** Name the environment you are pointed at. Clearly dev or local:
  mutate freely through the surface. Anything else, such as a shared staging, a demo, or
  anything prod-like: get the user's explicit confirmation before the first mutation.
  Without it, mutation cases are BLOCKED, not quietly run.
