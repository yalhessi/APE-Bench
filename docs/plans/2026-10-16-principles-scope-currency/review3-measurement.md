# Adversarial review 3, part 1: are the step-4 verdicts right? (2026-10-17)

Reviewer: an independent attack on the measurement behind step 4 of
`results/pr_review_v5/probes/stage-h-departures-2026-10-16/` (claims (a) and (b), and the check and audit rows that
(c)-(f) stand on). I read `PROTOCOL.md`, `RESULTS.md`, both briefs, `score_step4.py`, `build_audit_packet.py`, every
`checks/*.jsonl` row, `audit.jsonl` (only after labelling the rows myself), the step-3 readings, `follow.jsonl`, the
step-4 commit bodies and `review2-departures.md`. Nothing that spends was run. No tracked file was changed except this
one.

**Scripts and outputs**, all in
`/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/a142d916-dd29-4521-a449-00e1db067b18/scratchpad/rev3/measure/`:
- `t.sh` runs `cli tool` on a PR's reviewed workspace with my own `--workdir` (`ws_<PR>`);
- `mk.py` builds a `lean_verify_edit` request; `res.sh` summarises a result;
- `c/*.json`, `c/*.out` hold every candidate I compiled and Lean's answer (28 compiles, one at a time);
- `ws.py` prints a place's declaration in the reviewed file;
- `p084.py` re-measures the line joins; `p126.py` re-runs the spelling searches;
- `join.py` joins checks, audit, my labels, readers and merge outcomes, and recomputes the step-4 numbers;
- `denoms.py` checks the scorer's denominators; `boot.py` gives intervals; `sens.py` gives the line under each reading.

## Numbers computed for this review

| what | value |
|---|---|
| Compile-rule and P011 departures re-compiled from the evidence text | 20 candidates at 17 places, all `compiled`, no new errors or warnings: open K001, K003, K004, K014 (2), K015, K024 (2), K028 (2), K031, K053, K061, K062, K065; calibration K010, K034, K050, K056, K057 |
| Negative controls (the edit is really applied) | 4 of 4 fail as they should: K031 without `simp`, K003 without the iso lemma, K023 with an unknown name, K017 with an unknown attribute |
| P010 `conforms` spot-compiles | K040 (drop `[IsEmpty m]`) and K058 (drop `[Nontrivial S]`) fail to synthesise, as the rows say |
| The calibration miss K023 | the maintainer's asked derivation, `have h : … := update_eq_self i₀ f`, **compiles** in the reviewed workspace; `update_eq_self` is at the base, `Logic/Function/Basic.lean:546`; the merged file uses it (line 818) |
| Search rows re-run (grep at base and reviewed tree) | K002, K041, K043, K017, K054, K060, K016, K027: every fact the checker states holds |
| K017's variant | adding `+to_dual` to `Iso.map_hom_inv_id_app` in the reviewed workspace compiles; at the clone's HEAD the two lemmas still lack it |
| K002/K041 later history | `isMeagre_biUnion` was added later by #33308; there is still no meagre `sUnion` lemma |
| Read rows re-measured (codepoints) | K063 93, K044 89/88/87, K009 75, K013 80/74, K048 97, K059 92, K033 99/97: all as the checkers wrote |
| My blind labels against the audit, 48 `departs` rows | same call on 44; differ on K015, K053 (I say literal), K002, K041 (I say contested) |
| Open places, PRs | 59 open places on **11** PRs (28678, 30652, 37190 carry only asked places) |
| Section-1 line per place (either reader `conforms`) | strict 8 of 37 = 22%, Wilson 95% **11% to 37%**; written 20 of 37 = 54% (38% to 69%) |
| Ask rate per departure, cluster bootstrap over PRs | strict: 6.2% [4.7, 9.1] with 6 asks, 8.2% [**6.3, 11.9**] with 8; written: 4.1% [3.4, 5.5], 5.4% [4.6, 7.2] |
| Literal open departures in code an ask on another rule rewrote | 5 of 27 (K001, K062, K012, K013, K065); at 3 the ask removed the departure (K001, K062, K065) |
| Literal open departures that persist at merge in substance | **23 of 27** (20 unchanged, plus K012, K013, K024 whose declaration changed elsewhere); none changed toward its own rule |

---

