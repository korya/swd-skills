# Architecture

## High-level shape

```
<diagram: layers, data flow, integrations>
```

<One paragraph: what each layer is responsible for, and what crosses what.>

## Why each layer exists

### <Layer 1>

<Paragraph: what problem this layer solves, and why it is a separate thing.>

### <Layer 2>

<Paragraph.>

## Key technical assumptions

<List the assumptions that would break the architecture if violated. Examples: the
concurrency model, the auth model, data freshness, single-tenant versus multi-tenant, API
contract stability.>

- **<Assumption 1>:** <one line on what it is and why it matters>
- **<Assumption 2>:** ...

## Tech choices

| Decision | Choice | Why |
|----------|--------|-----|
| <e.g., Bundler> | <e.g., Vite> | <one-line reason> |
| ... | ... | ... |

## Project layout

```
<repo-root>/
├── ...
```

<Call out any non-obvious organizational decision.>

## What is intentionally simple in v1

<List the deliberate omissions and the reason for each. Example: no auth, no background
jobs, no real-time collaboration.>

## Future migration paths

<List the scaling or evolution paths the architecture is prepared for. Example: Sheets to
Postgres when row counts demand it.>
