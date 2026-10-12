#!/bin/bash
# Print the transcript context for every sampled row into recode_ctx.txt (read in chunks; re-coded by hand in recode.jsonl).
cd "$(dirname "$0")"
PY=../../../../../ape/bin/python
export PYTHONPATH=$PWD
{
$PY ctx.py D12 33145 d0029 DX3 --around 1 --cut 1100 --grep "orient"
$PY ctx.py P14_post 42814 p0005 DX2 --around 1 --cut 1100 --grep "UFD|squarefree_iff_irreducible"
$PY ctx.py P14_val 32875 v0094 DX3 --around 1 --cut 1100 --grep "rw \[this\]|simp only \[this\]"
$PY ctx.py P14_val 32875 v0095 AP1 --around 1 --cut 1100 --grep "Marginal|simpa only \[this\]"
$PY ctx.py P14_val 29842 v0053 DX2 --around 1 --cut 1100 --grep "description"
$PY ctx.py D12 33145 d0027 DX2 --around 1 --cut 1100 --grep "continuous_inf'|subject_unresolved"
$PY ctx.py D12 33294 d0038 AP2 --around 1 --cut 1100 --grep "IsFundamentalSequence\.|of_isNormal"
$PY ctx.py P14_val 34091 v0107 DX1 --around 1 --cut 1100 --grep "\[Uncountable"
$PY ctx.py P14_val 34091 v0108 DX3 --around 1 --cut 1100 --grep "\[Infinite"
$PY ctx.py P14_val 34091 v0105 DX1 --around 1 --cut 1100 --grep "exists_infinite_fiber"
$PY ctx.py P14_post 42184 p0003 DX2 --around 1 --cut 1100 --grep "HasProd"
$PY ctx.py P14_val 30641 v0067 DX3 --around 1 --cut 1100 --grep "positivity|sum_nonneg"
$PY ctx.py P14_post 43192 p0015 AP2 --around 1 --cut 1100 --grep "mkHom|cat_disch"
$PY ctx.py P14_post 43192 p0014 DX1 --around 1 --cut 1100 --grep "cat_disch|map_id|map_comp"
$PY ctx.py P14_val 30641 v0064 AP3 --around 1 --cut 1100 --grep "a : ℝ|x : ℝ"
$PY ctx.py P14_val 30641 v0067 DX2 --around 1 --cut 1100 --grep "positivity|sum_nonneg"
$PY ctx.py P14_val 30641 v0067 DX1 --around 1 --cut 1100 --grep "positivity|sum_nonneg"
$PY ctx.py P14_post 42814 p0007 DX1 --around 1 --cut 1100 --grep "variable|D : ℤ"
$PY ctx.py P14_val 28649 v0031 AP1 --around 1 --cut 1100 --grep "variances|Popoviciu"
$PY ctx.py D12 33066 d0002 DX1 --around 1 --cut 1100 --grep "ofAlgEquiv|toContinuousAlgEquiv"
$PY ctx.py D12 33337 d0045 AP1 --around 1 --cut 1100 --grep "should be a prefix|toLinearMap_"
$PY ctx.py D12 33337 d0045 DX3 --around 1 --cut 1100 --grep "48 of 124|plurality"
$PY ctx.py D12 33337 d0045 DX1 --around 1 --cut 1100 --grep "Candidate B|toLinearMap_ 21"
$PY ctx.py D12 33285 d0035 AP2 --around 1 --cut 1100 --grep "add_mem h.1 h.2|mem_comap"
$PY ctx.py P14_val 30641 v0065 AP1 --around 1 --cut 1100 --grep "h₂a"
$PY ctx.py D12 33145 d0027 AP2 --around 1 --cut 1100 --grep "continuous_inf'|continuous_sup'"
$PY ctx.py D12 33421 d0049 AP2 --around 1 --cut 1100 --grep "Tendsto \(2|P165|should exist|general lemma"
$PY ctx.py D12 33117 d0018 AP1 --around 1 --cut 1100 --grep "fun_add|to_fun"
$PY ctx.py P14_val 32875 v0091 AP1 --around 1 --cut 1100 --grep "den_inv|grind ="
$PY ctx.py D12 33421 d0051 AP1 --around 1 --cut 1100 --grep "two_mul_fract|generali"
} > recode_ctx.txt 2>&1
wc -c recode_ctx.txt; wc -l recode_ctx.txt