## 1. Re-verifying the 27 literal departures (and the 15 looser ones that compile)

**Compile rules and P011.** Every candidate the evidence describes compiles in the reviewed workspace, with no
new error and no linter warning. That includes the two that decide most of the strict line: the hinted `aesop`
at K001 and K062, and the one-call `simp [domain_sSup, …]` at K014. It also includes K031's `use 1; simp`. The
negative controls show the tool applies the edit, attributes included.

Does each candidate do what the rule's check asks?
- **P005 (7 of 7 literal): yes, by the letter.** The check allows hints and lists its tactics as examples. K031
  replaces a `rw` chain that closes the goal left by `use 1`; the trigger names a `rw` chain closing "a goal or
  branch", so it is literal. Both readers labelled it `departs`, citing the same file's `use 1; simp`. K001 and
  K062 re-encode the manual step as an `aesop` rule. That meets the letter and is twice as long (78 against 39
  characters).
- **P011 K061: literal** (shorter, from existing lemmas). **K030: looser**, as the audit says: the derivation is one
  line shorter but longer in characters, and the check asks for "shorter".
- **P040 K004 and K028: literal, K004 at the edge.** K028's `.trans Fin.forall_fin_one` is shorter and plainly reads
  no worse. K004 adds `Filter.mem_of_superset`, so it is not built only "from the same lemmas"; it matches the
  file's own `IsMeagre.mono` term. S1 named this exact candidate and judged it "reading no better"; S2 judged
  that any term would need `▸`.

**Search rules.** The facts hold everywhere. Whether the rule's check calls them departures is another matter.
- **K043 (P100): literal.** `homMk₃_app_two` to `homMk₅_app_five` keep `⟨n, by valid⟩`; the PR changed only
  `homMk₂_app_two`. They are unchanged at the clone's HEAD.
- **K017 (P100): literal by the letter, contested as a sibling.** The check says "in the file and library", and the
  variant compiles. But `map_hom_inv_id_app` states a bifunctor's `(F.map e.hom).app Z`, not a natural iso's
  component. The PR's title scopes it to one file.
- **K002 and K041 (P100): contested.** The check's departure is "a sibling exists for which the PR provides no
  corresponding variant or change". The existing siblings of `IsMeagre.union` (`IsGδ.union`,
  `BaireMeasurableSet.union`, `IsMeagre.inter`) need nothing. No existing sibling of `isMeagre_iUnion` lacks the
  countable generalisation either. The departure appears only if P100 is read as "complete this structure's
  family as the analogous structures have it". One of the packet's maintainer asks supports that reading ("add
  the `iSup` versions alongside"). The check's wording does not. The two rows are one omission counted twice.
- **K054 (P126): literal, at the edge.** It is the only line in the file that starts with `: `; 10 others end with
  ` :`. Colon placement is a layout choice, but so is the trigger's own example, "an attribute inline or on its
  own line".
- **K060 (P126): literal.** `(D R S) (P.val …)` at line 96; lines 57, 82, 143 and 147 omit the parentheses.
- **K016 (P126): contested.** The twin at 829 uses the notation, but the file splits about evenly. The
  maintainer's own suggestion on this PR spells `tprod R fun _ ↦ m`.
- **K027 (P254): looser, nearer conforms.** The PR only removed `private`, so the name existed at the base. The
  names `norm_map_zero'`, `norm_add_le'` and `norm_neg'` are `norm_` plus the `AddGroupNorm` field each fills.

**Read rules.** All 12 measurements reproduce (table above). Two of them have a history the check does not see.
- K048's break existed before the PR; removing `private` is what made the join fit.
- K007 and K055 are one pair, counted at both declarations. The repeated binder now carries an autoParam
  (`:= by cat_disch`) that the old `variable` line did not.

**Changes a headline?** No verdict is wrong as computed. Two rows the audit calls `looser` are literal departures
of the rule as written (K015, K053). Two rows it calls `literal` rest on a reading the check does not state
(K002, K041).

## 2. An independent re-audit

I labelled every `departs` row against `rules.json` before opening `audit.jsonl`'s `why`. Disagreements:

| row | audit | mine | why |
|---|---|---|---|
| K015, K053 (P018) | looser | **literal** | `simpa … using` is named in P018's `required` and in one of the packet's two maintainer examples. The audit saw `required` and still followed the check's parenthetical, as its brief told it to |
| K002, K041 (P100) | literal | **contested** | see §1: the check's "a sibling exists" is met only under a family-completion reading |
| K016 (P126) | looser | contested | same effect on the strict count |

