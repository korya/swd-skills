# Architecture

## High-level shape

```
<diagram: layers, data flow, integrations>
```

<one-paragraph summary: what each layer is responsible for, what crosses what>

## Why each layer exists

### <Layer 1>

<paragraph: what problem this layer solves, why it's a separate thing>

### <Layer 2>

<paragraph>

## Key technical assumptions

<list important assumptions that, if violated, would break the architecture. Examples: concurrency model, auth model, data freshness expectations, single-tenant vs multi-tenant, API contract stability.>

- **<Assumption 1>:** <one-line description and why it matters>
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

<call out any non-obvious organizational decisions>

## What's intentionally simple in v1

<list deliberate omissions and the reason. Example: no auth, no background jobs, no real-time collaboration.>

## Future migration paths

<list known scaling/evolution paths that the architecture is prepared for. Example: Sheets → Postgres when row counts demand it.>
