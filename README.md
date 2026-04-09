[English](#english-version) | [中文](#chinese-version)
<a name="english-version"></a>

# APE-Bench: Evaluating Automated Proof Engineering for Formal Math Libraries

<p align="center">
  <a href="https://arxiv.org/abs/2504.19110v3">
    <img src="https://img.shields.io/badge/APE--Bench_I-Paper-red"></a>
  <a href="https://huggingface.co/datasets/HuajianXin/APE-Bench_I">
    <img src="https://img.shields.io/badge/APE--Bench_I-Hugging Face Dataset-orange"></a>
  <a href="./LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-blue"></a>
  <a href="https://github.com/xinhjBrant/APE-Bench">
    <img src="https://img.shields.io/badge/GitHub-Repository-lightgrey"></a>
</p>

**APE-Bench** is the reference implementation for the paper "[APE-Bench: Evaluating Automated Proof Engineering for Formal Math Libraries](https://arxiv.org/abs/2504.19110v3)". This codebase implements the complete infrastructure described in the paper, including APE-Bench automated pipeline, APE-Harness task contract framework, and multi-version verification/retrieval services.

## Table of Contents
* [Paper to Code Mapping](#paper-to-code-mapping)
* [Installation](#installation)
* [Quick Start](#quick-start)
* [Usage Guide](#usage-guide)
  * [1. Building Execute Database](#1-building-execute-database)
  * [2. Building Retrieval Index](#2-building-retrieval-index)
  * [3. Running Evaluation](#3-running-evaluation)
  * [4. Constructing APE-Bench](#4-constructing-ape-bench)
* [Project Structure](#project-structure)
* [Configuration](#configuration)
* [Datasets](#datasets)
* [License](#license)
* [Citation](#citation)

## Paper to Code Mapping

### Core Concepts

| Paper Concept | Code Path |
|---------------|-----------|
| **Task Contract Abstraction** | `src/ape/tasks/base.py` (`BaseTask`, `BaseTaskData`, `BaseTaskConfig`, `BaseTaskResult`, `EvaluationResult`), `src/ape/tasks/models.py` (`WorkspaceInfo`) |
| **APE-Harness Infrastructure** | `src/ape/` (orchestration, toolkits, runtime, scaffolds) |
| **APE-Bench Pipeline** | `src/datasets/ape_bench/` |
| **Execute Services** | `src/ape/toolkits/execute/lean/` |
| **Retrieve Services** | `src/ape/toolkits/retrieve/lean/` |
| **APE-Agent Scaffold** | `src/ape/scaffolds/ape_agent/` |
| **Claude Code Scaffold** | `src/ape/scaffolds/claude_code/` |
| **Codex Scaffold** | `src/ape/scaffolds/codex/` |

### Task Types

| Paper Task Type | Code Implementation | Entry Point |
|----------------|---------------------|-------------|
| **Proof Engineering** | `src/ape/tasks/lean_tasks/formal_math/proof_engineering/` | `LeanProofEngineeringTask` |
| **Theorem Proving** | `src/ape/tasks/lean_tasks/formal_math/theorem_proving/` | `LeanTheoremProvingTask` |
| **Judgment** | `src/ape/tasks/lean_tasks/formal_math/judgment/` | `LeanJudgmentTask` |
| **Instruction Synthesis** | `src/datasets/ape_bench/task.py` | `InstructionGenerationTask` |
| **Library Annotation** | `src/ape/toolkits/retrieve/lean/semantic_annotation/task.py` | `AnnotationTask` |

### Infrastructure Services

| Paper Component | Code Path | Key Function |
|----------------|-----------|--------------|
| **Content-Addressable Storage** | `src/ape/toolkits/execute/lean/core/build_manager.py` | `BuildManager.build_workspace()` |
| **Semantic Search** | `src/ape/toolkits/retrieve/lean/` | `LeanRetrieveToolsProvider` |
| **Workspace Isolation** | `src/ape/tasks/models.py`, `src/ape/runtime/` | `WorkspaceInfo` (access control), `LocalRuntime`, `IsolatedLocalRuntime` |
| **Dual Verification** | Task evaluation in `src/ape/tasks/lean_tasks/formal_math/` | `evaluate()` methods |

## Installation

### Prerequisites

*   Python 3.10+
*   [Lean 4](https://leanprover.github.io/lean4/doc/setup.html) with [elan](https://github.com/leanprover/elan) installed
*   Git

### Setup Steps

```bash
# 1. Clone repository
git clone https://github.com/xinhjBrant/APE-Bench.git
cd APE-Bench

# 2. Install repository
pip install -e .
```

## Quick Start

### Interactive CLI

Use the unified `ape` CLI for live interactive agent sessions in a local workspace:

```bash
# APE-Agent
ape chat ape-agent --workspace .

# Claude Code-backed session
ape chat claude-code --workspace . --prompt "Inspect this Lean project"

# Codex-backed session
ape chat codex --workspace . --model gpt_5

# Load interactive scaffold settings from YAML, then override selectively
ape chat ape-agent --config configs/cli.yaml --workspace . llm_config.temperature=0.7
```

Use `ape task ...` when you want to run a registered task instead of a free-form workspace session:

```bash
# Show the registered tasks visible to the CLI
ape task ape-agent

# Run a built-in task and fill its fields interactively
ape task ape-agent lean_pr_review

# Load task-mode scaffold settings from YAML
ape task ape-agent --config configs/cli.yaml lean_pr_review

# Import a custom task module; its registered tasks become valid task names
ape task ape-agent \
  --task-module examples.arithmetic.task \
  arithmetic

# Run a specific benchmark task record
ape task ape-agent \
  --task-file inputs/proof_pr_review/mathlib_pr_review_10tasks.jsonl \
  --task-index 0 \
  lean_pr_review

# Import a custom task module and run it from inline JSON
ape task ape-agent \
  --task-module examples.arithmetic.task \
  arithmetic \
  --task-data-json '{"expression":"2 + 2","expected_result":4.0}'
```

When you run `ape chat ...` or `ape task ...`, `--config` follows the same precedence as the batch
scaffold entrypoints: explicit CLI flags and trailing `key=value` overrides win over YAML, which
wins over Pydantic defaults.

Managed agent skills are opt-in through the scaffold-level `skills` block. When `repo_discovery`
is enabled, the active workspace is checked for native repo skill directories (`.agents/skills`
for Codex, `.claude/skills` for Claude Code, and both for APE-Agent). `extra_roots` may point to
either a single skill directory or a directory that contains multiple skills.

```yaml
skills:
  enabled: true
  repo_discovery: true
  extra_roots:
    - ./skills
    - ../shared-skills/code-review
```

Relative `extra_roots` from YAML are resolved against the YAML file location. Relative trailing
CLI overrides are resolved against the current working directory:

```bash
ape chat codex --config configs/cli.yaml --workspace . 'skills.extra_roots=["./local-skills"]'
ape task claude-code --task-module examples.arithmetic.task arithmetic \
  --task-data-json '{"expression":"2 + 2","expected_result":4.0}' \
  'skills.enabled=True' \
  'skills.extra_roots=["./team-skills"]'
python -m ape.scaffolds.ape_agent.main inputs/ape_bench/ape_bench.jsonl \
  --config configs/ape_agent.yaml \
  'skills.extra_roots=["./benchmark-skills"]'
```

When you run `ape task ... <registered_task>` without `--task-file` or `--task-data-json`, the CLI
inspects that task's Pydantic schema and prompts for each input field directly in the terminal. For
nested task data such as `target_workspace`, the CLI walks the nested fields as well.

`lean_pr_review` uses a friendlier interactive flow: the CLI only asks for the GitHub `pr_url` and
the PR branch `commit`, then builds a live review snapshot automatically from GitHub. That live CLI
entrypoint always produces the shared PR review envelope with `evaluation: null`; benchmark records
use the same `snapshot` shape and attach `evaluation` plus `benchmark_context`.

The scaffold-specific aliases remain available for compatibility:

```bash
apea --workspace .
ape-claude --workspace .
ape-codex --workspace .
```

These interactive commands are separate from the existing batch evaluation entrypoints such as
`python -m ape.scaffolds.ape_agent.main ...`, which continue to work unchanged.

Creating a custom task requires three components: **TaskData** (input), **Task** (logic), and **register_task** (registration).

See `examples/arithmetic/task.py` for a complete minimal example.

### Example: Arithmetic Task

```python
from ape.tasks.base import BaseTask, BaseTaskData, BaseTaskResult, EvaluationResult, register_task

# 1. Define input data
class ArithmeticTaskData(BaseTaskData):
    expression: str
    expected_result: float

# 2. Implement task logic
class ArithmeticTask(BaseTask):
    task_type = "arithmetic"
    data_class = ArithmeticTaskData
    task_result_class = BaseTaskResult

    async def create_user_prompt(self) -> str:
        return f"Compute: {self.data.expression}"

    async def evaluate(self, submission: str) -> EvaluationResult:
        result = float(submission.strip())
        is_correct = abs(result - self.data.expected_result) < 1e-6
        return EvaluationResult(success=is_correct, score=1.0 if is_correct else 0.0)

# 3. Register task
register_task("arithmetic", ArithmeticTask)
```

**Input JSONL** (`input.jsonl`):
```json
{"task_id": "task_001", "task_type": "arithmetic", "expression": "1234 + 5678", "expected_result": 6912.0}
```

**Usage**:
```bash
python -m ape.scaffolds.ape_agent.main input.jsonl \
  --task_modules your.module.task \
  llm_config.model_name=gpt_5_mini
```

The `--task_modules` parameter imports your task module, which executes `register_task()` and makes the task type available.

## Usage Guide

### 1. Building Execute Database

**Paper Reference**: Section 4.2 "Multi-Version Execution"

The execute database provides compilation verification across multiple Mathlib4 versions using content-addressable storage.

```bash
# Build from single commit
python -m ape.toolkits.execute.lean.build \
  --target_repo "https://github.com/leanprover-community/mathlib4.git@@85eacf338f4140b402a3f970dde352b457e0dd5f"

# Build from JSONL file containing tasks
python -m ape.toolkits.execute.lean.build \
  --input_file inputs/ape_bench/ape_bench.jsonl \
  --num_processes 8

# Build from multiple datasets
python -m ape.toolkits.execute.lean.build \
  --input_file inputs/minictx_v2/*.jsonl \
  --num_processes 16
```

**Key Parameters**:
- `--target_repo`: Single repository in format `repo_url@@commit_hash`
- `--input_file`: JSONL file(s) containing tasks with `target_workspace` field
- `--num_processes`: Parallel build processes (default: CPU count)

**Output**: Compiled artifacts stored in `data/code_execute/storage/` with content deduplication.

### 2. Building Retrieval Index

**Paper Reference**: Section 4.2 "Version-Scoped Retrieval"

The retrieval index enables semantic search across library declarations at specific commits.

```bash
# Build index for single commit
python -m ape.toolkits.retrieve.lean.build \
  --target_repo "https://github.com/leanprover-community/mathlib4.git@@2df2f0150c275ad53cb3c90f7c98ec15a56a1a67@@Mathlib" \
  num_processes=32

# Build with reference workspaces
python -m ape.toolkits.retrieve.lean.build \
  --target_repo "https://github.com/fpvandoorn/carleson.git@@a5d265f109105809de4aaff16776b7c16b1c0bd5@@Carleson" \
  --reference_repo "https://github.com/leanprover-community/mathlib4.git@@79e94a093aff4a60fb1b1f92d9681e407124c2ca@@Mathlib" \
  num_processes=32

# Build from task file
python -m ape.toolkits.retrieve.lean.build \
  --input_file inputs/ape_bench/ape_bench.jsonl \
  num_processes=32
```

**Key Parameters**:
- `--target_repo`: Target repository in format `repo_url@@commit_hash@@default_target`
  - `default_target`: Directory to extract (e.g., `Mathlib`), or omit for all files
- `--reference_repo`: Reference repositories (can be specified multiple times)
- `num_processes`: Parallel annotation processes

**Output**:
- Embeddings database: `data/lean_retrieve/`
- Annotated declarations: `data/lean_retrieve/repos/{repo_name}/storage/annotated_ids.txt`

### 3. Running Evaluation

**Paper Reference**: Section 5 "Evaluation"

Execute tasks using APE-Harness with different scaffolds and configurations.

#### Basic Execution

```bash
# Run with APE-Agent scaffold
python -m ape.scaffolds.ape_agent.main \
  inputs/minictx_v2/all_test.jsonl \
  llm_config.model_name=gemini_3_flash \
  execution.sample_max_cost=3.0 \
  execution.num_processes=8 \
  runtime_config.runtime_type=isolated_local \
  --orchestrator_id ape_agent_minictx_gemini_3_flash_isolated_local

# Run with Claude Code scaffold
python -m ape.scaffolds.claude_code.main \
  inputs/ape_bench/ape_bench.jsonl \
  llm_config.model_name=claude_3_opus \
  execution.sample_max_cost=3.0 \
  --orchestrator_id claude_code_ape_bench_opus

# Run PR-review benchmark (Mathlib merge-readiness task)
python -m ape.scaffolds.ape_agent.main \
  inputs/proof_pr_review/mathlib_pr_review_benchmark.jsonl \
  llm_config.model_name=gpt_5.2 \
  execution.sample_count=1 \
  --orchestrator_id ape_agent_pr_review
```

#### Configuration via CLI

All configuration parameters can be overridden using dot-notation:

```bash
# LLM configuration
llm_config.model_name=gpt_5.2
llm_config.temperature=0.7
llm_config.max_tokens=8000

# Execution configuration
execution.sample_max_cost=3.0          # Budget per task (USD)
execution.max_turns=100                # Conversation turn limit
execution.num_processes=8              # Parallel workers
execution.sample_count=1               # Samples per task

# Runtime configuration
runtime_config.runtime_type=isolated_local   # or: local, container
```

#### Scaffold Comparison (Table 3 in paper)

```bash
# APE-Agent (integrated verification)
python -m ape.scaffolds.ape_agent.main inputs/ape_bench/ape_bench.jsonl \
  llm_config.model_name=gemini_3_flash \
  --orchestrator_id ape_agent_comparison

# Claude Code
python -m ape.scaffolds.claude_code.main inputs/ape_bench/ape_bench.jsonl \
  llm_config.model_name=gemini_3_flash \
  --orchestrator_id claude_code_comparison

# Codex CLI
python -m ape.scaffolds.codex.main inputs/ape_bench/ape_bench.jsonl \
  llm_config.model_name=gemini_3_flash \
  --orchestrator_id codex_comparison
```

### 4. Constructing APE-Bench

**Paper Reference**: Section 4 "APE-Bench: Automated Benchmark Construction"

The APE-Bench pipeline automatically extracts proof engineering tasks from Mathlib4 commit histories.

```bash
# Extract tasks from date range
python -m src.datasets.ape_bench.main \
  --repo_url "https://github.com/leanprover-community/mathlib4.git" \
  --start_date "2026-01-06" \
  --end_date "2026-01-12" \
  --num_processes 8 \
  model=gpt_5.2 \
  validate_generated_task=true

# Use custom configuration
python -m src.datasets.ape_bench.main \
  --config configs/ape_bench_config.yaml \
  --repo_url "https://github.com/leanprover-community/mathlib4.git" \
  --start_date "2026-01-06" \
  --end_date "2026-01-12"
```

**Key Parameters**:
- `--repo_url`: Mathlib4 repository URL
- `--start_date`, `--end_date`: Date range for commit extraction
- `model`: LLM for instruction synthesis
- `validate_generated_task`: Whether to validate tasks via dual verification
- `num_processes`: Parallel processes for pipeline stages

**Pipeline Stages** (Section 4.1):
1. **Commit Filtering**: Extract file-level modifications (5-100 lines)
2. **Instruction Synthesis**: Generate natural-language task descriptions
3. **Validation**: Verify tasks are solvable via dual verification

**Output**: Generated tasks saved to orchestrator run directory under `.ape/runs/`

## Project Structure

```
.
├── inputs/                          # Benchmark datasets
│   ├── ape_bench/                  # APE-Bench (100 proof engineering tasks)
│   ├── ape_judge_benchmark/        # Semantic judge validation (64 tasks)
│   ├── minictx_v2/                 # Theorem proving benchmarks
│   └── minif2f/                    # Competition theorem proving
├── src/
│   ├── ape/
│   │   ├── tasks/                  # Task contract implementations
│   │   │   ├── base.py            # BaseTask, BaseTaskData
│   │   │   ├── models.py          # WorkspaceInfo, verification protocols
│   │   │   └── lean_tasks/        # Lean-specific tasks
│   │   │       └── formal_math/
│   │   │           ├── proof_engineering/   # APE tasks
│   │   │           ├── theorem_proving/     # Theorem proving
│   │   │           └── judgment/            # Semantic validation
│   │   ├── scaffolds/              # Agent implementations
│   │   │   ├── ape_agent/         # APE-Agent with integrated verification
│   │   │   ├── claude_code/       # Claude Code integration
│   │   │   └── codex/             # Codex CLI scaffold
│   │   ├── toolkits/               # Infrastructure services
│   │   │   ├── execute/           # Verification services
│   │   │   │   └── lean/
│   │   │   │       ├── build.py  # Execute database builder
│   │   │   │       └── core/     # Content-addressable storage
│   │   │   ├── retrieve/          # Semantic search
│   │   │   │   └── lean/
│   │   │   │       ├── build.py  # Retrieval index builder
│   │   │   │       └── semantic_annotation/
│   │   │   ├── file_system/       # File operations
│   │   │   └── code/              # Code navigation
│   │   ├── runtime/                # Execution environments
│   │   │   ├── local/             # Direct execution
│   │   │   ├── isolated_local/    # Workspace copying
│   │   │   └── container/         # Docker isolation
│   │   ├── orchestration/          # Batch execution
│   │   │   ├── orchestrator.py   # TaskOrchestrator
│   │   │   └── worker.py         # Task execution
│   │   └── llm_clients/            # LLM integrations
│   └── datasets/
│       ├── ape_bench/            # APE-Bench pipeline
│       │   ├── main.py            # Pipeline entry point
│       │   ├── collector.py       # Commit filtering
│       │   └── task.py            # Instruction synthesis
│       ├── pr_review/             # PR review benchmark pipeline
│       │   ├── main.py            # GitHub extraction entry point
│       │   ├── collector.py       # PR + maintainer feedback collection
│       │   └── config.py          # Hyperparameter config
│       └── taxonomy/               # Task taxonomy
├── setup.py
├── requirements.txt
└── README.md
```

## Configuration

### Task Contract Specification

Task contracts are defined as JSONL files where each line is a JSON object. Tasks are loaded using `load_tasks_from_file()` from `src/ape/tasks/utils.py`:

```python
from ape.tasks.utils import load_tasks_from_file
from pathlib import Path

# Load tasks from JSONL file
tasks = load_tasks_from_file(
    file_path=Path("inputs/minif2f/minif2f_test.jsonl"),
    config=scaffold_config,
    max_tasks=None,  # Load all tasks
    task_config_overrides={"enabled_tools": ["lean_verify"]}
)
```

**JSONL Task Format Example** (from `inputs/minif2f/minif2f_test.jsonl`):
```json
{
  "task_id": "mathd_algebra_478",
  "task_type": "lean_theorem_proving",
  "metadata": {"split": "test"},
  "theorem_statement": "import Mathlib\n...\ntheorem mathd_algebra_478 ...",
  "target_workspace": {
    "name": "target",
    "commit_hash": "2df2f0150c275ad53cb3c90f7c98ec15a56a1a67",
    "repo_url": "https://github.com/leanprover-community/mathlib4.git",
    "default_target": "Mathlib",
    "toolchain": "leanprover/lean4:v4.22.0",
    "read_only_path_patterns": ["**/*"]
  }
}
```

**Task Contract Components** (from `src/ape/tasks/base.py`):
- `BaseTaskData`: Input data (task_id, task_type, metadata, etc.)
- `BaseTaskConfig`: Task-specific configuration (enabled_tools, etc.)
- `BaseTask`: Task execution logic (setup, evaluate, etc.)
- `BaseTaskResult`: Output results (success, score, metrics, etc.)
- `EvaluationResult`: Intermediate evaluation state
- `WorkspaceInfo` (from `src/ape/tasks/models.py`): Workspace metadata with access control:
  - `blocked_path_patterns`: Paths completely blocked from access
  - `read_only_path_patterns`: Paths that can be read but not written
  - `no_read_path_patterns`: Paths that can be written but not read

### Scaffold Configuration

Scaffolds are configured via CLI or YAML:

```yaml
# APE-Agent configuration
scaffold_type: ape_agent

llm_config:
  model_name: gpt_5.2
  temperature: 0.7
  max_tokens: 8000

runtime_config:
  runtime_type: isolated_local

execution:
  sample_count: 3
  sample_max_cost: 3.0
  max_turns: 100
  num_processes: 8

task_config:
  semantic_validation:
    enabled: true
    num_judges: 3

skills:
  enabled: true
  repo_discovery: true
  extra_roots:
    - ./skills
    - ../shared-skills/reviewer
```

### Multi-Version Infrastructure

Execute and retrieve services are configured in:
- `src/ape/toolkits/execute/lean/config.py` - `LeanVerifyToolConfig`
- `src/ape/toolkits/retrieve/lean/config.py` - `LeanRetrieveToolConfig`

Default paths:
- Repository storage: `data/code_execute/repos/`
- Build artifacts: `data/code_execute/storage/`
- Retrieval database: `data/lean_retrieve/`
- Execution runs: `.ape/runs/`

## Datasets

### APE-Bench

- **Path**: `inputs/ape_bench/ape_bench.jsonl`
- **Size**: 100 tasks from 67 Mathlib4 commits (2026-01-06 to 2026-01-12)
- **Task Type**: Proof engineering (bug fixes, features, refactoring)
- **Zero Contamination**: All commits after model training cutoffs

### APE Judge Benchmark

- **Path**: `inputs/ape_judge_benchmark/ape_judge_benchmark.jsonl`
- **Size**: 64 expert-annotated tasks
- **Purpose**: Validate LLM-as-Judge reliability for semantic equivalence

### Mathlib PR Review Benchmark

- **Path**: `inputs/proof_pr_review/mathlib_pr_review_*.jsonl` (generated)
- **Task Types**: `lean_pr_review` and `skilled_pr_review`
- **Source**: Real pull requests from `leanprover-community/mathlib4` via GitHub API
- **Goal**: Decide if a PR is merge-ready and identify blocking/advisory issues
- **Task Envelope**: Shared snapshot-driven schema with top-level `snapshot`, optional `evaluation`, optional `benchmark_context`, plus `target_workspace`
- **Temporal Snapshots**: One data point = one maintainer review round (PRs can contribute multiple rounds)
- **Round Feedback**: Each round record groups that reviewer’s review body + inline review comments + same-round high-level issue comments
- **Conversation Context**: `snapshot.conversation` includes both maintainer and PR-author comments for that round
- **PR-Head Hints**: `snapshot.pr_head` carries fork/head checkout hints for live head-workspace setup
- **Comment-Only Support**: Maintainer comments without formal review states can still become extracted rounds
- **Ground Truth**: Benchmark labels live under `evaluation.ground_truth`, derived from feedback in that review round rather than the final PR state
- **Live CLI Mode**: Uses the same snapshot builder but leaves `evaluation=null`, so interactive live reviews are intentionally unscored
- **Extraction Order**: Configure `pr_order=newest` or `pr_order=oldest` when collecting candidates
- **Primary Metric**: `review_quality_score` in `[0,1]`
  - `0.65 * decision_accuracy`
  - `0.25 * blocking_issue_f1`
  - `0.10 * advisory_issue_f1`
  - plus false-approve penalty for approving PRs that experts rejected

Build/rebuild this benchmark (new pipeline under `src/datasets/pr_review/`):
```bash
python -m src.datasets.pr_review.main \
  start_date=2025-01-01 \
  end_date=2025-03-31 \
  date_field=closed \
  decision_review_states='["APPROVED","CHANGES_REQUESTED","COMMENTED"]' \
  include_comment_only_rounds=True \
  max_review_events_per_pr=0 \
  max_prs=200 \
  pr_order=newest \
  output_file=inputs/proof_pr_review/mathlib_pr_review_benchmark.jsonl \
  require_maintainer_feedback=True
```

Or with YAML config:
```bash
python -m src.datasets.pr_review.main --config configs/pr_review_config.yaml
```

Optional legacy wrapper (same pipeline):
```bash
python3 src/datasets/external_benchmarks/build_mathlib_pr_review.py \
  start_date=2025-01-01 end_date=2025-03-31
```

### MiniCtx v2

- **Path**: `inputs/minictx_v2/`
- **Size**: 334 test tasks + 334 validation tasks
- **Task Type**: Theorem proving from multiple domains
- **Subsets**: mathlib, carleson, FLT, foundation, HepLean, Seymour, ConNF

### MiniF2F

- **Path**: `inputs/minif2f/`
- **Size**: 488 tasks (244 test + 243 validation)
- **Task Type**: Competition mathematics theorem proving

## License

This project is licensed under the **MIT License**. See the [LICENSE](./LICENSE) file for details.

## Citation

If you use APE-Bench in your research, please cite:

```bibtex
@misc{xin2026apebenchevaluatingautomatedproof,
      title={APE-Bench: Evaluating Automated Proof Engineering for Formal Math Libraries},
      author={Huajian Xin and Luming Li and Xiaoran Jin and Jacques Fleuriot and Wenda Li},
      year={2026},
      eprint={2504.19110},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2504.19110v3},
}
```

---
<a name="chinese-version"></a>

# APE-Bench: 评估形式化数学库的自动化证明工程

<p align="center">
  <a href="https://arxiv.org/abs/2504.19110v3">
    <img src="https://img.shields.io/badge/APE--Bench_I-Paper-red"></a>
  <a href="https://huggingface.co/datasets/HuajianXin/APE-Bench_I">
    <img src="https://img.shields.io/badge/APE--Bench_I-Hugging Face Dataset-orange"></a>
  <a href="./LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-blue"></a>
  <a href="https://github.com/xinhjBrant/APE-Bench">
    <img src="https://img.shields.io/badge/GitHub-Repository-lightgrey"></a>
</p>

**APE-Bench** 是论文"[APE-Bench: Evaluating Automated Proof Engineering for Formal Math Libraries](https://arxiv.org/abs/2504.19110v3)"的参考实现。本代码库实现了论文中描述的完整基础设施，包括 APE-Bench 自动化流水线、APE-Harness 任务合约框架以及多版本验证/检索服务。

## 目录
* [论文到代码映射](#论文到代码映射)
* [安装](#安装)
* [快速开始](#快速开始)
* [使用指南](#使用指南)
  * [1. 构建执行数据库](#1-构建执行数据库)
  * [2. 构建检索索引](#2-构建检索索引)
  * [3. 运行评估](#3-运行评估)
  * [4. 构造 APE-Bench](#4-构造-ape-bench)
* [项目结构](#项目结构)
* [配置](#配置)
* [数据集](#数据集)
* [许可证](#许可证)
* [引用](#引用)

## 论文到代码映射

### 核心概念

| 论文概念 | 代码路径 |
|---------|---------|
| **Task Contract Abstraction** | `src/ape/tasks/base.py` (`BaseTask`, `BaseTaskData`, `BaseTaskConfig`, `BaseTaskResult`, `EvaluationResult`), `src/ape/tasks/models.py` (`WorkspaceInfo`) |
| **APE-Harness Infrastructure** | `src/ape/` (orchestration, toolkits, runtime, scaffolds) |
| **APE-Bench Pipeline** | `src/datasets/ape_bench/` |
| **Execute Services** | `src/ape/toolkits/execute/lean/` |
| **Retrieve Services** | `src/ape/toolkits/retrieve/lean/` |
| **APE-Agent Scaffold** | `src/ape/scaffolds/ape_agent/` |
| **Claude Code Scaffold** | `src/ape/scaffolds/claude_code/` |
| **Codex Scaffold** | `src/ape/scaffolds/codex/` |

### 任务类型

| 论文任务类型 | 代码实现 | 入口点 |
|------------|---------|--------|
| **Proof Engineering** | `src/ape/tasks/lean_tasks/formal_math/proof_engineering/` | `LeanProofEngineeringTask` |
| **Theorem Proving** | `src/ape/tasks/lean_tasks/formal_math/theorem_proving/` | `LeanTheoremProvingTask` |
| **Judgment** | `src/ape/tasks/lean_tasks/formal_math/judgment/` | `LeanJudgmentTask` |
| **Instruction Synthesis** | `src/datasets/ape_bench/task.py` | `InstructionGenerationTask` |
| **Library Annotation** | `src/ape/toolkits/retrieve/lean/semantic_annotation/task.py` | `AnnotationTask` |

### 基础设施服务

| 论文组件 | 代码路径 | 关键函数 |
|---------|---------|---------|
| **Content-Addressable Storage** | `src/ape/toolkits/execute/lean/core/build_manager.py` | `BuildManager.build_workspace()` |
| **Semantic Search** | `src/ape/toolkits/retrieve/lean/` | `LeanRetrieveToolsProvider` |
| **Workspace Isolation** | `src/ape/tasks/models.py`, `src/ape/runtime/` | `WorkspaceInfo` (访问控制), `LocalRuntime`, `IsolatedLocalRuntime` |
| **Dual Verification** | `src/ape/tasks/lean_tasks/formal_math/` 中的任务评估 | `evaluate()` 方法 |

## 安装

### 前置要求

*   Python 3.10+
*   已安装 [Lean 4](https://leanprover.github.io/lean4/doc/setup.html) 和 [elan](https://github.com/leanprover/elan)
*   Git

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/xinhjBrant/APE-Bench.git
cd APE-Bench

# 2. 安装仓库
pip install -e .
```

## 快速开始

### 交互式 CLI

使用统一的 `ape` CLI 在本地工作空间中启动交互式 agent 会话：

```bash
# APE-Agent
ape chat ape-agent --workspace .

# Claude Code 会话
ape chat claude-code --workspace . --prompt "Inspect this Lean project"

# Codex 会话
ape chat codex --workspace . --model gpt_5

# 从 YAML 加载交互式 scaffold 配置，并按需用命令行覆盖
ape chat ape-agent --config configs/cli.yaml --workspace . llm_config.temperature=0.7
```

当你想运行一个已注册任务，而不是自由交互式工作空间会话时，可以使用 `ape task ...`：

```bash
# 显示当前 CLI 可见的已注册任务
ape task ape-agent

# 运行一个内置任务，并交互式填写字段
ape task ape-agent lean_pr_review

# 从 YAML 加载 task 模式下的 scaffold 配置
ape task ape-agent --config configs/cli.yaml lean_pr_review

# 导入自定义任务模块；其中注册的任务会成为可用任务名
ape task ape-agent \
  --task-module examples.arithmetic.task \
  arithmetic

# 运行一个基准任务记录
ape task ape-agent \
  --task-file inputs/proof_pr_review/mathlib_pr_review_10tasks.jsonl \
  --task-index 0 \
  lean_pr_review

# 导入自定义任务模块并通过内联 JSON 运行
ape task ape-agent \
  --task-module examples.arithmetic.task \
  arithmetic \
  --task-data-json '{"expression":"2 + 2","expected_result":4.0}'
```

当你运行 `ape chat ...` 或 `ape task ...` 时，`--config` 与批量 scaffold 入口遵循相同的
优先级：显式 CLI 参数和尾随 `key=value` 覆盖优先于 YAML，YAML 又优先于 Pydantic 默认值。

Agent skill 通过 scaffold 级别的 `skills` 配置块按需启用。打开 `repo_discovery` 后，
系统会检查当前活动工作空间中的原生仓库技能目录：Codex 使用 `.agents/skills`，
Claude Code 使用 `.claude/skills`，APE-Agent 同时读取两者。`extra_roots` 既可以指向
单个 skill 目录，也可以指向一个包含多个 skill 的目录。

```yaml
skills:
  enabled: true
  repo_discovery: true
  extra_roots:
    - ./skills
    - ../shared-skills/code-review
```

YAML 中的相对 `extra_roots` 会相对于 YAML 文件所在目录解析；尾随 CLI 覆盖中的相对路径
会相对于当前工作目录解析：

```bash
ape chat codex --config configs/cli.yaml --workspace . 'skills.extra_roots=["./local-skills"]'
ape task claude-code --task-module examples.arithmetic.task arithmetic \
  --task-data-json '{"expression":"2 + 2","expected_result":4.0}' \
  'skills.enabled=True' \
  'skills.extra_roots=["./team-skills"]'
python -m ape.scaffolds.ape_agent.main inputs/ape_bench/ape_bench.jsonl \
  --config configs/ape_agent.yaml \
  'skills.extra_roots=["./benchmark-skills"]'
```

当你运行 `ape task ... <registered_task>` 且不提供 `--task-file` 或 `--task-data-json`
时，CLI 会读取该任务的 Pydantic schema，并在终端中逐项提示你填写输入字段。像
`target_workspace` 这样的嵌套字段也会继续展开并逐项收集。

`lean_pr_review` 提供了更友好的交互流程：CLI 只会询问 GitHub `pr_url` 和该 PR 分支上的
`commit`，然后自动构建一个 live review snapshot。这个 CLI 入口始终生成共享的 PR review
封装结构，并令 `evaluation: null`；基准数据则复用同样的 `snapshot` 结构，再附加
`evaluation` 和 `benchmark_context`。

兼容性别名仍然可用：

```bash
apea --workspace .
ape-claude --workspace .
ape-codex --workspace .
```

这些交互式命令与现有批量评测入口分离，例如
`python -m ape.scaffolds.ape_agent.main ...`，后者保持不变。

创建自定义任务需要三个组件：**TaskData**（输入）、**Task**（逻辑）、**register_task**（注册）。

参考 `examples/arithmetic/task.py` 查看完整的最小示例。

### 示例：算术任务

```python
from ape.tasks.base import BaseTask, BaseTaskData, BaseTaskResult, EvaluationResult, register_task

# 1. 定义输入数据
class ArithmeticTaskData(BaseTaskData):
    expression: str
    expected_result: float

# 2. 实现任务逻辑
class ArithmeticTask(BaseTask):
    task_type = "arithmetic"
    data_class = ArithmeticTaskData
    task_result_class = BaseTaskResult

    async def create_user_prompt(self) -> str:
        return f"计算: {self.data.expression}"

    async def evaluate(self, submission: str) -> EvaluationResult:
        result = float(submission.strip())
        is_correct = abs(result - self.data.expected_result) < 1e-6
        return EvaluationResult(success=is_correct, score=1.0 if is_correct else 0.0)

# 3. 注册任务
register_task("arithmetic", ArithmeticTask)
```

**输入 JSONL** (`input.jsonl`):
```json
{"task_id": "task_001", "task_type": "arithmetic", "expression": "1234 + 5678", "expected_result": 6912.0}
```

**使用**:
```bash
python -m ape.scaffolds.ape_agent.main input.jsonl \
  --task_modules your.module.task \
  llm_config.model_name=gpt_5_mini
```

`--task_modules` 参数导入任务模块，执行 `register_task()` 使任务类型可用。

## 使用指南

### 1. 构建执行数据库

**论文参考**: 第 4.2 节 "Multi-Version Execution"

执行数据库使用内容寻址存储为多个 Mathlib4 版本提供编译验证。

```bash
# 从单个提交构建
python -m ape.toolkits.execute.lean.build \
  --target_repo "https://github.com/leanprover-community/mathlib4.git@@85eacf338f4140b402a3f970dde352b457e0dd5f"

# 从包含任务的 JSONL 文件构建
python -m ape.toolkits.execute.lean.build \
  --input_file inputs/ape_bench/ape_bench.jsonl \
  --num_processes 8

# 从多个数据集构建
python -m ape.toolkits.execute.lean.build \
  --input_file inputs/minictx_v2/*.jsonl \
  --num_processes 16
```

**关键参数**:
- `--target_repo`: 单个仓库，格式为 `repo_url@@commit_hash`
- `--input_file`: 包含 `target_workspace` 字段的任务 JSONL 文件
- `--num_processes`: 并行构建进程数 (默认: CPU 数量)

**输出**: 编译产物存储在 `data/code_execute/storage/`，带内容去重。

### 2. 构建检索索引

**论文参考**: 第 4.2 节 "Version-Scoped Retrieval"

检索索引支持在特定提交的库声明中进行语义搜索。

```bash
# 为单个提交构建索引
python -m ape.toolkits.retrieve.lean.build \
  --target_repo "https://github.com/leanprover-community/mathlib4.git@@2df2f0150c275ad53cb3c90f7c98ec15a56a1a67@@Mathlib" \
  num_processes=32

# 使用参考工作空间构建
python -m ape.toolkits.retrieve.lean.build \
  --target_repo "https://github.com/fpvandoorn/carleson.git@@a5d265f109105809de4aaff16776b7c16b1c0bd5@@Carleson" \
  --reference_repo "https://github.com/leanprover-community/mathlib4.git@@79e94a093aff4a60fb1b1f92d9681e407124c2ca@@Mathlib" \
  num_processes=32

# 从任务文件构建
python -m ape.toolkits.retrieve.lean.build \
  --input_file inputs/ape_bench/ape_bench.jsonl \
  num_processes=32
```

**关键参数**:
- `--target_repo`: 目标仓库，格式为 `repo_url@@commit_hash@@default_target`
  - `default_target`: 要提取的目录 (如 `Mathlib`)，或省略以提取所有文件
- `--reference_repo`: 参考仓库 (可以多次指定)
- `num_processes`: 并行标注进程数

**输出**:
- 嵌入数据库: `data/lean_retrieve/`
- 已标注声明: `data/lean_retrieve/repos/{repo_name}/storage/annotated_ids.txt`

### 3. 运行评估

**论文参考**: 第 5 节 "Evaluation"

使用 APE-Harness 以不同的 scaffolds 和配置执行任务。

#### 基本执行

```bash
# 使用 APE-Agent scaffold 运行
python -m ape.scaffolds.ape_agent.main \
  inputs/minictx_v2/all_test.jsonl \
  llm_config.model_name=gemini_3_flash \
  execution.sample_max_cost=3.0 \
  execution.num_processes=8 \
  runtime_config.runtime_type=isolated_local \
  --orchestrator_id ape_agent_minictx_gemini_3_flash_isolated_local

# 使用 Claude Code scaffold 运行
python -m ape.scaffolds.claude_code.main \
  inputs/ape_bench/ape_bench.jsonl \
  llm_config.model_name=claude_3_opus \
  execution.sample_max_cost=3.0 \
  --orchestrator_id claude_code_ape_bench_opus
```

#### 通过 CLI 配置

所有配置参数都可以使用点号语法覆盖:

```bash
# LLM 配置
llm_config.model_name=gpt_5.2
llm_config.temperature=0.7
llm_config.max_tokens=8000

# 执行配置
execution.sample_max_cost=3.0          # 每个任务的预算 (USD)
execution.max_turns=100                # 对话轮次限制
execution.num_processes=8              # 并行 worker
execution.sample_count=1               # 每个任务的样本数

# 运行时配置
runtime_config.runtime_type=isolated_local   # 或: local, container
```

#### Scaffold 对比 (论文表 3)

```bash
# APE-Agent (集成验证)
python -m ape.scaffolds.ape_agent.main inputs/ape_bench/ape_bench.jsonl \
  llm_config.model_name=gemini_3_flash \
  --orchestrator_id ape_agent_comparison

# Claude Code
python -m ape.scaffolds.claude_code.main inputs/ape_bench/ape_bench.jsonl \
  llm_config.model_name=gemini_3_flash \
  --orchestrator_id claude_code_comparison

# Codex CLI
python -m ape.scaffolds.codex.main inputs/ape_bench/ape_bench.jsonl \
  llm_config.model_name=gemini_3_flash \
  --orchestrator_id codex_comparison
```

### 4. 构造 APE-Bench

**论文参考**: 第 4 节 "APE-Bench: Automated Benchmark Construction"

APE-Bench 流水线从 Mathlib4 提交历史自动提取证明工程任务。

```bash
# 从日期范围提取任务
python -m src.datasets.ape_bench.main \
  --repo_url "https://github.com/leanprover-community/mathlib4.git" \
  --start_date "2026-01-06" \
  --end_date "2026-01-12" \
  --num_processes 8 \
  model=gpt_5.2 \
  validate_generated_task=true

# 使用自定义配置
python -m src.datasets.ape_bench.main \
  --config configs/ape_bench_config.yaml \
  --repo_url "https://github.com/leanprover-community/mathlib4.git" \
  --start_date "2026-01-06" \
  --end_date "2026-01-12"
```

**关键参数**:
- `--repo_url`: Mathlib4 仓库 URL
- `--start_date`, `--end_date`: 提取提交的日期范围
- `model`: 用于指令合成的 LLM
- `validate_generated_task`: 是否通过双重验证来验证任务
- `num_processes`: 流水线阶段的并行进程数

**流水线阶段** (第 4.1 节):
1. **Commit Filtering**: 提取文件级修改 (5-100 行)
2. **Instruction Synthesis**: 生成自然语言任务描述
3. **Validation**: 通过双重验证验证任务可解

**输出**: 生成的任务保存到 `.ape/runs/` 下的编排器运行目录

## 项目结构

```
.
├── inputs/                          # 基准测试数据集
│   ├── ape_bench/                  # APE-Bench (100 个证明工程任务)
│   ├── ape_judge_benchmark/        # 语义判断验证 (64 个任务)
│   ├── minictx_v2/                 # 定理证明基准
│   └── minif2f/                    # 竞赛定理证明
├── src/
│   ├── ape/
│   │   ├── tasks/                  # 任务合约实现
│   │   │   ├── base.py            # BaseTask, BaseTaskData
│   │   │   ├── models.py          # WorkspaceInfo, 验证协议
│   │   │   └── lean_tasks/        # Lean 特定任务
│   │   │       └── formal_math/
│   │   │           ├── proof_engineering/   # APE 任务
│   │   │           ├── theorem_proving/     # 定理证明
│   │   │           └── judgment/            # 语义验证
│   │   ├── scaffolds/              # Agent 实现
│   │   │   ├── ape_agent/         # 带集成验证的 APE-Agent
│   │   │   ├── claude_code/       # Claude Code 集成
│   │   │   └── codex/             # Codex CLI scaffold
│   │   ├── toolkits/               # 基础设施服务
│   │   │   ├── execute/           # 验证服务
│   │   │   │   └── lean/
│   │   │   │       ├── build.py  # 执行数据库构建器
│   │   │   │       └── core/     # 内容寻址存储
│   │   │   ├── retrieve/          # 语义搜索
│   │   │   │   └── lean/
│   │   │   │       ├── build.py  # 检索索引构建器
│   │   │   │       └── semantic_annotation/
│   │   │   ├── file_system/       # 文件操作
│   │   │   └── code/              # 代码导航
│   │   ├── runtime/                # 执行环境
│   │   │   ├── local/             # 直接执行
│   │   │   ├── isolated_local/    # 工作空间复制
│   │   │   └── container/         # Docker 隔离
│   │   ├── orchestration/          # 批量执行
│   │   │   ├── orchestrator.py   # TaskOrchestrator
│   │   │   └── worker.py         # 任务执行
│   │   └── llm_clients/            # LLM 集成
│   └── datasets/
│       ├── ape_bench/            # APE-Bench 流水线
│       │   ├── main.py            # 流水线入口点
│       │   ├── collector.py       # 提交过滤
│       │   └── task.py            # 指令合成
│       └── taxonomy/               # 任务分类
├── setup.py
├── requirements.txt
└── README.md
```

## 配置

### 任务合约规范

任务合约定义为JSONL文件，每行是一个JSON对象。任务通过 `src/ape/tasks/utils.py` 中的 `load_tasks_from_file()` 加载：

```python
from ape.tasks.utils import load_tasks_from_file
from pathlib import Path

# 从JSONL文件加载任务
tasks = load_tasks_from_file(
    file_path=Path("inputs/minif2f/minif2f_test.jsonl"),
    config=scaffold_config,
    max_tasks=None,  # 加载所有任务
    task_config_overrides={"enabled_tools": ["lean_verify"]}
)
```

**JSONL任务格式示例** (来自 `inputs/minif2f/minif2f_test.jsonl`):
```json
{
  "task_id": "mathd_algebra_478",
  "task_type": "lean_theorem_proving",
  "metadata": {"split": "test"},
  "theorem_statement": "import Mathlib\n...\ntheorem mathd_algebra_478 ...",
  "target_workspace": {
    "name": "target",
    "commit_hash": "2df2f0150c275ad53cb3c90f7c98ec15a56a1a67",
    "repo_url": "https://github.com/leanprover-community/mathlib4.git",
    "default_target": "Mathlib",
    "toolchain": "leanprover/lean4:v4.22.0",
    "read_only_path_patterns": ["**/*"]
  }
}
```

**任务合约组件** (来自 `src/ape/tasks/base.py`):
- `BaseTaskData`: 输入数据 (task_id, task_type, metadata等)
- `BaseTaskConfig`: 任务特定配置 (enabled_tools等)
- `BaseTask`: 任务执行逻辑 (setup, evaluate等)
- `BaseTaskResult`: 输出结果 (success, score, metrics等)
- `EvaluationResult`: 中间评估状态
- `WorkspaceInfo` (来自 `src/ape/tasks/models.py`): 工作空间元数据及访问控制:
  - `blocked_path_patterns`: 完全禁止访问的路径
  - `read_only_path_patterns`: 可读但不可写的路径
  - `no_read_path_patterns`: 可写但不可读的路径

### Scaffold 配置

Scaffolds 通过 CLI 或 YAML 配置:

```yaml
# APE-Agent 配置
scaffold_type: ape_agent

llm_config:
  model_name: gpt_5.2
  temperature: 0.7
  max_tokens: 8000

runtime_config:
  runtime_type: isolated_local

execution:
  sample_count: 3
  sample_max_cost: 3.0
  max_turns: 100
  num_processes: 8

task_config:
  semantic_validation:
    enabled: true
    num_judges: 3

skills:
  enabled: true
  repo_discovery: true
  extra_roots:
    - ./skills
    - ../shared-skills/reviewer
```

### 多版本基础设施

执行和检索服务配置在:
- `src/ape/toolkits/execute/lean/config.py` - `LeanVerifyToolConfig`
- `src/ape/toolkits/retrieve/lean/config.py` - `LeanRetrieveToolConfig`

默认路径:
- 仓库存储: `data/code_execute/repos/`
- 构建产物: `data/code_execute/storage/`
- 检索数据库: `data/lean_retrieve/`
- 执行运行: `.ape/runs/`

## 数据集

### APE-Bench

- **路径**: `inputs/ape_bench/ape_bench.jsonl`
- **大小**: 来自 67 个 Mathlib4 提交的 100 个任务 (2026-01-06 至 2026-01-12)
- **任务类型**: 证明工程 (错误修复、功能、重构)
- **零污染**: 所有提交都在模型训练截止之后

### APE Judge Benchmark

- **路径**: `inputs/ape_judge_benchmark/ape_judge_benchmark.jsonl`
- **大小**: 64 个专家标注任务
- **用途**: 验证 LLM-as-Judge 在语义等价性判断上的可靠性

### MiniCtx v2

- **路径**: `inputs/minictx_v2/`
- **大小**: 334 个测试任务 + 334 个验证任务
- **任务类型**: 多个领域的定理证明
- **子集**: mathlib, carleson, FLT, foundation, HepLean, Seymour, ConNF

### MiniF2F

- **路径**: `inputs/minif2f/`
- **大小**: 488 个任务 (244 测试 + 243 验证)
- **任务类型**: 竞赛数学定理证明

## 许可证

本项目根据 **MIT 许可证**授权。详情见 [LICENSE](./LICENSE) 文件。

## 引用

如果您在研究中使用 APE-Bench，请引用:

```bibtex
@misc{xin2026apebenchevaluatingautomatedproof,
      title={APE-Bench: Evaluating Automated Proof Engineering for Formal Math Libraries},
      author={Huajian Xin and Luming Li and Xiaoran Jin and Jacques Fleuriot and Wenda Li},
      year={2026},
      eprint={2504.19110},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2504.19110v3},
}
```
