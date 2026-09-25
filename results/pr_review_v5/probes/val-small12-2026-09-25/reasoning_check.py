"""The free check before any reasoning run: does `reasoning_effort` reach gpt_5.2 through the
project's own client, does the provider report reasoning tokens, and what does one call cost?
Writes reasoning_check.json beside itself. Exit 2 if the key is rejected (the launch aborts)."""
import asyncio, json, sys, time
from pathlib import Path
from ape.llm_clients.client import LLMClient
from ape.llm_clients.config import LLMConfig
from ape.llm_clients.models import ContentBlock, ConversationSession

PROMPT = ("You are reviewing Lean 4 code for Mathlib. A lemma `foo_eq_bar (n : ℕ) (h : 0 < n) : foo n = bar n`"
          " is proved by `by cases n <;> simp_all`. In three sentences, would a Mathlib maintainer ask for a"
          " change, and what evidence would settle it?")

async def one(effort):
    cfg = LLMConfig(model_name="gpt_5.2", reasoning_effort=effort, streaming=False)
    client = LLMClient(cfg, enable_raw_logging=False)
    s = ConversationSession(); s.add_user_message([ContentBlock(type="text", text=PROMPT)], cwd=".")
    t = time.time()
    try:
        nodes, usage, raw = await client.call_api(s, max_tokens=1200)
    except Exception as exc:  # noqa: BLE001
        return {"effort": effort, "error": f"{type(exc).__name__}: {str(exc)[:300]}"}
    finally:
        await client.close()
    return {"effort": effort, "seconds": round(time.time() - t, 1), "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens, "reasoning_tokens": usage.reasoning_tokens,
            "cost": round(usage.cached_total_cost or usage.total_cost, 5)}

async def main():
    out = {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "calls": []}
    for effort in (None, "low", "medium"):
        r = await one(effort); out["calls"].append(r); print(json.dumps(r))
        if effort is None and "error" in r and ("401" in r["error"] or "auth" in r["error"].lower()):
            out["verdict"] = "key rejected"; break
    ok = [c for c in out["calls"] if "error" not in c]
    base = next((c for c in ok if c["effort"] is None), None)
    on = [c for c in ok if c["effort"] and (c.get("reasoning_tokens") or 0) > 0]
    out["accepted_efforts"] = [c["effort"] for c in ok if c["effort"]]
    out["chosen_effort"] = on[0]["effort"] if on else (out["accepted_efforts"][0] if out["accepted_efforts"] else None)
    if base and on:
        out["cost_ratio_on_over_off"] = round(on[0]["cost"] / base["cost"], 2) if base["cost"] else None
        out["verdict"] = "reasoning reaches the model and is reported"
    elif base and out["accepted_efforts"]:
        out["verdict"] = "effort accepted but no reasoning tokens reported"
    elif not base:
        out.setdefault("verdict", "the default call failed")
    Path(__file__).with_name("reasoning_check.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "calls"}))
    sys.exit(2 if out.get("verdict") in ("key rejected", "the default call failed") else 0)

asyncio.run(main())
