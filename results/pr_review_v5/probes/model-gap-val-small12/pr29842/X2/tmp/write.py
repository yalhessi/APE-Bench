import json, os
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
findings = [
  {
    "target": "UniqueDiffWithinAt.mono",
    "claim": "The PR moves `UniqueDiffWithinAt.mono` into the TVS block after `variable [ContinuousAdd E] [ContinuousSMul 𝕜 E]`, so the lemma now requires both instances. It does not need either. Monotonicity in the set follows directly from `tangentConeAt_mono`, which carries no continuity assumption, together with `closure_mono`. Going through `mono_nhds` (and so `tangentConeAt_mono_nhds` and `tangentConeAt.lim_zero`) is what adds the continuity requirement.",
    "requested_change": "Move `UniqueDiffWithinAt.mono` above `variable [ContinuousAdd E] [ContinuousSMul 𝕜 E]` in the `UniqueDiff`/`TVS` section and prove it without `mono_nhds`: `theorem UniqueDiffWithinAt.mono (h : UniqueDiffWithinAt 𝕜 s x) (st : s ⊆ t) : UniqueDiffWithinAt 𝕜 t x := ⟨h.1.mono <| Submodule.span_mono <| tangentConeAt_mono st, closure_mono st h.2⟩`.",
    "severity": "advisory",
    "evidence": "Read the file as the PR leaves it (lines 433-443: the variable line, then `mono_nhds`, then `mono` proved as `h.mono_nhds <| nhdsWithin_mono _ st`). Called lean_verify_edit in line mode on lines 433-443. The edit put `UniqueDiffWithinAt.mono` with the direct proof above the `variable [ContinuousAdd E] [ContinuousSMul 𝕜 E]` line and left `mono_nhds` below it. The result was success: true, with no errors or warnings, over the whole recompiled file. That file includes `UniqueDiffWithinAt.mono_closure` and `uniqueDiffWithinAt_Ici`/`Iic`, which use `.mono`. The as-is compile check of the PR file also passed with no errors."
  }
]
with open(os.path.join(D, "findings.json"), "w") as f:
    json.dump(findings, f, ensure_ascii=False, indent=2)
