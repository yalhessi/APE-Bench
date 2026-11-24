# Which APE tools could run outside an APE session?

24 November 2026 · upstream `20017343` · Mathlib review fork `e9a048c3`

**The first public APE-Harness release let the benchmark change agents and keep the same Lean services. Running individual tools independently was possible, but some needed an adapter to supply what an APE task normally provided.** The April and May 2025 versions of the paper describe the earlier file-level benchmark and Eleanstic verifier. The February 2, 2026 revision describes the three-scaffold framework. The authors’ public `main` has one root commit dated February 3, which is also the root of this fork. That is the earliest implementation of the three adapters we could verify. [April paper][v1] · [May revision][v2] · [Scaffold design][design] · [Upstream commit][commit]

### Who supplies the workspace?

In a benchmark run, APE prepared the workspace and registered its tools. APE-Agent called them in process. The managed Claude Code and Codex batch adapters connected through MCP over HTTP. Each agent could then present the capability differently. In the authors’ proof-engineering experiments, an APE-Agent file edit could compile the change immediately. Claude Code and Codex issued a separate verification call. Even within one vendor, launch modes differed. The Codex batch adapter pointed its bridge at the generated MCP configuration. The interactive launcher started Codex with its usual configuration directory and did not explicitly select that file. [Reported comparison][comparison] · [APE-Agent][ape] · [Claude SDK][claude] · [Codex configuration][toml] · [Batch environment][env] · [Interactive launch][interactive] · [MCP registration][registration]

The authors’ standalone **declaration search** shows exactly where the inconvenience arose. An HTTP client could call `POST /lean-retrieve`. The endpoint and the MCP tool both called `lean_retrieve_impl`. A caller starting the server could specify the repository and commit, but behind that interface the factory constructed a `MockTask` and a scaffold configuration named `lean_retrieve_test`. The client escaped the APE task lifecycle because someone had already written that adapter. [HTTP service][http] · [MCP retrieval][retrieve] · [Provider factory][factory]

The original **Lean verification engine** had a simpler Python interface. We exported the upstream source and called `VerificationEngine().verify(code, working_dir=project)` on a temporary Lean 4.24.0 project. With no task or agent running, `example : 2 + 2 = 4 := rfl` passed and changing the right-hand side to `5` produced a type mismatch. The model-facing `lean_verify` provider added workspace rules and read tool settings from the scaffold configuration before it called that engine. [Verification engine][verification] · [Tool provider][provider]

**Submitting a result** has a genuine dependency on a running task. In the upstream proof-engineering task, `submit_result` evaluated the code and signaled completion when the stopping condition was met. In the fork, `submit_findings` checks the review budget and records the PR result. A reusable declaration lookup can serve many callers, while a submission needs an identified recipient and rules for what counts as complete. [Original submission][submit] · [Review submission](../../src/ape/tasks/lean_tasks/formal_math/review/base.py#L699)

### What changed in the fork?

On September 25 the fork exposed its review tools to independent probes through `cli tool`. It reused the implementations by constructing a stand-in review task. On PR 30458 the probe used the PR’s source files with the base commit’s compiled dependencies. One changed file used a declaration generalized in another. Lean reported two missing `Group` instances in a file that compiled in the reviewed workspace. The September 29 fix made the probe use the same reviewed-workspace setup as the task. This is the practical reason to share the workspace resolver as well as the tool function. An external agent should be able to name the PR once and rely on that resolver for subsequent checks. [Toolbox history](../../src/mathlib_review/review/toolbox.py#L14) · [Regression case](../../tests/datasets/test_pr_review_v5_toolbox.py#L57)

[v1]: https://arxiv.org/abs/2504.19110v1
[v2]: https://arxiv.org/abs/2504.19110v2
[design]: https://arxiv.org/html/2504.19110v3#S4.SS3
[comparison]: https://arxiv.org/html/2504.19110v3#S6.SS4
[commit]: https://github.com/xinhjBrant/APE-Bench/commit/20017343657a7ce77fc67467c3dc9e443c81c075
[ape]: https://github.com/xinhjBrant/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/src/ape/scaffolds/ape_agent/scaffold.py#L87-L104
[claude]: https://github.com/xinhjBrant/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/src/ape/scaffolds/claude_code/scaffold.py#L70-L150
[toml]: https://github.com/xinhjBrant/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/src/ape/scaffolds/codex/scaffold.py#L63-L147
[env]: https://github.com/xinhjBrant/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/src/ape/scaffolds/codex/conversation.py#L104-L146
[interactive]: https://github.com/xinhjBrant/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/src/ape/scaffolds/codex/scaffold.py#L215-L255
[registration]: https://github.com/xinhjBrant/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/src/ape/toolkits/mcp_manager.py#L292-L305
[verification]: https://github.com/xinhjBrant/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/src/ape/toolkits/execute/lean/core/verification.py#L152-L188
[http]: https://github.com/xinhjBrant/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/src/ape/toolkits/retrieve/lean/server.py#L103-L175
[retrieve]: https://github.com/xinhjBrant/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/src/ape/toolkits/retrieve/lean/tools.py#L317-L327
[factory]: https://github.com/xinhjBrant/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/src/ape/toolkits/retrieve/lean/utils.py#L421-L445
[submit]: https://github.com/xinhjBrant/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/src/ape/tasks/lean_tasks/formal_math/proof_engineering/task.py#L389-L407
[provider]: https://github.com/xinhjBrant/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/src/ape/toolkits/execute/lean/tools.py#L50-L62
