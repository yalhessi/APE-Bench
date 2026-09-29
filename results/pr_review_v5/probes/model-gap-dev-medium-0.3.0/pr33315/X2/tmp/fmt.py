import json, sys
d = json.load(sys.stdin)
if not d.get("success"):
    print(json.dumps(d, ensure_ascii=False)[:400])
else:
    if "content" in d:
        print(d["content"])
    for r in d.get("results", []):
        if isinstance(r, dict):
            print("--", r.get("path"))
            for m in r.get("matches", []):
                print(m["content"])
