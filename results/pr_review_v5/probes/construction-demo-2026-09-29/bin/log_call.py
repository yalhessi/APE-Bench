"""One compact row per tool call, written by the wrapper: what was asked and, for a compile, what
it returned. The raw output stays in the session scratchpad."""
import json, sys
log, stamp, tool, args, out, status = sys.argv[1:7]
row = {"stamp": stamp, "tool": tool, "exit": int(status)}
try:
    row["arguments"] = json.loads(args) if args else None
except ValueError:
    row["arguments"] = args
try:
    result = json.loads(open(out).read())
except (ValueError, OSError):
    result = None
if tool == "lean_verify_edit" and isinstance(result, dict):
    row["result"] = {k: result.get(k) for k in ("mode", "success", "compiles") if k in result}
    row["result"]["errors_introduced"] = len(result.get("errors_introduced_by_your_edit") or [])
    row["result"]["errors_already"] = len(result.get("errors_already_in_the_file") or [])
    row["result"]["environment_reviewed"] = str(result.get("environment", "")).startswith("Verified against the reviewed")
elif result is not None:
    row["result_chars"] = len(json.dumps(result, ensure_ascii=False))
with open(log, "a") as fh:
    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
