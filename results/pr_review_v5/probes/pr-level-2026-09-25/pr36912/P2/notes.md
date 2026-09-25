# PR #36912 — PR-level review notes

1. **Wanted?** No. `my_add_comm` is `Nat.add_comm` (core; proof term is exactly that, used on 88 lines of Mathlib) and a special case of generic `add_comm` (additive `mul_comm`, Mathlib/Algebra/Group/Defs.lean:225). Pure duplicate; blocking, close the PR.
2. **Every hunk an improvement?** `push_proofs.sh` is the author's personal git/`gh pr create` script (hard-coded fork `batmeezy918`, `git add .`, push); unrelated to the library and unsafe to ship. Must be removed. The .lean hunk is covered by the question-1 finding.
3. **One thing?** Two unrelated things: a (duplicate) lemma and a workflow script. Covered by the question-2 finding (remove the script); no separate split request, since neither half should land.
4. **Description?** Describes the tooling ("Automated PR from Termux"), not the change: no motivation, no links, title not in `feat(...)` form. "Automated" without saying whether AI generated the content, so AI-use disclosure is missing. Blocking.
5. **Finishes the job?** No analogous places to update — nothing is genuinely added. The new module is not registered in Mathlib.lean (no entry near Mathlib.lean:364), folded into the question-6 placement finding. No automation or meta code, so no tests needed.
6. **Right place?** A `Nat` lemma in a personally named top-level file `Mathlib/Algebra/MyNewProofs.lean` does not fit Mathlib's subject-based layout; the script sits at the repo root instead of anywhere maintained (scripts/). Blocking, moot once the question-1 finding closes the PR.
