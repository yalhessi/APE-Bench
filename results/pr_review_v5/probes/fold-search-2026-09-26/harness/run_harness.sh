#!/usr/bin/env bash
# Compile every harness file against ITS chosen base workspace, 8 at a time. The search module is
# compiled once per (toolchain, module-or-plain) pair, from within a workspace on that toolchain.
set -u
S=/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/b9848b08-eb04-43a7-9e77-0f87417755b6/scratchpad/fold
H=$S/harness2
export PATH=/research/projects/proofedit/ya475/.elan/bin:$PATH
python3 - <<'PY' > "$H/jobs.txt"
import json
for x in json.load(open("/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/b9848b08-eb04-43a7-9e77-0f87417755b6/scratchpad/fold/harness2/index.json")):
    print(x["cid"], x["workspace"], x["toolchain"].replace("/", "-").replace(":", "-"), int(x["is_module"]))
PY
while read -r cid W tc ismod; do
  D=$S/fold2_${tc}_$ismod
  if [ ! -f "$D/Fold.olean" ]; then
    mkdir -p "$D"; if [ "$ismod" = "1" ]; then cp "$S/v6h4/Fold.lean" "$D/Fold.lean"; else cp "$S/v6h4/FoldPlain.lean" "$D/Fold.lean"; fi
    ( cd "$W" && lake env lean -Dexperimental.module=true --root="$D" -o "$D/Fold.olean" -i "$D/Fold.ilean" "$D/Fold.lean" > "$D/compile.out" 2>&1 \
      || lake env lean --root="$D" -o "$D/Fold.olean" -i "$D/Fold.ilean" "$D/Fold.lean" > "$D/compile.out" 2>&1 )
    echo "Fold for $tc module=$ismod: $( [ -f "$D/Fold.olean" ] && echo ok || echo FAILED ) $(grep -c ': error' "$D/compile.out") errors $(grep -m1 ': error' "$D/compile.out" | cut -c1-160 | sed 's|/tmp/claude[^ ]*fold_||')"
  fi
done < <(sort -u -k2,4 "$H/jobs.txt" | awk '!seen[$3" "$4]++')
one() { cid="$1"; W="$2"; tc="$3"; ismod="$4"; D=$S/fold2_${tc}_$ismod; s=$(date +%s)
  if [ ! -f "$D/Fold.olean" ]; then echo "$cid SKIPPED (no Fold for $tc module=$ismod)"; return; fi
  flag=""; [ "$ismod" = "1" ] && flag="-Dexperimental.module=true"
  ( cd "$W" && timeout 1500 lake env bash -c "LEAN_PATH=$D:\$LEAN_PATH lean $flag $H/$cid.lean" > "$H/$cid.out" 2>&1 ); rc=$?
  if grep -q "unknown option\|invalid -D\|unknown configuration" "$H/$cid.out"; then ( cd "$W" && timeout 1500 lake env bash -c "LEAN_PATH=$D:\$LEAN_PATH lean $H/$cid.lean" > "$H/$cid.out" 2>&1 ); rc=$?; fi
  echo "$cid rc=$rc $(( $(date +%s) - s ))s folds=$(grep -c '⇒' "$H/$cid.out") errors=$(grep -c ': error' "$H/$cid.out") first=$(grep -m1 ': error' "$H/$cid.out" | cut -c1-140 | sed 's|/tmp/claude[^ ]*harness/||')"; }
export -f one; export S H
xargs -P 8 -L 1 bash -c 'one "$@"' _ < "$H/jobs.txt" | tee "$H/run.log"
echo DONE-HARNESS
