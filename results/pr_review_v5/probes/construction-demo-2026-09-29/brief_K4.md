# Pass 4 of a review: proofs

This review reads a PR in a fixed order, one pass at a time. Pass 0 built the PR model
(`model.md`). Pass 3 reviewed the statements and built constructions; what they established is in
`constructions_pass3.json`. Those are facts (a twin that compiled, a weaker statement that
compiled, what the area's siblings look like), not requests, and you may rely on them. Other passes
review names, prose, layout and location, and the PR as a change. **Do not review those, and do
not review the statements again.**

Your pass takes the point of view of the maintainer who will keep these proofs working while the
library around them is refactored. It asks of every proof the PR adds or changes, one family at a
time: **is this the proof the library would write?** You answer it by re-doing the proof the
library's way and compiling it. A request is a proof you built that is better, or something the
rebuilding showed.

Read `pr.md`, then `model.md`, then `constructions_pass3.json`, then `diff.patch`.

## What to construct, for every proof

1. **The rewrite in the idiom.** Re-do the proof, and each of its steps, with the library's
   standard closing tactics and combinators. Compile each attempt.
2. **The library as a tool.** For each step, whether an existing declaration closes it: one in the
   library, one elsewhere in the file, or one of the PR's own declarations (including the ones
   pass 3 compiled). Compile the step with it.
3. **The pre-PR proof.** For a declaration the PR modifies, compile its proof from before the PR
   (in `model.md`) against the statement as the PR leaves it.
4. **Derivations.** Where pass 3 compiled a twin or a dual, or a family has a partner a dual or a
   generator could produce, whether one proof should be derived from the other. Compile it.
5. **Repetition.** A fragment repeated across the family's proofs, extracted into a lemma and
   compiled.

Record every construction, including the ones that compiled and changed nothing.

## Tools

Run `./ptool describe` once to read every tool's description and arguments; call one as
`./ptool <tool> '<json arguments>'`. `lean_verify_edit` compiles the PR's file, with your edit,
against the PR's reviewed workspace: give `path`, `declaration_name` and a complete
`new_declaration`.

## Output

Write, in this directory:
- `constructions.json`: a JSON list, one object per construction, with keys `id` (`c1`, `c2`, ...),
  `kind` (`idiom_rewrite`, `library_tool`, `pre_pr_proof`, `derivation`, `extraction`),
  `objects`, `lean` (the Lean text you compiled), `compiled` (`true` or `false`), `result` (one
  line: what the tool returned) and `shows` (the fact it established).
- `findings.json`: a JSON list, one object per request, with keys `target`, `claim`,
  `requested_change`, `severity` (`blocking` or `advisory`), `evidence` and `construction` (the ids
  it rests on).
- `notes.md`: proof by proof, what you constructed and what it showed.
