# PR 32315 — reviewer P2 (PR as a change)

1. **Wanted?** `GRewrite.Config extends Rewrite.Config` (Core.lean:53), so `transparency` was already an
   accepted option that failed at the `gcongr` step. That makes the PR mostly a bug fix, and it is
   wanted. No duplicate found (no `egrw`; `erw?` in Mathlib/Tactic/ErwQuestion.lean is a debugging
   tool). The author explains why there is no separate `egrw`. No finding, beyond noting that erw-style
   rewriting is something Mathlib tries to remove (that is why `erw?` exists).
2. **Every hunk an improvement?** The `construct` -> `Construct ... .` comment edit sits inside a hunk
   that is rewritten anyway, and it joins the new explanatory comment, so it is fine. The core edit,
   docstring line and test all serve the purpose. The spelling of `default` is raised under Q4.
3. **One thing?** Yes: one fix in Core.lean, one docstring line and one test. The scope matches the title.
4. **Description?** It has a design choice (no `egrw`) but gives little motivation. It does not say the
   option already existed and was broken, does not explain the fix, and does not say the fix changes
   how the proof is built for every `grw` call. No discussion or downstream link. The bare
   `(transparency := default)` probably elaborates to `Inhabited.default = .all` rather than `.default`
   (inferred from core's `deriving Inhabited`; I could not check it with the tools). Mathlib writes
   `.default` in 8 places. Nothing suggests AI use, so there is no disclosure finding.
5. **Finishes the job?** `nth_grw`, `apply_rw` and `grewrite` forward their config items (Elab.lean:108-122),
   so they get the fix automatically. `mkHoleAnnotation` has no other user of this pattern in
   Mathlib/Tactic. The test gap: only the goal direction is tested, although the change flips the
   `forwardImp`-dependent flag for `at h` too. There is no negative test and no `guard_target`.
6. **Right place?** Yes: Core.lean for the backend, Elab.lean for the user docstring, and
   MathlibTest/GRewrite.lean for the tests, next to the existing `grw` tests.
