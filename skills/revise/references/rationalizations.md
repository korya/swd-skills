# Rationalizations: how reviews get obeyed instead of answered

Loaded when tempted to just accept, silently drop, or drive-by. Each row hands the PR's
judgment to whoever wrote the last comment.

| Shortcut | Why it fails |
|---|---|
| "It's well argued, or the reviewer is senior. Just take it." | Argument quality measures the writer, and authority is not validation. Reviewers with partial context argue well from wrong premises. |
| "Easier to make the change than to argue." | Every unjustified acceptance teaches the codebase a pattern nobody chose. A justified rejection costs one paragraph. |
| "While I'm in this file anyway..." | That is scope creep. Unrelated improvements go to DEFER tickets. This run changes only what an ACCEPT or PARTIAL verdict covers. |
| "It could matter at scale, better safe than sorry." | Optimizing for a load that does not exist buys complexity with nothing. If the scale may realistically come, that is a measured DEFER with a ticket, not code today. |
| "A guard is cheap, why not add it." | Every guard claims the case happens. One for a state nothing produces is dead code that tells the next reader the inputs can be something they cannot. A fallback there hides the failure it should surface. Accept a guard only where a writer or caller exists that produces the state. |
| "I'll skip replying on the rejected ones." | An unanswered finding reads as an ignored one. The reviewer re-raises it, and trust drops. Rejections are where the response matters most. |
| "It's vague, or I'm 60% sure. I'll decide anyway." | A guess at their meaning satisfies nobody, and a guessed verdict errs in the convenient direction. Both are NEEDS-INPUT. |
| "Quiet the reviewer with the minimal patch." | Appeasement patches fix the comment, not the code. ACCEPT means fix at the root or argue it does not need fixing. |
| "I'll fold the fixes in without updating the PR description." | The revision changed the PR. A stale description lies to the next reviewer. Re-submission includes the `/submit` revalidation pass, always. |
