# Pass 3 of a review: statements and the family

This review reads a PR in a fixed order, one pass at a time. Pass 0 built the PR model
(`model.md`): every changed object with its kind and what changed, the declarations removed or
renamed, and the families and relations the change graph finds. This PR adds no definitions, so
there is no pass 2. Later passes review the proofs, then names, prose, layout and location, then
the PR as a change. **Do not review those.**

Your pass asks one question of every statement the PR adds or changes, one family at a time (a
declaration in no family is a family of one): **can the people and the automation that will
consume these declarations do their jobs with them?** You answer it by building what each consumer
would build. A request is something your construction could not do, or something it showed to be
better.

Read `pr.md`, then `model.md`, then `diff.patch`.

## The rule of the model

Entries in `model.md` are facts. A family marked `hypothesis` is a suspicion from names: check the
statements before you rely on it.

## What to construct, for every family

1. **The user's usage.** Write one or two short `example`s that a downstream user would write with
   the family: apply it at the generality and in the form a client needs, with the arguments a
   client has in hand. Compile them with `lean_verify_edit` (insert them after the family, in line
   mode). An argument the client must supply awkwardly, a statement it must unfold first, a lemma
   it reaches for and cannot find in the PR, a twin it needs: each is an obstacle.
2. **The next developer's generalised statement.** For each member, the weakest statement that
   still compiles with its proof: drop or weaken each hypothesis and typeclass argument, make a
   literal a parameter. Compile each attempt. What compiles is a fact.
3. **The family closure.** Find the pattern of twins the area uses for this shape (read the file
   and its neighbours with the tools: left and right, a dual, an additive version, an `iff`, the
   other side of a pair, the weaker and stronger versions). State each twin the pattern expects
   and the PR lacks, and compile it, deriving it from its partner where a dual or a generator
   applies. Check also whether one member is a special case of another, or says the same thing.
4. **Automation's view.** For each statement, would automation use it, and is it registered so
   that it can: find how the file's sibling declarations of the same shape are registered (count
   them with the tools), and where it matters compile an `example` closed by the automation with
   and without the attribute.
5. **Binders and form against the area.** Compare each member's binders (explicit, implicit,
   instance-implicit), its section structure and `variable`s, and its statement form with how the
   file and its directory write the same kind of declaration (count with `content_search`), and
   with the family's other members.

Record every construction, including the ones that compiled and showed nothing wrong.

## Tools

Run `./ptool describe` once to read every tool's description and arguments; call one as
`./ptool <tool> '<json arguments>'`. `lean_verify_edit` compiles the PR's file, with your edit,
against the PR's reviewed workspace. If a construction fails to compile for a reason unrelated to
the question it asks, fix the construction, not the conclusion.

## Output

Write, in this directory:
- `constructions.json`: a JSON list, one object per construction, with keys `id` (`c1`, `c2`, ...),
  `kind` (`usage`, `generalised_statement`, `twin`, `closure_check`, `automation_check`,
  `binders_form_check`), `objects` (the declarations it is about), `lean` (the Lean text you
  compiled, or the search you ran), `compiled` (`true`, `false`, or `null` for a search),
  `result` (one line: what the tool returned) and `shows` (the fact it established, stated as a
  fact about the code, not as a request).
- `findings.json`: a JSON list, one object per request, with keys `target`, `claim` (the present
  problem), `requested_change` (the concrete change), `severity` (`blocking` or `advisory`),
  `evidence` (what the construction showed) and `construction` (the ids it rests on).
- `notes.md`: family by family, what you constructed and what it showed.
