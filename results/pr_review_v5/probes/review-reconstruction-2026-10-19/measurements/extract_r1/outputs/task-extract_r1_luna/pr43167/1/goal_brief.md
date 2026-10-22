# Goal brief

## 1. Kind of contribution
New results and an API reorganization, with an import/dependency change. The contribution adds facts about subgroup commutators and relocates and renames an existing normalizer result.

## 2. Capability
Write the commutator subgroup of subgroups A and B as C(A,B). For subgroups H, K and a normal subgroup N, provide the distributive equality C(H ∨ K,N) = C(H,N) ∨ C(K,N), together with its counterpart when the normal subgroup is in the first argument. Also provide monotonicity in either commutator argument and the fact that C(A,B) lies in L whenever both A and B lie in L. The corresponding additive-subgroup forms of these monotonicity and containment facts are included as well. Reorganize the existing result that the intersection of the normalizers of H and K lies in the normalizer of H ∨ K, giving it a more consistent canonical API placement and name.

## 3. What must keep working
The normalizer-intersection result and its additive-subgroup counterpart must remain available, including under the established spelling during the transition. Existing consequences that use it—such as conjugation preserving a subgroup join and the normalizer of one subgroup lying in the normalizer of a join under the existing hypothesis—must continue to work. The commutator equalities must cover the stated normal-subgroup case without requiring H or K to be normal; the opposite-argument equality is also part of the contribution.

## 4. Open questions
The inputs do not settle whether the distributivity equality should also be supplied for additive commutators, or whether the normalizer API reorganization should extend beyond this existing result. They do not establish whether the one-argument monotonicity and common-upper-bound facts are intended as independent public API or primarily as supporting facts.

## 5. Where the requirements come from
The left-argument distributivity equality and its normal-subgroup condition come from description paragraph 1; the current title also states this goal, but is not verified to be the title at review time. The opposite-argument equality, monotonicity facts, common-upper-bound fact, and corresponding additive forms come from additions and registrations in the change itself. The normalizer result and the consequences to preserve are evidenced by the removed/added result and the changed uses in the diff. Its API reorganization comes from description paragraph 3 and the corresponding move/rename in the change. The import maintenance requirement comes from the changed import in the diff.