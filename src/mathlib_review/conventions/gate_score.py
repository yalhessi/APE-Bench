"""Score the review-join precision gate from independent rater panels.

Each rater file is a JSON list of per-comment ratings (`comment_id`, `about_declaration`,
`requests_form_change`, `category`, `key_fits`, `form_A`, `form_B`, `confidence`). Panels are
`panelA_*` (even-handed) and `panelB_*` (refute-framed). Per comment, each panel's verdict on a
field is its majority; ties go to the *less* affirmative value.

  strict   := both panels: about=yes  ∧  request=yes  ∧  key_fits=yes
  lenient  := either panel: about∈{yes,partial} ∧ request=yes ∧ key_fits∈{yes,partial}

Reported per stratum and overall, with inter-rater agreement (share of raters matching the
panel majority) so a low number can be told from a noisy one.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

_ORDER = {  # less affirmative first, for tie-breaking
    "about_declaration": ["no", "partial", "yes"],
    "requests_form_change": ["no", "yes"],
    "key_fits": ["n/a", "no", "partial", "yes"],
}


def _majority(values: List[str], field: str) -> str:
    counts = collections.Counter(v for v in values if v is not None)
    if not counts:
        return _ORDER[field][0]
    top = max(counts.values())
    tied = [v for v, n in counts.items() if n == top]
    return min(tied, key=lambda v: _ORDER[field].index(v) if v in _ORDER[field] else -1)


def load_panels(directory: Path) -> Dict[str, List[Dict[str, Dict[str, Any]]]]:
    panels: Dict[str, List[Dict[str, Dict[str, Any]]]] = {"A": [], "B": []}
    for path in sorted(directory.glob("panel*_rater*.json")):
        panel = "A" if path.name.startswith("panelA") else "B"
        rows = json.loads(path.read_text(encoding="utf-8"))
        panels[panel].append({str(r["comment_id"]): r for r in rows})
    return panels


def score(sample: List[Dict[str, Any]], panels: Dict[str, List[Dict[str, Dict[str, Any]]]]) -> Dict[str, Any]:
    per_comment = []
    for item in sample:
        cid = str(item["comment_id"])
        verdict: Dict[str, Any] = {"comment_id": cid, "stratum": item["stratum"]}
        agree_hits = agree_total = 0
        for panel, raters in panels.items():
            for field in _ORDER:
                values = [r[cid].get(field) for r in raters if cid in r]
                maj = _majority(values, field)
                verdict[f"{panel}.{field}"] = maj
                agree_hits += sum(1 for v in values if v == maj)
                agree_total += len(values)
            cats = [r[cid].get("category") for r in raters if cid in r]
            verdict[f"{panel}.category"] = collections.Counter(c for c in cats if c).most_common(1)[0][0] if any(cats) else None
            forms_b = [r[cid].get("form_B") for r in raters if cid in r and r[cid].get("form_B")]
            verdict[f"{panel}.form_B"] = forms_b[0] if forms_b else ""
        verdict["agreement"] = round(agree_hits / max(1, agree_total), 3)
        a_ok = (verdict["A.about_declaration"] == "yes" and verdict["A.requests_form_change"] == "yes"
                and verdict["A.key_fits"] == "yes")
        b_ok = (verdict["B.about_declaration"] == "yes" and verdict["B.requests_form_change"] == "yes"
                and verdict["B.key_fits"] == "yes")
        verdict["strict"] = a_ok and b_ok

        def lenient(panel: str) -> bool:
            return (verdict[f"{panel}.about_declaration"] in ("yes", "partial")
                    and verdict[f"{panel}.requests_form_change"] == "yes"
                    and verdict[f"{panel}.key_fits"] in ("yes", "partial"))
        verdict["lenient"] = lenient("A") or lenient("B")
        per_comment.append(verdict)

    def summarise(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        n = len(rows)
        return {
            "n": n,
            "strict": sum(r["strict"] for r in rows),
            "lenient": sum(r["lenient"] for r in rows),
            "about_yes_A": sum(r["A.about_declaration"] == "yes" for r in rows),
            "about_yes_B": sum(r["B.about_declaration"] == "yes" for r in rows),
            "request_yes_A": sum(r["A.requests_form_change"] == "yes" for r in rows),
            "request_yes_B": sum(r["B.requests_form_change"] == "yes" for r in rows),
            "keyfits_yes_A": sum(r["A.key_fits"] == "yes" for r in rows),
            "keyfits_yes_B": sum(r["B.key_fits"] == "yes" for r in rows),
            "agreement": round(sum(r["agreement"] for r in rows) / max(1, n), 3),
        }

    by_stratum = collections.defaultdict(list)
    for row in per_comment:
        by_stratum[row["stratum"]].append(row)
    categories_A = collections.Counter(r["A.category"] for r in per_comment
                                       if r["A.requests_form_change"] == "yes")
    return {
        "raters": {p: len(rs) for p, rs in panels.items()},
        "overall": summarise(per_comment),
        "by_stratum": {k: summarise(v) for k, v in sorted(by_stratum.items())},
        "request_categories_panelA": dict(categories_A.most_common()),
        "per_comment": per_comment,
    }


def main() -> None:
    sample_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "data/pr_review_v5/review_join/precision_sample_aug2025_v2.json")
    ratings_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
        "data/pr_review_v5/review_join/ratings_aug2025_v2")
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    panels = load_panels(ratings_dir)
    result = score(sample, panels)
    (ratings_dir / "gate_result.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n",
                                                  encoding="utf-8")
    o = result["overall"]
    print(f"raters: {result['raters']} | n={o['n']}  strict={o['strict']} ({100*o['strict']/max(1,o['n']):.0f}%)"
          f"  lenient={o['lenient']} ({100*o['lenient']/max(1,o['n']):.0f}%)  agreement={o['agreement']}")
    print(f"{'stratum':32s} {'n':>3} {'strict':>6} {'lenient':>7} {'aboutA/B':>9} {'reqA/B':>7} {'fitA/B':>7} {'agree':>6}")
    for k, v in result["by_stratum"].items():
        print(f"{k:32s} {v['n']:3d} {v['strict']:6d} {v['lenient']:7d} "
              f"{v['about_yes_A']:4d}/{v['about_yes_B']:<4d} {v['request_yes_A']:3d}/{v['request_yes_B']:<3d} "
              f"{v['keyfits_yes_A']:3d}/{v['keyfits_yes_B']:<3d} {v['agreement']:6.2f}")
    print("request categories (panel A majority):", result["request_categories_panelA"])


if __name__ == "__main__":
    main()
