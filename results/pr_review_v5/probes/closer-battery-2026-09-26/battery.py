"""Closer battery on the missed asks: each variant is the reviewed file with ONE textual edit,
compiled with `lake env lean` from the reviewed workspace. Result: exit code, wall time, messages."""
import json, subprocess, time, os, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
REPO = Path("/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/pipeline-overfit-review")
W = REPO / "data/code_execute/repos/mathlib4/workspaces"
OUT = Path(__file__).parent
ENV = dict(os.environ, PATH="/research/projects/proofedit/ya475/.elan/bin:" + os.environ["PATH"])
def ws(prefix): return next(W.glob(prefix))
POS = ("a77a0aeac5e8*+304744da43f2", "Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean")
PI = ("26fffffcccd7*+102dba721ebc", "Mathlib/MeasureTheory/Constructions/Pi.lean")
PW = ("586e9c386274*+499cdbb44262", "Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean")
NC = ("241db1e2c678*+c5e601604585", "Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean")
PH = ("7ee74e7d3f87*+f4a3c7b0726b", "Mathlib/SetTheory/Cardinal/Pigeonhole.lean")
DJ = ("4b627f034993*+6d111510fcad", "Mathlib/Order/Interval/Set/Disjoint.lean")
SIMP_LINE = "    simp [Finset.sum_nonneg (fun i _ ↦ norm_nonneg (f i))]\n"
STEP = ("  _ ≤ log⁺ (∑ t ∈ s, ‖f t‖) := by\n    apply monotoneOn_posLog (by simp) _ (norm_sum_le s f)\n" + SIMP_LINE)
PI_OLD = "  simp only [pi_pi, this]\n  exact Fintype.prod_equiv _ _ _ (congrFun rfl)\n"
LEFT_NEW = ("@[to_additive] lemma card_le_card_div_left (hs : s.Nonempty) : #t ≤ #(s / t) := by\n"
            "  obtain ⟨a, ha⟩ := hs\n  exact card_le_card_image₂_left _ ha (div_right_injective (b := a))\n")
LEFT_OLD = ("@[to_additive] lemma card_le_card_div_left (hs : s.Nonempty) : #t ≤ #(s / t) :=\n"
            "  have ⟨_, ha⟩ := hs; card_le_card_image₂_left _ ha div_right_injective\n")
RIGHT_NEW = ("@[to_additive] lemma card_le_card_div_right (ht : t.Nonempty) : #s ≤ #(s / t) := by\n"
             "  obtain ⟨b, hb⟩ := ht\n  exact card_le_card_image₂_right _ hb (div_left_injective (b := b))\n")
RIGHT_OLD = ("@[to_additive] lemma card_le_card_div_right (ht : t.Nonempty) : #s ≤ #(s / t) :=\n"
             "  have ⟨_, ha⟩ := ht; card_le_card_image₂_right _ ha div_left_injective\n")
FIBER_BODY = ("  simp_rw [Cardinal.infinite_iff] at hβ ⊢\n  rcases lt_or_ge #α ℵ₀ with hα | hα\n"
              "  · exact infinite_pigeonhole_card f ℵ₀ hβ le_rfl (by rwa [isRegular_aleph0.cof_eq])\n"
              "  · obtain ⟨a, ha⟩ := infinite_pigeonhole_card_lt f h hβ\n    exact ⟨a, hα.trans ha.le⟩\n")
