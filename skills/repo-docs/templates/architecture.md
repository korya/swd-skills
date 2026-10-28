# Architecture

## High-level shape

```
<diagram: layers, data flow, integrations>
```

<One paragraph: what each layer is responsible for, and what crosses what.>

## Why each layer exists

### <Layer 1>

<Paragraph: what problem this layer solves, and why it is a separate thing.>

## Key technical assumptions

<The assumptions that would break the architecture if violated, such as the concurrency
model, the auth model, or data freshness.>

- **<Assumption>:** <one line on what it is and why it matters>

## Tech choices

| Decision | Choice | Why |
|----------|--------|-----|
| <e.g., Bundler> | <e.g., Vite> | <one-line reason> |

## What is intentionally simple

<The deliberate omissions and the reason for each, such as no auth or no background jobs.>

## Future migration paths

<Only the paths the code or its docs already prepare for. Delete this section otherwise.>
