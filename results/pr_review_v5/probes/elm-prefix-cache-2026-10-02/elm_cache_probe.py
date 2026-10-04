"""Does ELM's vLLM reuse a prompt prefix? Same long prompt twice, then extended by a turn; max_tokens=1
so latency is prefill plus queueing. A fresh random prefix each trial so no earlier run warms it."""
import os, random, time, json, urllib.request
URL = "https://elm.edina.ac.uk/api/v1/chat/completions"
KEY = os.environ["ELM_API_KEY"]
words = [w.strip() for w in open("/usr/share/dict/words") if w.strip().isalpha()][:50000] if os.path.exists("/usr/share/dict/words") else [f"tok{i}" for i in range(5000)]
def call(messages):
    body = json.dumps({"model": "Qwen/Qwen3.5-397B-A17B-FP8", "messages": messages, "max_tokens": 1,
                       "temperature": 0, "reasoning_effort": "none", "stream": False}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    t = time.time(); r = json.load(urllib.request.urlopen(req, timeout=600)); dt = time.time() - t
    return dt, r["usage"]["prompt_tokens"], r["usage"].get("prompt_tokens_details")
for trial in range(3):
    rng = random.Random(time.time_ns())
    doc = " ".join(rng.choice(words) for _ in range(30000))
    base = [{"role": "system", "content": "You read documents."}, {"role": "user", "content": doc + "\n\nReply with one word."}]
    ext = base + [{"role": "assistant", "content": "Okay."}, {"role": "user", "content": "Now say one more word."}]
    for label, msgs in [("cold", base), ("same", base), ("extended", ext)]:
        dt, p, det = call(msgs)
        print(f"trial {trial}  {label:9s} prompt_tokens={p:6d}  latency={dt:6.2f}s  details={det}", flush=True)
