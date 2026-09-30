# Why gpt_5.2 high effort (Gr1) missed asks that Claude reached: post-cutoff and dev

Source: Gr1 full transcripts (`last_turn_file`), Claude `calls.jsonl`, `notes.md` and `findings.json`, and matcher notes from
`match_reasoning` (blinding: 43024 Gr1=R2, 43192 Gr1=R2, 33098 Gr1=R3, 33305 Gr1=R3, 33337 Gr1=R5, 33362 Gr1=R4).
Turn Tn is the n-th assistant record. Claude call numbers `#k` are 0-based line indices in `calls.jsonl`.
Per-ask detail, with quotes, is in `perask_post_dev.json`.

**How the classes were applied.** A class is the first one that fits the *issue the ask raises*. When a Gr1
finding targets the same site and the same issue but asks for a different fix, the class is FILED_DIFFERENT. When a
Gr1 finding sits at the same site on a different issue, it is recorded as a secondary class. I read
SEARCHED_WRONG_TERM as "never retrieved, although it searched"; NEVER_RETRIEVED is reserved for "never retrieved and
never searched" (no ask here fell into that class).

**Two corrections to the premise.** For three of these asks the matchers scored Gr1 *partial* on both cells, not *no*:
`p0008`, `d0014` and `d0046`. For three asks only one of Claude's two sessions reached: `p0008`, `d0046` and `d0047`.

## Per-ask table

| ask | PR | Gr1 cells | Claude | class (secondary) | one-line reason | lever |
|---|---|---|---|---|---|---|
| p0008 `_mono`→`_anti` | 43024 | partial | X1 yes, X2 partial | FILED_DIFFERENT (search regexes too narrow) | Diagnosed the wrong direction and compiled and filed `_of_le` (T57, F0), citing `isNoetherian_of_le`. The `_anti` name was in the PR title. Its `_anti` regexes required an `(h : s ≤ t)` binder, so `Set.Subsingleton.anti`-style precedents never surfaced. Claude X2 chose `_of_le` too. | loose naming-alternatives census, and honour the title (weak: coin flip) |
| p0014 `mk` gets `cat_disch` defaults | 43192 | no | both | EXAMINED_NOT_CONSTRUCTED | Read the parent structure's `:= by cat_disch` fields (T7). At T35 it compiled a different design, dropping `map_id`/`map_comp`, which failed (aesop). It never tried binders with defaults and filed nothing on `mk`. | `#check Parent.mk` signature comparison, and retry after a failed construction |
| p0015 `mkHom` gets a default too | 43192 | no | both | IN_VIEW_UNTARGETED (FILED_DIFFERENT: F3 remove mkHom) | `isoMk`'s `:= by cat_disch` (in the diff) and `Hom.naturality`'s (T7) were in view. Its mkHom calls were existence and duplication searches only (T2, T15, T28), with no edit. | intra-PR sibling diff (mkHom vs isoMk vs Hom) |
| p0016 `mkHom`→`homMk` | 43192 | no | both | SEARCHED_WRONG_TERM (FILED_DIFFERENT: F3) | Searched the parent only with the PR's spelling (`PresheafOfModules.mkHom` T2; `isoMk\|mkHom` with use_regex=false, 0 hits, T15). Its Presheaf.lean reads skipped line 220, where `homMk` is. | naming-alternatives search (component swap + census) |
| d0014 `by_cases!` + `coveringNumber_le_encard` | 33098 | partial | both | FILED_DIFFERENT (partial) | Flipped the split to `= ⊤` and compiled it (T32), but kept `iInf_le` + `simp`. The file's `IsCover.coveringNumber_le_encard` (line 135) was in view at T1. F6 filed. | directed lookup of in-file lemmas matching the goal shape |
| d0016 `calc` layout | 33098 | no | both | CONSTRUCTED_NOT_FILED (probably untargeted) | T44 compiled a rewrite with correctly indented calc steps. Its only comment concerns the `ε/2` arithmetic, and it filed nothing on that declaration. | file every compiled variant as a diff; style comparison with in-file calc blocks |
| d0041 101-char line | 33305 | no | both | IN_VIEW_UNTARGETED (tool masked) | The line was in the diff and in T1. The as-is compile returned `warnings: []` because no Mathlib linters run. It submitted `[]`, merge-ready, confidence 0.93, at T12. | lint-enabled compile or line-length check (tool fix) |
| d0046 `coe_`→`toLinearMap_` | 33337 | partial | X1 yes, X2 partial | FILED_DIFFERENT (opposite resolution) | T1 naming_norm returned the maintainer's exact name as the candidate. Gr1 instead restated the LHS as a coercion to keep `coe_` (T29 compiled, F0). Claude X2 also kept `coe_`. | file the naming_norm candidate, or both alternatives |
| d0047 aux inside `namespace Complex` | 33362 | no | X2 yes, X1 declined | IN_VIEW_UNTARGETED | The move was in the diff. Its calls around the aux (T29 usages; T33-34 privateModule linter) were about private/expose, not namespace placement. No edit, no finding. | enumerate section/namespace objects (weak: Claude 1/2) |

## 43192: Gr1 against the two high-effort calibration sessions

| | Gr1 (rep1, 47 turns) | calib (capped at $3, 36 turns, never submitted) | calib2 (43 turns, submitted) |
|---|---|---|---|
| parent in view | T7 structure fields with `:= by cat_disch` | T3 read Presheaf.lean 1-200 | T2 read 150-260 (includes `homMk`), T4 read 1-150 |
| parent constructor signature | never | declaration_search only | **T25 `#check PresheafOfModules.mk`**, printing `(map_id : … := by cat_disch)` binders |
| `mk` construction | T35: dropped the args, **failed**, no retry | T16: dropped the args, **failed**, no retry | T37: binders with defaults, **success**, filed F1 |
| `mkHom` construction | none | T28: default, success (never submitted) | T37: default, success, filed F2 |
| `mkHom` finding | F3: remove it | none | F2: add default |
| `homMk` | never in view | never in view | in view at T2, not used: IN_VIEW_UNTARGETED |

