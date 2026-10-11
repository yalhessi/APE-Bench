import json
exec(open("/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33321/TA1/tmp/be2.py").read().split("e1 =")[0])
vs = ["span_mono <| range_subset_iff.mpr fun _ ↦ mem_range_self _"]
spec = [(v, {"path":F,"declaration_name":"RootPairing.linearIndepOn_root_baseOf","new_declaration":base.replace("span_mono fun x i ↦ by aesop", v)}) for v in vs]
json.dump(spec, open("/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33321/TA1/tmp/be4.json","w"))
