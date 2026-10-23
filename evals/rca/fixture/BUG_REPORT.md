# Bug report: customer support can't find users by email

**Reporter:** support@acme.test
**Severity:** P2
**First seen:** 2026-05-12 (reported by 4 separate agents in 24h)

## Symptom

Customer-support agents use the internal user-search tool to look up customers
by email when handling tickets. Multiple agents have reported that searches
return "not found" even though the customer is definitely in our system — we
can see them on Stripe, we've billed them, etc.

The agents have been working around it by paging the data team, who run a SQL
query and find the customer in the `users` table.

## Logs

```
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

(Same customer, three attempts, only one casing matched.)

## What support is asking

> Either fix the search, or tell us the rule for which casing to use. Right
> now we're just guessing and it's eating 5–10 minutes per ticket.

## Repro

The repo has a failing test that demonstrates it:

```sh
cd evals/rca/fixture
python3 -m unittest tests.test_search.SearchTests.test_search_finds_user_signed_up_with_mixed_case -v
```
