# Testing conventions

- `unittest`; `tests/` mirrors `app/`.
- Money and lookup paths require failure-path tests (invalid input, not-found, limit
  exceeded) — not just the happy path.
- Run: `python3 -m unittest discover tests -v`