What calib2 did differently on `p0014`/`p0015` was one lookup: it printed the parent *constructor's* signature. The
printout shows the binder-with-default form directly. Both sessions that saw only the structure's field declarations
tried to drop the arguments, and both failed. Gr1 and calib2 spent similar turns and reasoning (47 vs 43 turns; 221k vs 225k reasoning tokens;
calib 187k before its cap), so effort does not explain the difference. On `homMk`, having the object in view
(calib2) did not help; Claude's route was a name census.

## Per-session coverage and filing of its own compiled variants

"Named" means some call's arguments name the declaration. "Read only" means it was in view only through file reads.
Every session submitted voluntarily, before the 80-turn cap.

| session | turns / calls / findings | changed decls named in calls | never named | successful edits not filed |
|---|---|---|---|---|
| 43024 Gr1 | 60 / 166 / 1 | `isMulCommutative_mono` (T1…T57), `setLike_mul_comm` (T2, T59 failed) | none | none (T57 → F0). The T52/T59 edits failed because `declaration_name` mode keeps the original docstring/attribute line, so a new docstring does not parse. |
| 43192 Gr1 | 47 / 65 / 4 | core abbrev, `mk` (T6, T35 failed, T44), `mkHom` (T2 search only), `isoMk` (T2; parent T23-25), `obj`/`map` (T37 #check), `unit`, `restrictScalars`/`pushforward₀` (T46 #check) | `pushforward`, `pullback`, `pullbackPushforwardAdjunction` (read only, T1) | none: its only edit (T35) failed |
| 43192 calib2 | 43 / 73 / 4 | all 12 (some only inside another edit's text) | none | none (T37 → F1, F2; T40 → F3) |
| 33098 Gr1 | 49 / 84 / 9 | 14 of 16 | `minimalCover_subset`, `isCover_minimalCover` (read only) | **T38** (`exists_set_encard_eq_coveringNumber` refactor) and **T44** (`coveringNumber_subset_le`, whose edit contains the d0016 layout). About 10 calls (T4-T45) probed whether a `Nonempty` hypothesis is found by instance search; none were filed. |
| 33305 Gr1 | 12 / 37 / 0 | all 7 module docs (headers read at T1, targets checked) | none | no edits made |
| 33337 Gr1 | 35 / 61 / 1 | the 3 renamed lemmas and the removed alias | `starProjection_le_starProjection_iff`, `IsSymmetricProjection.le_iff_range_le_range` (read only, T1 and T16 on Positive.lean) | none (T29 → F0) |
| 33362 Gr1 | 41 / 61 / 6 | 8 of 9 theorems, including `schwarz_aux` (T1, T29) | `affine_…_eq_div'` (read only) | **T28** (alternative proof of `dist_le_dist_of_mapsTo_ball_self`) and **T30** (a probe of `norm_dslope_le_div_of_mapsTo_ball`). T27 → F5. |

None of the nine misses comes from never touching the ask's object. The weakest touch is `mkHom` (p0015), named only
in searches.

## Synthesis

- **Retrieval was rarely the gap.** The evidence was in Gr1's context for 8 of 9 asks. The exception is `p0016`, where
  every search used the PR's own spelling. The misses sit after retrieval: choosing between fixes, constructing the fix,
  and filing it.
- **Three misses are choices of fix, not failures to look.** On `p0008`, `d0046` and `d0014`, Gr1 filed at the site,
  on the same issue, with another defensible fix (`_of_le`; a coercion restatement; the split flipped without the
  lemma). The matchers scored all three partial. On two of them one Claude session made the same choice, so they carry
  little signal about the model gap.
- **Construction took a wrong first attempt and no second.** On `p0014`, Gr1 (and calib) compiled the nearest radical
  design, dropping the arguments. It failed, and Gr1 moved on. calib2 got the binder-with-default form from a
  `#check Parent.mk` printout. The shape of the comparison lookup (constructor signature vs source) looks like the
  lever on one PR, from one contrast; provisional.
- **Intra-PR sibling comparison is missing.** `p0015`: the PR's own `isoMk` carried the default next to `mkHom`.
  Gr1 never diffed the siblings and instead filed "remove mkHom".
- **Some compiled work goes unfiled** (33098 T38 and T44; 33362 T28 and T30), but only `d0016` might hinge on it, and
  there the indentation looks incidental. Evidence for "persisting conclusions" as the lever is thin here.
- **One miss is the tool's.** `d0041` needs a lint the compile check does not run (`warnings: []`). Claude got around
  it with shell `len()` and `set_option linter.style.longLine true`. Gr1, with no shell, declared the PR merge-ready.
  Separately, `declaration_search` false positives cost 43024 a 25-call chase after a nonexistent
  `IsMulCommutative.mono`, re-checked after T15 had returned "Unknown constant". That is consistent with reasoning not
  being carried between turns, but it cost turns, not this ask.
- **Budget did not bind.** All six Gr1 sessions stopped on their own at 12-60 turns (cap 80). The long ones spent 140k-220k
  reasoning tokens, largely on repeated or tangential checks. A larger budget is not the indicated lever.
- **Robust gap asks: 6 of 9.** Only `p0014`, `p0015`, `p0016`, `d0014`, `d0016` and `d0041` were reached by both Claude
  sessions. The other three (`p0008`, `d0046`, `d0047`) are 1/2 for Claude, which is within the matcher/replication
  noise noted in CLAUDE.md. Everything here is one Gr1 run: provisional.
