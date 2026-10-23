# bug-fixture: user-service

A tiny in-memory user service used as a fixture for RCA evals.

Run the failing test:

```sh
cd evals/rca/fixture
python3 -m unittest discover tests -v
```

`BUG_REPORT.md` contains the support ticket that kicks off the investigation.