PRIME_BODY = ("  exists_infinite_fiber f h (by\n    rw [Cardinal.infinite_iff] at hα ⊢\n    exact hα.trans h.le)\n")
CT = ("4be5c6872db6*+89dfcf685b0e", "Mathlib/RingTheory/Ideal/Cotangent.lean")
OT = ("74bdd8deff80*+bac116010241", "Mathlib/SetTheory/Ordinal/Topology.lean")
CT_OLD = "  rw [I.cotangentEquivIdeal.symm_apply_eq]\n  ext\n  simp\n"
CASES = [
 ("v0067b_mem_Ici_positivity", POS, SIMP_LINE, "    exact Set.mem_Ici.2 (by positivity)\n"),
 ("v0067c_simp_mem_Ici_positivity", POS, SIMP_LINE, "    simp only [Set.mem_Ici]\n    positivity\n"),
 ("b12613af1b38_simp", CT, CT_OLD, "  simp\n"),
 ("b12613af1b38_simp_suggested", CT, CT_OLD, "  simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff]\n"),
 ("95eb6cac0fc0_dot_rewrite", OT, "    rw [Order.IsNormal.map_iSup h (bddAbove_of_small _)]\n", "    rw [h.map_iSup (bddAbove_of_small _)]\n"),
 ("v0067_positivity", POS, SIMP_LINE, "    positivity\n"),
 ("v0068_gcongr_a", POS, STEP, "  _ ≤ log⁺ (∑ t ∈ s, ‖f t‖) := by gcongr\n"),
 ("v0068_gcongr_b", POS, STEP, "  _ ≤ log⁺ (∑ t ∈ s, ‖f t‖) := by\n    gcongr\n    exact norm_sum_le s f\n"),
 ("v0068_gcongr_c", POS, STEP, "  _ ≤ log⁺ (∑ t ∈ s, ‖f t‖) := by\n    gcongr ?_\n    exact norm_sum_le s f\n"),
 ("v0068_exact_positivity", POS, STEP, "  _ ≤ log⁺ (∑ t ∈ s, ‖f t‖) :=\n    monotoneOn_posLog (by simp) (by positivity) (norm_sum_le s f)\n"),
 ("v0092_simpa_only", PI, PI_OLD, "  simpa only [pi_pi, this] using Fintype.prod_equiv _ _ _ (congrFun rfl)\n"),
 ("v0092_simpa", PI, PI_OLD, "  simpa [pi_pi, this] using Fintype.prod_equiv _ _ _ (congrFun rfl)\n"),
 ("v0062_v0063_old_proofs", PW, [(LEFT_NEW, LEFT_OLD), (RIGHT_NEW, RIGHT_OLD)], None),
 ("v0016_computable_coeMonoidHom", NC, "noncomputable def coeMonoidHom", "def coeMonoidHom"),
 ("v0016_computable_commMonoid", NC, "protected noncomputable def commMonoid", "protected def commMonoid"),
 ("v0016_computable_divisionMonoid", NC, "protected noncomputable def divisionMonoid", "protected def divisionMonoid"),
 ("v0016_computable_divisionCommMonoid", NC, "protected noncomputable def divisionCommMonoid", "protected def divisionCommMonoid"),
 ("v0105_exactq_fiber", PH, FIBER_BODY, "  exact?\n"),
 ("v0105_exactq_after_simp", PH, FIBER_BODY, "  simp_rw [Cardinal.infinite_iff] at hβ ⊢\n  exact?\n"),
 ("v0105_applyq_after_simp", PH, FIBER_BODY, "  simp_rw [Cardinal.infinite_iff] at hβ ⊢\n  apply?\n"),
 ("v0105_exactq_prime", PH, PRIME_BODY, "  by exact?\n"),
 ("v0131_v0132_attr_simp", DJ, [("@[to_dual Iio_disjoint_Ioi_same]", "@[to_dual (attr := simp) Iio_disjoint_Ioi_same]"),
                                 ("@[to_dual Iio_disjoint_Ioi_iff]", "@[to_dual (attr := simp) Iio_disjoint_Ioi_iff]")], None),
]
def run(case):
    name, (wsp, rel), old, new = case
    w = ws(wsp); src = (w / rel).read_text()
    edits = old if isinstance(old, list) else [(old, new)]
    text = src
    for o, n in edits:
        assert text.count(o) == 1, (name, o[:60], text.count(o))
        text = text.replace(o, n)
    d = OUT / name; d.mkdir(exist_ok=True); f = d / "Variant.lean"; f.write_text(text)
    t = time.time()
    p = subprocess.run(["lake", "env", "lean", str(f)], cwd=w, env=ENV, capture_output=True, text=True, timeout=1500)
    if "`module` keyword is experimental" in p.stdout + p.stderr:
        p = subprocess.run(["lake", "env", "lean", "-Dexperimental.module=true", str(f)], cwd=w, env=ENV, capture_output=True, text=True, timeout=1500)
    r = {"case": name, "exit": p.returncode, "seconds": round(time.time() - t, 1),
         "stdout": p.stdout[-6000:], "stderr": p.stderr[-2000:]}
    (d / "result.json").write_text(json.dumps(r, indent=1, ensure_ascii=False))
    print(f"{name}: exit {p.returncode} in {r['seconds']}s", flush=True)
    return r
only = sys.argv[1:]  # optional case-name prefixes
todo = [c for c in CASES if not only or any(c[0].startswith(o) for o in only)]
with ThreadPoolExecutor(max_workers=6) as ex:
    results = list(ex.map(run, todo))
(OUT / "results.json").write_text(json.dumps(results, indent=1, ensure_ascii=False))
print("DONE", len(results))
