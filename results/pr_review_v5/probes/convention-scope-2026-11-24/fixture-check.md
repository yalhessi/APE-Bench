# Checked packet inputs

The edited PR 42184 packet adds one public declaration, `HasProd.nonneg`, immediately before `tprod_nonneg`. Removing that addition reproduces the entire submitted file byte for byte, including its original proof. The submitted packet file also matches the cached reviewed workspace. Each of the three ordinary/comparison pairs has identical PR text, diff and source bytes. The only differing file within a pair is `operation.md`. [Generator and case mapping](build_packets.py)

| PR 42184 input | Complete Order.lean SHA-256 | Diff SHA-256 | Lean exit |
|---|---|---|---|
| Submitted, p37/p83 | `b20ed2427082b6ce2e1310860b73f3f6a08b9d126b99f6f075723b2b33f8ee57` | `75ebc25bc5f5ec39926f4c600e054def8c1688e54825e6a9a9f4113ecbd2e18d` | 0 |
| With companion, p19/p52 | `a3d89693ae16bd7bca4015c6e3f50358f02733f96ea227cf6d0bab27c9c1738a` | `5cb2734880e2069011d7311a0673cff26fd74b6467e6c60c4b865b621e71e0ba` | 0 |

The two invocations below take a fresh scratch copy of the actual packet files and check them in the existing reviewed workspace with Lean 4.33.0-rc1. Lake reported local changes in Batteries. Its HEAD matched the manifest and the worktree diff comprised mode changes on four shell scripts. [Submitted 42184 file](https://github.com/leanprover-community/mathlib4/blob/c5474cb4a68a515228b49225b38a2507264f91f7/Mathlib/Topology/Algebra/InfiniteSum/Order.lean)

```bash
probe=results/pr_review_v5/probes/convention-scope-2026-11-24
scratch=$(mktemp -d)
ape/bin/python "$probe/build_packets.py" "$scratch/packets"
export ELAN_HOME=/research/projects/proofedit/ya475/.elan
export PATH="$ELAN_HOME/bin:$PATH"
cd data/code_execute/repos/mathlib4/workspaces/5b3f719bf129e3cf48daf6ff76a2ec5cb6e9b1e3+0f03738044bd
lake env lean -Dexperimental.module=true "$scratch/packets/p37/Mathlib/Topology/Algebra/InfiniteSum/Order.lean"
lake env lean -Dexperimental.module=true "$scratch/packets/p19/Mathlib/Topology/Algebra/InfiniteSum/Order.lean"
```

## Natural control and source provenance

PR 29857 entered from the 390 previously exposed, request-positive development PRs. We searched **added diff lines**, then inspected the added theorem and its two clients. Both accepted-draw lists for reserved validation and evaluation exclude 29857 and 42184. The natural control belongs to the September 2025 main stratum of the development census, and 42184 to the July 2026 main stratum of the historical probe. Both draw records carry empty AI-evidence lists. Development membership establishes selection eligibility only. Its historical review outcomes were unnecessary for either selecting 29857 or checking the two calls. [Development draw](../../../../inputs/pull_requests/evaluation/val1000-2025-06-2026-03-v1/draw.json) · [Historical probe draw](../../../../inputs/pull_requests/evaluation/probe-2026-07-08-v1/draw.json) · [Reserved validation draw](../../../../inputs/pull_requests/evaluation/val-2025-06-2026-03-v1/draw.json) · [Reserved evaluation draw](../../../../inputs/pull_requests/evaluation/eval-2025-06-2026-03-v1/draw.json)

The reviewed September 21 commit gives 29857's title verbatim. Its only recorded rename on October 1 prepended the Bors merge prefix to that exact title, after the September 29 first review. The cache records a successful body-edit fetch with zero edits. The cleaned description matches the development export's `review_time_verified` text, SHA-256 `ccc68a401d0fa474e042a86b9ba4bdb8e9587d3bde88581bee88f32f85558cda`. PR 42184's July 28 submitted subject likewise matches the title before its sole August 3 Bors rename, and its body-edit fetch also recorded zero edits. The packet generator obtains each title from the submitted commit. Each reviewer receives only the title and the cleaned body. [29857 submitted commit](https://github.com/leanprover-community/mathlib4/commit/43fd03f7e657c6395612509dfa2d3372275bb9ef) · [29857 rename](https://api.github.com/repos/leanprover-community/mathlib4/issues/events/20029537158) · [29857 fetch record](../../../../data/pull_requests/pr/29857/fetch.json) · [42184 submitted commit](https://github.com/leanprover-community/mathlib4/commit/c5474cb4a68a515228b49225b38a2507264f91f7) · [42184 rename](https://api.github.com/repos/leanprover-community/mathlib4/issues/events/28914026840) · [42184 reviewed input](../../../../inputs/probes/probe-2026-07-08-v1/input/episodes.jsonl)

Applying the archived 29857 patch to its cached base reconstructs 285 lines of `Ring.lean`, SHA-256 `00f70797f66db5d86a735459b0a94c31d93346b5429ea00ef1119aae17918ecd`. The base file matches the corresponding local Git blob. Line 268 introduces the specified-limit operation. Lines 279 and 283 call it in two corollaries. This checks an observable property of the submitted source. We did not run Lean on 29857. The experiment uses 29857 and 42184 as historical development cases, and the edited 42184 file as an investigator-created fixture. Only the original two files are public PR submissions. [Reviewed file and calls](https://github.com/leanprover-community/mathlib4/blob/43fd03f7e657c6395612509dfa2d3372275bb9ef/Mathlib/Topology/Algebra/InfiniteSum/Ring.lean#L268-L283) · [Archived comparison](../../../../data/pull_requests/pr/29857/compares/43fd03f7e657c6395612509dfa2d3372275bb9ef.json)

## The generic alternative offered by the declining reviewer

After scoring, an additional check inserted the following example immediately before `tprod_nonneg` in a temporary copy of the original packet file and ran the same pinned Lean checker. It exited 0. The declined comment's proposed generic client really is possible under the PR's assumptions. This does not settle whether naming the specialization is worthwhile. [Declining reviewer](packet-reviews/p83-2.json)

```lean
example [CommMonoidWithZero α] [TopologicalSpace α] [Preorder α] [ZeroLEOneClass α]
    [PosMulMono α] [ClosedIciTopology α] [L.NeBot] {f : ι → α} {a : α}
    (hf : ∀ i, 0 ≤ f i) (ha : HasProd f a L) : 0 ≤ a :=
  le_hasProd_of_le_prod ha fun s ↦ s.prod_nonneg fun i _ ↦ hf i
```
