"""How a design's first message divides: brief, PR header, PR model (and its code blocks), diff,
design contract -- built exactly as the task builds it, for every PR of a config. Spends nothing.

    PYTHONPATH=$PWD/src ape/bin/python results/pr_review_v5/probes/review-designs-2026-10-02/prompt_parts.py configs/designs/structured_dev_claude_sub.yaml

Also counts the PR model's relation lines that repeat another line in the opposite direction
(`a -> b` beside `b -> a` for a symmetric relation), which carry no information the first did not.
"""

import asyncio
import re
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


async def main(config: str) -> int:
    from ape.tasks.base import create_task_from_data
    from src.mathlib_review.review.runner import (
        _solo_task_data, load_release, load_run, select_units_and_episodes,
    )

    dataset, scaffold, overrides = load_run(Path(config), {"dataset": {"run_name": "prompt_parts"}})
    release = load_release(dataset)
    units, episodes = select_units_and_episodes(dataset, release)
    agenda = SimpleNamespace(proposals=[SimpleNamespace(episode_id=e.episode_id) for e in episodes])
    data = _solo_task_data(agenda, episodes, dataset, {}, Path("t.jsonl"), graphs=release["graphs"])
    keys = ("total", "brief", "header", "model", "before", "after", "relations", "mirrored", "diff", "contract")
    totals = dict.fromkeys(keys, 0)
    print("| PR | " + " | ".join(keys) + " |\n|" + "---|" * (len(keys) + 1))
    for payload in sorted(data, key=lambda p: p["pr_number"]):
        task = create_task_from_data(payload, scaffold, task_config_overrides=overrides)
        system, user = await task.create_system_prompt(), await task.create_user_prompt()
        model_at, diff_at = user.find("# The PR model"), user.find("## The diff")
        contract_at = max(user.find("## The ledger"), user.find("## The first stage's ledger"))
        contract_at = contract_at if contract_at > 0 else len(user)
        model = user[model_at:diff_at] if model_at > 0 else ""
        relations = model[model.find("## Relations between changed declarations"):] if "## Relations" in model else ""
        pairs = re.findall(r"^- (\w+) \[\w+\]: `([^`]+)` -> (.+)$", relations, re.M)
        seen, mirrored = set(), 0
        for kind, source, targets in pairs:
            for target in re.findall(r"`([^`]+)`", targets):
                if (kind, target, source) in seen:
                    mirrored += 1
                seen.add((kind, source, target))
        row = {
            "total": len(system) + len(user), "brief": len(system),
            "header": len(user[:model_at if model_at > 0 else diff_at]), "model": len(model),
            "before": sum(map(len, re.findall(r"- before the PR:\n```lean\n.*?```", model, re.S))),
            "after": sum(map(len, re.findall(r"- as the PR leaves it:\n```lean\n.*?```", model, re.S))),
            "relations": len(relations), "mirrored": mirrored,
            "diff": len(user[diff_at:contract_at]), "contract": len(user[contract_at:]),
        }
        for key in keys:
            totals[key] += row[key]
        print(f"| {payload['pr_number']} | " + " | ".join(f"{row[k]:,}" for k in keys) + " |")
    print("| all | " + " | ".join(f"{totals[k]:,}" for k in keys) + " |")
    print({k: round(totals[k] / totals["total"], 3) for k in keys if k not in ("total", "mirrored")})
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1])))
