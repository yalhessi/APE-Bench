# APE-Bench glossary

## Automated proof engineering

**Automated Proof Engineering (APE)** — Modifying a formal mathematics library to meet a written objective in a specified repository revision and proof-assistant toolchain. A change can involve definitions, theorem statements, proofs, or automation.

**APE-Bench** — The benchmark construction pipeline mines library commits for proof-engineering tasks. **APE-Bench I** is the resulting Mathlib benchmark released with the paper. The Mathlib PR review task developed in this fork asks an agent to *review* a proposed change.

**Instruction synthesis** — Turning a historical change into a request an agent can work from. The **reference implementation** is the historical solution. A different implementation can satisfy the same request.

**Dual verification** — Checking both that the submitted Lean code compiles and that it fulfills the instruction. The paper’s semantic judgment asks three questions: does the mathematics express the intended claim (**semantic correctness**), did the change deliver everything requested (**requirement alignment**), and did it stay within the requested bounds (**scope control**)?

For example, if the instruction asks for a lemma and its registration with a tactic, proving the lemma alone can pass compilation while leaving the automation requirement unmet. [Paper, §§3–5](https://arxiv.org/html/2504.19110v3)

## APE-Harness

**APE-Harness** — The framework that sets up tasks, runs agents against them, and evaluates their submissions. The starter code uses it for theorem proving, proof engineering, and judgment, and also for generating benchmark instructions and annotating library declarations for retrieval.

**Task contract** — The agreement that determines what the agent receives, which resources and actions it may use, what it must submit, and how that submission will be evaluated. A **task instance** supplies the concrete inputs for one case, such as an instruction, a target file, and a repository revision.

**Scaffold** — The agent implementation that drives the model’s interaction with a task. **APE-Agent** is the reference scaffold. Claude Code and Codex are alternative scaffolds that can execute the same contract.

**Workspace** — A task’s view of files with specified access permissions. A **target workspace** supplies the pinned project, a **reference workspace** supplies additional material when the task provides it, and a **scratch workspace** gives the agent a place to work on its solution.

**Toolkit** — A group of operations available to the agent. The Lean **execute service** checks code against the selected environment. **Version-scoped retrieval** searches declarations available in the selected library revision.

**Runtime** — The execution environment in which a task runs, such as a local process or a container. The same scaffold can be run in different environments.

**Sample and attempt** — A sample is one requested execution of a task instance. An attempt is one try at completing that sample, with its own workspace. Retrying a failed attempt does not add another sample.

**Submission and evaluation** — A submission is the answer the agent hands to the task. Evaluation applies the contract’s checks to that answer. In the original proof-engineering task, the submission contains Lean code and a judgment task can assess its semantic quality. In the review task below, the agent submits feedback on someone else’s code.

Sources for the inherited vocabulary: [paper, §4](https://arxiv.org/html/2504.19110v3), [starter README’s paper-to-code map](https://github.com/yalhessi/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/README.md#paper-to-code-mapping), [workspace model](https://github.com/yalhessi/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/src/ape/tasks/models.py), and [sample and attempt records](https://github.com/yalhessi/APE-Bench/blob/20017343657a7ce77fc67467c3dc9e443c81c075/src/ape/orchestration/models.py).

## Mathlib PR review in this fork

**Reviewed head**
The revision of the author's contribution that the reviewer is asked to assess. Later changes made in response to feedback belong to the history of the PR.

**First review round**
The exchange that begins with the first maintainer review. For the first-round task, the feedback window runs from that first event to the author's next push.

**Solo review**
One reviewer assesses the whole PR in a single session with the review brief and the permitted tools. In an ordinary solo review, the reviewer chooses what to investigate from the PR and the sources it can inspect.

**Submitted review**
The feedback a reviewer hands in about a particular revision on a particular occasion. It can include a whole-review message, ordered comments, a verdict and suggested edits. A reviewer can complete a review with zero comments.

**Reference feedback**
The feedback selected for comparison with a submitted review. In a historical first review round, it can include comments and replies from several maintainers.

**Raw ask**
A first-round request expressed in the maintainer's own words. One request can ask the author to address several things.

**Gold obligation**
An individual point derived from historical review feedback that the benchmark uses to assess whether a reviewer identified the same issue.

**Review finding**
A point raised by the reviewer being evaluated about the contribution under review. A finding can address a concern the historical maintainer never mentioned.

Sources: [first-round task specification](docs/research/review-task-spec.md) and [raw-ask matcher](src/mathlib_review/judge/ask_matching.py).
