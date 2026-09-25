# PR #32315: reviewer notes on the PR as a whole

1. **Wanted?** `GRewrite.Config` already extends `Rewrite.Config` (Core.lean:53), so the `transparency` option was already accepted and passed to `kabstract` (Core.lean:108). It was not usable because the gcongr step could not close the goal. Fixing an option that already exists is wanted, not churn, even though Mathlib discourages `erw` (the `erw?` tactic in Mathlib/Tactic/ErwQuestion.lean exists to help remove it). No duplicate exists, and I did not file a finding.

2. **Every hunk an improvement?** The only cosmetic edit is the comment `construct` -> `Construct ... .`. It sits directly above new comment lines it now introduces, so I did not ask for a revert, although the file's other comments are lowercase fragments. No hunk is unrelated to the PR. The Core.lean hunk also changes the default path (see finding 2).

3. **One thing?** Yes: one core change, one docstring line, one test, all serving the title. Scope matches.

4. **Description?** It gives no motivation or discussion link, and does not mention the change to the shared proof construction that every grw call goes through (about 488 uses in Mathlib; asked for the design note and a `!bench`). The spelling `(transparency := default)` in the title, description, docstring and test is not Mathlib's `.default`. A bare `default` is `Inhabited.default`, which is probably `.all` (finding 1, blocking). Nothing indicates AI assistance, so there is no disclosure issue to raise.

5. **Finishes the job?** `nth_grw`, `nth_grewrite`, `apply_rw` and `apply_rewrite` pass the config through (Elab.lean:108-122), and `grewrite`'s docstring points to `grw`, so there are no other places to update. No callers of `MVarId.grewrite` exist outside GRewrite/. The test is in the right file, but it covers only the goal path, ends in `simp`, and cannot tell `.default` from `.all` (finding 3).

6. **Right place?** Yes: Mathlib/Tactic/GRewrite/{Core,Elab}.lean and MathlibTest/GRewrite.lean are the natural homes.
