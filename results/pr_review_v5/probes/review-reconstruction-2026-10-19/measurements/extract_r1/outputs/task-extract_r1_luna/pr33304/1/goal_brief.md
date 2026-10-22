# Kind of contribution

Documentation only: corrections to file cross-references in existing Category Theory module documentation and an explanatory comment. No mathematical definitions, results, proofs, or API behavior are changed.

# Capability

Make the affected references to other library material accurate and useful for navigation under the current organization of the library. The references concern concrete-category guidance, functor and groupoid material, limits and preservation, localization, monoidal categories, and category-theoretic tactics. The contribution should clarify where readers can find the material being discussed, without changing the mathematical content or adding a new capability.

# What must keep working

Preserve the mathematical explanations, caveats, and descriptions surrounding the references, including the accounts of limits, localization, and monoids in a braided monoidal category. The text should continue to direct readers to material relevant to those explanations. Existing declarations and their behavior are outside the change and must remain unaffected.

# Open questions

The inputs do not establish whether the intended scope is limited to the affected references or includes a wider audit of Category Theory documentation. They do not prescribe a path style, whether references should identify files or broader locations, or how much surrounding prose should be reformatted. The current title suggests a reference correction, but does not settle that scope.

# Where the requirements come from

The description was absent at review start. The current title, “doc(CategoryTheory): fix file refs” (not verified to be the title at review time), supports the documentation and navigation goal, but does not specify its scope. The change itself edits references in module documentation and comments, including those in `ConcreteCategory/Bundled.lean`, `Groupoid/Subgroupoid.lean`, the functor-category limit files, `Limits/HasLimits.lean`, `Localization/Equivalence.lean`, and `Monoidal/Mon_.lean`; these edits support correcting the affected pointers while leaving surrounding mathematical content intact.