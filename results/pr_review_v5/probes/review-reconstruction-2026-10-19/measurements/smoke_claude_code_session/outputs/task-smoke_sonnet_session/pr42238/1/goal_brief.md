# Goal brief

## 1. Kind of contribution

Maintenance (variables and performance) in one existing file, `Mathlib/Analysis/Normed/Operator/LinearIsometry.lean`. No new mathematics.

## 2. Capability

The file develops semilinear isometric embeddings and equivalences between seminormed modules over rings related by ring homomorphisms. Its opening `variable` declarations bring in four rings, with their carrier modules, the ring homomorphisms between each pair, and the inverse-pair and composition-triple instance assumptions on them. The fourth ring is needed by very few declarations. In the base text, the only ones are the associativity statements for composition of isometric embeddings (`LinearIsometry.comp_assoc`) and for composition of isometric equivalences (`LinearIsometryEquiv.trans_assoc`).

The contribution should make the file elaborate faster. It should do this by making the declarations that do not involve the fourth ring stop carrying the fourth-ring data and its instance assumptions. Those assumptions currently enlarge every typeclass search for ring-homomorphism inverse pairs and composition triples. The two associativity statements must still have access to what they need.

## 3. What must keep working

- Every declaration in the file that does not involve the fourth ring keeps exactly its current type.
- The two associativity statements keep their mathematical content: the same hypotheses and the same objects being composed, and the same conclusion (associativity of composition).
- Downstream uses in Mathlib of anything in this file keep compiling. The inputs do not say whether any use applies the two associativity statements with explicit `@`-style arguments.
- The file's other results, instances (for example the monoid and group structures on endomorphisms and automorphisms) and API are unchanged.

## 4. Open questions

- Should the two associativity statements keep their exact binder order? Or may the order of their implicit and instance arguments change?
- Should any other variables or instances in the opening block be trimmed too, such as third-ring data? Or is this contribution limited to the fourth ring?
- Should each of the two statements get its own local set of assumptions, or should they share one?
- How much of the speed-up is required? How is it to be measured (standalone elaboration time or benchmark instruction counts)?

## 5. Where the requirements come from

- Fourth ring used by only two declarations, and the aim of faster typeclass search and elaboration: the description (first and second paragraphs). The title also says this is a performance change. It is the current title, not verified to be the one at review time.
- Types of other declarations unchanged, and the two statements keeping their hypotheses and explicit arguments: the description (third paragraph). The change itself also shows this, since no statement text is edited.
- The question of exact binder order is open because the description says the order of implicit and instance binders changes. It does not say whether that is required.
- Speed-up magnitude: the description's fourth paragraph reports measurements. These are results, not requirements.
