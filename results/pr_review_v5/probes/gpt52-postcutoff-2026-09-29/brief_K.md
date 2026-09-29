# A review in two passes over the PR model: statements and the family, then proofs

This review reads a PR in a fixed order. The PR model at the end of the user message lists every
changed object with its kind and what changed, the declarations removed or renamed, and the
families and relations the change graph finds. Entries in the model are facts. A family marked
`hypothesis` is a suspicion from names: check the statements before you rely on it. Names, prose,
layout and location, and the PR as a change, are reviewed by other passes. **Do not review those.**

## Pass 3: statements and the family

Ask one question of every statement the PR adds or changes, one family at a time (a declaration in no
family is a family of one): **can the people and the automation that will consume these declarations
do their jobs with them?** Answer it by building what each consumer would build. A request is
something your construction could not do, or something it showed to be better.

### What to construct, for every family

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

## Pass 4: proofs

Then take the point of view of the maintainer who will keep these proofs working while the library
around them is refactored. Ask of every proof the PR adds or changes, one family at a time: **is this
the proof the library would write?** Answer it by re-doing the proof the library's way and compiling
it. Use what pass 3 established as facts (a twin that compiled, a weaker statement that compiled).

### What to construct, for every proof

1. **The rewrite in the idiom.** Re-do the proof, and each of its steps, with the library's
   standard closing tactics and combinators. Compile each attempt.
2. **The library as a tool.** For each step, whether an existing declaration closes it: one in the
   library, one elsewhere in the file, or one of the PR's own declarations (including the ones
   pass 3 compiled). Compile the step with it.
3. **The pre-PR proof.** For a declaration the PR modifies, compile its proof from before the PR
   (in the PR model) against the statement as the PR leaves it.
4. **Derivations.** Where pass 3 compiled a twin or a dual, or a family has a partner a dual or a
   generator could produce, whether one proof should be derived from the other. Compile it.
5. **Repetition.** A fragment repeated across the family's proofs, extracted into a lemma and
   compiled.

Record every construction, including the ones that compiled and changed nothing.

## Tools and output

`lean_verify_edit` compiles the PR's file, with your edit, against the PR's reviewed workspace: give
`path`, `declaration_name` and a complete `new_declaration`, or a line span and its replacement. If a
construction fails to compile for a reason unrelated to the question it asks, fix the construction,
not the conclusion. Submit your findings as the user message says; each finding's `evidence` names
the construction it rests on and what its compile returned.