On the rows the brief singled out, I agree with the audit:
- K031 is literal;
- K001 and K062 are literal, by the letter;
- K054 is literal, at the edge;
- the remaining 13 looser rows are looser.

K021 is closest to the line: a named form (a `rw` list), reached by swapping the `exact` term for a new lemma.

**Where my labels put the lines** (`sens.py`):

| reading | the line (reader-`conforms` cells where the check departs) | region | substantive departs | all open departs |
|---|---|---|---|---|
| checkers' verdicts | 32/64 = 50% | ≥ 30% | 31/48 | 42/59 |
| audit strict | 14/64 = 22% | mixed | 16/48 | 27/59 |
| strict, plus the `required` forms (K015, K053) | 15/64 = 23% | mixed | 18/48 | 29/59 |
| the same, with K002 and K041 not counted | 12/64 = 19% | mixed | 16/48 | 27/59 |
| audit strict, without the 4 literal candidates longer than the code (K001, K004, K062, K065) | 7/64 = 11% | mixed, at the line | 12/48 | 23/59 |
| the same, without K002 and K041 | 4/64 = 6% | ≤ 10% | 10/48 | 21/59 |

The last two rows are not pre-registered: `longer` was fixed as changing no verdict. They are a sensitivity, not a
correction. They show the line can land in any of its three regions, depending only on how the rule is read.
My own literal labels fall in "mixed" (19-23%), on the same side of both lines as the audit.

## 3. The `conforms` rows

- **K023 is not a scope miss.** The audit marks it `incomplete` because "recent master was not searched", and
  RESULTS repeats that. The asked lemma is at the base. The maintainer's derivation compiles in the reviewed
  workspace (`c/K023ask.out`), and it is what merged. The check searched for an equivalence that replaces the
  whole declaration; the ask replaced a one-line `have` inside it. That is a miss at the check's grain.
  - Review 2 found the same grain miss in the step-2 readers (H055).
  - The same `have` goal is open place K065 (P005), which the check counts as an unasked literal departure. An
    ask on another rule covered it.
- **P010 (K019, K025, K036, K040, K058): done as described.** I re-compiled K040 and K058; both fail. At K019, K040
  and K036 the hypothesis is the point of the declaration (`[IsEmpty m]` in a lemma about empty matrices), so the
  rule's situation hardly occurs. These rows dilute *d*. They are not wrong.
- **The other 12 conforms rows** (P100, P126, P254) are plausibly done as described. I did not re-run their
  searches; review 2 verified several of them at step 2. K049's derived name was inferred and not compiled, as
  its checker said.

## 4. Leaks and comparability

**Leaks.** No packet or brief carries an `asked` flag, a reader label, a note or a score; I grepped all 66 packets
and the 14 rendered briefs. Several channels stayed open, though, and the logs cannot rule them out.
- **Results files.** The checkers wrote into the directory that holds `step3_items.jsonl` (with `asked`) and
  `readings/`. Nothing but the brief kept them out. One checker read `checks/30652.jsonl` (75ed736e). That row
  carries nothing about its PR.
- **Commit bodies.** They name calibration items ("a calibration place (asked)": 4027071c, 75ed736e, dcab8630).
  `git log` was not forbidden. The step-3 commit adds `step3_items.jsonl` with its flags.
- **The Mathlib clone.** It holds every merged PR. `declaration_search` is base-only, but a checker with a shell
  could grep the clone.
- **The logs.** `calls_*.log` records only `cli tool` calls, so none of this can be ruled out from them.

The evidence I have argues against copying. The 35140 checker failed first with another lemma, and its
calibration derivations differ from the merged code (merged: `IsLimit.equivOfNatIsoOfIso`). The 28678 one
differs too (`⟨InvImage.wf ULift.down wellFounded_lt⟩` against the merged `InvImage.wf down h.wf`).
- *Smallest fix:* run checkers in a worktree with no `results/`, and no clone beyond the base, and log their
  shell.

