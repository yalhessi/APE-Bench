"""Replay three known development cases on the reviewed files, without a reviewer or matcher.

From the repository root, run PYTHONPATH=. ape/bin/python <this file> 42184
(or 33066 or 30641). Set ELAN_HOME to the installation containing the snapshot's toolchain.
Each variant is a temporary copy. The paired check only passes on the expected Lean diagnostic.
"""

import argparse
import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from src.mathlib_review.evidence.operators.canonical_api import lean_check_command
from src.mathlib_review.workspace import tool_env


WORKSPACES = Path("data/code_execute/repos/mathlib4/workspaces").resolve()
PROBES = Path(__file__).resolve().parent.parent
CASES = {
    42184: ("5b3f719bf129e3cf48daf6ff76a2ec5cb6e9b1e3+0f03738044bd",
            "Mathlib/Topology/Algebra/InfiniteSum/Order.lean"),
    33066: ("d9996c5f3e91cac9f069958181c2e86e47b8863f+924f0b317442",
            "Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean"),
    30641: ("a77a0aeac5e8e691c32a65b878b02574930b5f90+304744da43f2",
            "Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean"),
}


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Expected one match for {old!r} in the reviewed source")
    return source.replace(old, new)


def variants(number, source):
    if number == 42184:
        old_proof = "ge_of_tendsto' h.hasProd fun s ↦ s.prod_nonneg fun i _ ↦ hf i"
        client = replace_once(source, old_proof, "h.hasProd.nonneg hf")
        signature = "theorem tprod_nonneg [CommMonoidWithZero α]"
        companion = """lemma HasProd.nonneg [CommMonoidWithZero α] [TopologicalSpace α] [Preorder α] [ZeroLEOneClass α]
    [PosMulMono α] [ClosedIciTopology α] [L.NeBot] {f : ι → α} {a : α}
    (hf : ∀ i, 0 ≤ f i) (ha : HasProd f a L) : 0 ≤ a :=
  le_hasProd_of_le_prod ha fun _ ↦ prod_nonneg fun i _ ↦ hf i

"""
        yield "direct call on the submitted API", client, "Invalid field `nonneg`"
        yield "same call with the companion lemma", replace_once(client, signature, companion + signature), None
    elif number == 33066:
        client = replace_once(source, "ContinuousAlgEquiv.ofAlgEquiv f.toAlgEquiv hf",
                              "ContinuousAlgEquiv.mk f.toAlgEquiv hf")
        client = replace_once(client, "ContinuousAlgEquiv.coe_ofAlgEquiv f.toAlgEquiv hf _ ▸ hy", "hy")
        rewrite = "rw [ContinuousAlgEquiv.ext_iff] at hy"
        yield "actual client using the existing constructor", replace_once(
            client, rewrite, rewrite + "\n  change ⇑f.toAlgEquiv = _ at hy"), None
    else:
        edit = json.loads((PROBES / "model-gap-val-small12/pr30641/TA1/tmp/gcongr_lemma.json").read_text())
        lines = source.splitlines(keepends=True)
        start, end = edit["line_start"] - 1, edit["line_end"]
        if "lemma posLog_norm_sum_le " not in "".join(lines[start:end]):
            raise ValueError("Saved edit does not address the reviewed proof")
        registered = edit["replacement"]
        plain = replace_once(registered, "@[gcongr]\n", "")
        explicit = replace_once(plain, "by gcongr; exact norm_sum_le s f",
                                "posLog_le_posLog (norm_nonneg _) (norm_sum_le s f)")
        for label, replacement, expected in [
            ("unregistered lemma, tactic call", plain, "gcongr did not make progress"),
            ("registered lemma, same tactic call", registered, None),
            ("unregistered lemma, explicit call", explicit, None),
        ]:
            yield label, "".join([*lines[:start], replacement + "\n", *lines[end:]]), expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pr", type=int, choices=CASES)
    number = parser.parse_args().pr
    snapshot, filename = CASES[number]
    workspace = WORKSPACES / snapshot
    with TemporaryDirectory() as temporary:
        path = Path(temporary) / "Replay.lean"
        for label, source, expected_error in variants(number, (workspace / filename).read_text()):
            path.write_text(source)
            check = subprocess.run(
                lean_check_command("lake", source, path), cwd=workspace, env=tool_env(workspace),
                text=True, capture_output=True, timeout=600,
            )
            diagnostics = check.stdout + check.stderr
            errors = [line for line in diagnostics.splitlines() if ": error" in line.lower()]
            if expected_error is None:
                ok = check.returncode == 0
            else:
                ok = check.returncode == 1 and errors and all(expected_error in line for line in errors)
            print(f"{number} | {label} | Lean exit {check.returncode}", flush=True)
            if not ok:
                raise SystemExit(diagnostics or "Unexpected Lean exit status")
            if errors:
                print(errors[0], flush=True)


if __name__ == "__main__":
    main()
