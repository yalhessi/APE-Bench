# PR 36856: PR-level review notes

1. **Wanted?** Correcting the misspelled surnames (Domingues to Domínguez, Margalef-Roig to Margalef Roig) is a real fix, and nothing in Mathlib duplicates it. The key rename is cheap, since the key has only 3 citations, all in Immersion.lean. But the new key is still not canonical (see finding 1).
2. **Every hunk an improvement?** Moving the translation remark from the title into a note matches the existing `note = {Translated from ...}` form (about 10 entries, e.g. references.bib:741, 770, 1818), so it counts as an improvement. The publisher rewrite is only a change of style, and the bib has no convention for that field (23 of 254 entries use the zbMATH 'City: Publisher' form). Finding 2 asks to revert it.
3. **One thing?** Yes. Every hunk concerns this one bibliography entry and its citations, and the scope matches the title.
4. **Description?** It gives the motivation and sources for each change and discloses AI assistance (Codex). It matches the diff. There is no discussion to link and no dependency.
5. **Finishes the job?** Every citation of the old key is updated (whole-tree grep for `roigdomingues`: only Immersion.lean and the bib). The 'canonical names' goal is only half met: the prose 'Roig and Domínguez's' and the key still use only the maternal surnames. The precedent is `cabreragarciarodriguezpalacios2014` (finding 1). No automation is involved.
6. **Right place?** Yes. The bib entry is in docs/references.bib and the citations are in the file that cites the book.