**Comparability: section 1 does not compare like with like.**
- A reader's `departs` means "a maintainer holding the rule … would ask here". That is a normative bar.
- A reader's `conforms` means "the code already does what the rule asks, or its check would fail".
- A place where the literal check passes but no maintainer would ask has no label of its own. It goes to
  `conforms`, `excluded` or `unclear`.
- So "reader `conforms`, check `departs`" mixes two things: readers who did not check, and readers who applied a
  reason not to ask.

Reading the reader notes on the 14 strict cells:

| why the reader said `conforms` | cells | rows |
|---|---|---|
| predicted the letter wrongly (no hinted finisher, in-file scope only) | 9 | K001 ×2, K062 ×2, K014 ×2, K017 ×2, K065 |
| read P100 as "an existing sibling left without the change" | 3 | K002 ×2, K041 |
| judged that a term would read no better (S1 named this candidate) | 2 | K004 ×2 |

So "not checking" is 9 of 64 cells, 14%. That is "mixed", not the 30% "largely not checking". Also, the readers'
packets truncated long declarations. Both readers said `unclear` at K024 because "the proof is truncated", while
the checkers had the whole workspace.

**Denominators** (`denoms.py`).
- Section 1 uses reader `conforms` only, as pre-registered. Ten open substantive cells carry `unclear`,
  `needs_tools` or `excluded`, and 8 of them sit at check departures. They drop out.
- Section 2's reader shares count `excluded` (K022, K045 by S2) as non-departures. The check has no such category.
- Pooling S1 and S2 counts a place twice when both say `conforms`. Per place, the strict line is the same 22%
  (8 of 37). The 8 places come from 5 PRs, and K001/K062 are twins.

## 5. What (c), (d) and (f) stand on

- **(c), the arithmetic.** Reproduced: 46% and 71%; 6.2%, 4.1%, 8.2% and 5.4% (8 asks over 197).
  - Weighting *d* by each rule's share of the 199 unasked places gives 43% strict and 66% written, so 6.5% and
    4.4%.
  - Under the strict reading the 95% interval with 8 asks reaches 11.9%, so step 2's 10% is not excluded. "Stays
    near 5%" holds for the checkers' verdicts only.
  - 3 of the 27 literal departures were removed by an ask on another rule (K001, K062, K065).
- **(d).** The numbers stand and understate survival.
  - Five of the seven changed or gone literal departures sit in a declaration an ask rewrote.
  - At K012 and K013 the merged signatures keep `{F : C ⥤ D}` twice and the break after `:`. At K024 the merged
    `map_inj` term and `intro k; simp only` are unchanged.
  - So 23 of 27 persist, and none was changed toward its own rule.
- **(f), the silence-test sample** of "20 unchanged literal departures":
  - it is 18 distinct omissions (K002/K041 and K007/K055 are pairs);
  - 11 of the 20 sit on two PRs (33879: 7, 26979: 4);
  - 2 rest on the contested P100 reading;
  - it leaves out K012, K013 and K024. Those departures survived in declarations a maintainer was actively
    reviewing, so they are the sharpest test of a reason not to ask.
  - The asked contrast set is 5 of 7 P011, so it confounds being asked with the rule.

## Verdicts

- **(a) Calibration passes, 6 of 7: stands as a count, weakened in what it shows.** I reproduced all six by compile
  or measurement. The miss is not "searched the base only": the asked derivation uses a base lemma and compiles.
  The check looked at the wrong grain. Calibration is 5 of 7 on P011 and measures sensitivity only. It cannot
  catch over-called departures, which is the risk under the checkers' 71%.
- **(b) The line is reading-dependent: stands, weakened as stated.**
  - Strict is 19-23% under my labels, per place 22% with 95% interval 11-37%, which spans 30%.
  - The rows that decide it are mainly P040's "reads no worse": 8 cells, which alone cross 30%. P018 contributes 5
    cells, not "six merges"; two of the six merges are literal under the rule's `required`.
  - Dropping the 4 longer literal candidates puts it at 11% (6% with the P100 pair contested).
  - The reader label is not the check's question, so even the strict cells are 9 "not checking" and 5 reading or
    judgement.
- **(c) 46-71%, ask rate 4-8%, "stays near 5%": the rows stand; the conclusion is weakened.** Every literal verdict
  I re-ran holds, except that K002 and K041 are contested. The strict estimate's interval includes 10%, the open
  places are on 11 PRs, not 14, and 3 literal departures were covered by other asks.
