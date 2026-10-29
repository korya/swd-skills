# Surfaces: test as the real user

Loaded from `SKILL.md` step 1. Decide who the product's user is and through what they use
it. Testing a different surface tests a different product, so state the surface and stay
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
  what renders. Injected scripts and direct fetches bypass the layer under test. Use them
  only to diagnose a failure already observed, never to produce a verdict.
- **Visual validation is part of the job.** Check buttons, colors, borders, spacing,
  alignment, truncation, and the states users hit: hover, disabled, loading, empty, error.
  A wrong border is a finding with a screenshot.
- **UX inconveniences count.** Dead ends, unclear labels, missing feedback after an action,
  needless steps. Report them as gaps even when the function passes.
- Create, update, and delete the entities the scenarios need through the product's own UI.
  Reach for a seed script or API only for state the UI cannot produce, and say so in the
  report.

## CLI: the shell persona

- Run the binary the way the docs install and invoke it. Do not use the source tree's dev
  entry point, unless that is what users get.
- Cover the shell contract: `--help` and its accuracy, exit codes, stdout against stderr,
  behavior in a pipe, garbage and missing arguments, interrupted runs.
- Error messages are UI. An unhelpful or misspelled one is a finding.

## Library or SDK: the developer persona

- Write small, out-of-tree consumer programs in a scratch directory. Install the package
  the way the README says and use only the public, documented API.
- Follow the docs literally. Every place they lied, omitted a step, or assumed unstated
  context is a finding, even when the code itself works.
- Exercise the advertised entry points, a realistic composition of them, and the error
  behavior a consumer will hit: bad input, misuse, missing config.

## Service or API: the client persona

- Build requests from the public API documentation alone. Undocumented behavior needed to
  succeed is a finding.
- Check contracts, not just 200s: response shapes, error bodies, status codes, auth
  failures.
- [`http-assert`](https://github.com/korya/http-assert) automates this persona. It makes
  curl-style requests with built-in assertions, is scriptable per case, and can wait for
  the service to come up.

## Fail fast

The step-3 smoke check fits the surface. The page renders, the binary answers `--help`,
the package installs clean, or the API answers a trivial request. When it fails,
report what you tried. Do not push through, and do not slide sideways, such as curl
instead of a browser or importing internals instead of installing the package. A lesser
surface tests a different product, and its verdicts are worthless.
