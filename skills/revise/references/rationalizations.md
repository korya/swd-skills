# Rationalizations: how reviews get obeyed instead of answered

Loaded when tempted to just accept, silently drop, or drive-by. Each row is the
path of least resistance; each one quietly hands the PR's judgment to whoever wrote the
last comment.

| Shortcut | Why it fails |
|---|---|
| "It's well argued — just take it." | Argument quality measures the writer, not the claim. Reviewers with partial context produce excellent arguments from wrong premises; validation, not eloquence, decides. |
| "Easier to make the change than to argue." | Cheapest now, priciest later: every unjustified acceptance teaches the codebase a pattern nobody chose and invites the next reviewer to redecorate too. A justified rejection costs one paragraph. |
| "The reviewer is senior / it's the review agent — they know." | Authority is a reason to validate carefully, not a substitute for validating. They still haven't read this PR's intent, constraints, and history the way you just did. |
| "While I'm in this file anyway…" | That is scope creep wearing a toolbelt. Unrelated improvements go to DEFER tickets; this run changes only what an ACCEPT or PARTIAL verdict covers. |
| "It could matter at scale, better safe than sorry." | Optimizing for a load that doesn't exist buys complexity with nothing. If the scale may realistically come, that's a measured DEFER with a ticket — not code today. |
| "I'll skip replying on the rejected ones." | An unanswered finding reads as an ignored one; the reviewer re-raises it, trust drops, and the next review gets louder. Rejections are where the response matters most. |
| "This finding is vague — I'll interpret it charitably and fix something." | Fixing your guess at their meaning satisfies nobody and muddies the diff. Vague findings are NEEDS-INPUT: ask what they meant. |
| "I'm 60% sure — good enough to decide." | A guessed verdict is wrong 40% of the time in whichever direction was convenient. Below confident, the move is a batched question to the user, not a quiet call. |
| "Quiet the reviewer with the minimal patch." | Appeasement patches fix the comment, not the code — the defect survives under a cosmetic change. ACCEPT means fix at the root or argue it doesn't need fixing. |
| "I'll fold the fixes in without updating the PR description." | The revision changed the PR; a stale description now lies to the next reviewer. Re-submission includes the `/submit` revalidation pass, always. |