- **(d) 20 of 27 unchanged: stands, and understates.** 23 of 27 persist in substance. None of the changes is toward
  the rule.
- **(e) No `not_when` on the ten (11 of 52 overall): stands.** The hinted-`aesop` example is real (compiles, 78
  against 39 characters). The 4 longer literal candidates carry 7 of the 14 strict cells, which is consistent with
  the hypothesis but does not test it.
- **(f) Silence test on the 20: weakened as a sample.** The defects are listed in §5.

Not checked:
- whether any checker or the auditor used the open channels in §4;
- the 12 search-rule `conforms` rows (§3);
- whether the four P040 looser terms and the P018 looser merges compile (they were not in dispute);
- whether a maintainer holds any literal departure, which is not a measurement question.

## Corrections

1. "The miss, K023 (use the existing API), searched the base only; the audit marks it `incomplete`." should say:
   "The miss, K023 (use the existing API), searched for an equivalence replacing the whole declaration. The ask was a
   one-line `have` closed by `update_eq_self i₀ f`, a lemma at the base, and that derivation compiles in the
   reviewed workspace. The audit's `incomplete` (recent master not searched) names the wrong cause."
2. "It found 50 `literal`, 15 `looser`, 1 `incomplete`." should add: "An independent re-audit (review 3) agrees on
   44 of 48 `departs` rows. It labels K015 and K053 literal (P018's `required` names `simpa … using`) and K002 and
   K041 contested (they depart only if P100's family must be completed like the analogous structures')."
3. "all six "merge consecutive steps" (P018) departures use a combining form the check does not list (`simpa ...
   using`, `rintro`, a rewrite replacing `simp` or `aesop`)" should say: "four of the six P018 departures use a form
   the rule does not name (`rintro`, a rewrite replacing `simp`, `aesop` or an `exact` term). Two (K015, K053) use
   `simpa … using`, which the rule's `required` text names. Between the readings, P040's four reads-no-worse rows
   carry 8 cells and alone cross 30%; P018's carry 5."
4. The strict row "**22%** (14 of 64) | mixed" should read "**22%** (14 of 64; per place 8 of 37, 95% 11-37%; 23%
   with K015 and K053 literal) | mixed, with an interval that reaches 30%". Add after the table: "Without the four
   literal departures whose candidate is longer than the code (K001, K004, K062, K065), the line is 11%. The line can
   fall in any of its three regions depending on how the rules are read."
5. "In the other direction, under the strict reading 7 reader `departs` labels meet a check `conforms`" should say
   "… 7 (4 once K015 and K053 count as literal) …".
6. The written row's verdict, "readers were largely not checking", should be qualified: "the reader label asks
   whether a maintainer would ask, not whether the literal check passes. By the reader notes, 9 of the 14 strict
   cells are readers predicting the check wrongly. The other 5 are a different reading of P100 (3), or a judgement
   that a term reads no better (2)."
7. "Either way it stays near 5%, not the 10% step 2 estimated." should say: "Under the checkers' verdicts it is near
   5% (95% 3.4-7.2%). Under the strict reading it is 6.2-8.2%, and the interval with 8 asks (6.3-11.9%) includes step
   2's 10%."
8. In the merge table, after "open, departs by the literal check | 27 | **20** | 5 | 2 | 0", add: "Five of the seven
   changed or gone sit in a declaration an ask on another rule rewrote (K001, K012, K013, K062, K065). At K012,
   K013 and K024 the departure is still there at merge. So 23 of 27 persist, and none changed toward its own rule."
9. "three quarters of those breaks reach merge unchanged" should say "23 of 27 of those breaks are still there at
   merge (20 byte-for-byte)".
10. "the 20 literal departures that merged unchanged are the sample on which it can be tested" should say: "the
    literal departures that persist at merge are the sample: 18 distinct omissions among the 20 unchanged, plus
    K012, K013 and K024, which survived in declarations the maintainer asked about. 11 of the 20 sit on two PRs, and
    K002/K041 rest on a contested reading."
11. "Limits: 59 open places on 14 PRs" should say "59 open places on 11 PRs (three PRs carry only asked places)".
    The same sentence's "searches at the base, not recent master (K023)" should say "P011 searched at the
    declaration's grain, not the step's (K023)".
