"""
v2 first-round-review runner: run a model over v2 gold records and emit
prediction JSONL for the D1/D2 evaluators.

Modes (spec §4 input contract; the mode is a harness variable):
  diff_only  — model sees title + description + δ₀ in one prompt (floor baseline)
  workspace  — agentic checkout at b with δ₀ applied (not yet implemented)

Usage:
  python -m src.datasets.pr_review_v2.runner --config configs/pr_review_runner_v2.yaml
  python -m src.datasets.pr_review_v2.runner records=<extract.jsonl> model_name=gpt_5_mini limit=5
  python -m src.datasets.pr_review_v2.runner records=<extract.jsonl> dry_run=true limit=1

Each run writes <output>.jsonl plus a <output>_summary.json with parse-failure
rates and token/cost totals. With resume=true, PRs already present in the
output file are skipped.
"""

import argparse
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ape.llm_clients.client import LLMClient
from ape.llm_clients.config import LLMConfig
from ape.llm_clients.models import ContentBlock, ConversationSession
from ape.utils import deep_merge, load_yaml, parse_cli_args
from ape.utils.logging import create_logger
from ape.utils.project import PROJECT_ROOT

from .predictions import (
    RETRY_PROMPT,
    SYSTEM_PROMPT,
    PredictionRecord,
    build_user_prompt,
    parse_prediction_text,
)
from .schema import PRReviewV2Record


class RunnerV2Config(BaseModel):
    records: Path = Field(description="v2 extract JSONL (gold records)")
    output_file: Optional[Path] = None
    output_dir: Path = Field(default=PROJECT_ROOT / "inputs" / "pr_review_v2" / "predictions")

    model_name: str = Field(default="gpt_5_mini")
    mode: str = Field(default="diff_only")
    finding_budget: int = Field(default=10)
    max_tokens: int = Field(default=16000)
    thinking_budget_tokens: int = Field(default=8000)
    temperature: float = Field(default=1.0)

    concurrency: int = Field(default=4)
    limit: int = Field(default=0, description="0 = all records")
    pr_numbers: List[int] = Field(default_factory=list)
    h0_review_commit_only: bool = Field(
        default=False, description="Restrict to the review_commit_id slice (audit scoping rule)"
    )
    max_diff_chars: int = Field(default=120_000)
    resume: bool = Field(default=True)
    dry_run: bool = Field(default=False, description="Print prompts instead of calling the model")


def _resolve_output(config: RunnerV2Config) -> Path:
    if config.output_file:
        return config.output_file
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    name = f"preds_{config.model_name}_{config.mode}_{stamp}.jsonl"
    return config.output_dir / name


def load_records(config: RunnerV2Config) -> List[PRReviewV2Record]:
    records = [
        PRReviewV2Record.model_validate_json(line)
        for line in config.records.read_text().splitlines()
        if line.strip()
    ]
    if config.pr_numbers:
        wanted = set(config.pr_numbers)
        records = [r for r in records if r.pr_number in wanted]
    if config.h0_review_commit_only:
        records = [r for r in records if r.input.h0_resolution == "review_commit_id"]
    if config.limit > 0:
        records = records[: config.limit]
    return records


async def predict_one(
    client: LLMClient,
    config: RunnerV2Config,
    record: PRReviewV2Record,
    semaphore: asyncio.Semaphore,
    logger,
) -> PredictionRecord:
    prediction = PredictionRecord(
        pr_number=record.pr_number, model=config.model_name, mode=config.mode  # type: ignore[arg-type]
    )
    if not record.input.diff:
        prediction.parse_ok = False
        prediction.parse_error = "record_missing_diff"
        return prediction
    if len(record.input.diff) > config.max_diff_chars:
        prediction.parse_ok = False
        prediction.parse_error = f"diff_too_large:{len(record.input.diff)}"
        return prediction

    async with semaphore:
        session = ConversationSession()
        cwd = str(PROJECT_ROOT)
        session.add_system_message([ContentBlock.text_block(SYSTEM_PROMPT)], cwd=cwd)
        session.add_user_message(
            [ContentBlock.text_block(build_user_prompt(record, budget=config.finding_budget))], cwd=cwd
        )

        start = time.time()
        text = ""
        for attempt in (1, 2):  # one corrective retry on unparseable output
            nodes, usage, _raw = await client.call_api(
                session,
                max_tokens=config.max_tokens,
                thinking_budget_tokens=config.thinking_budget_tokens,
                temperature=config.temperature,
                meta_info={"task": "pr_review_v2_runner", "pr_number": record.pr_number},
            )
            prediction.input_tokens += usage.input_tokens
            prediction.output_tokens += usage.output_tokens
            prediction.cost_usd += usage.total_cost
            text = "\n".join(
                block.text
                for node in nodes
                for block in node.message.content
                if block.type == "text" and block.text
            )
            try:
                merge_ready, confidence, findings = parse_prediction_text(
                    text, budget=config.finding_budget
                )
                prediction.merge_ready_as_is = merge_ready
                prediction.confidence = confidence
                prediction.findings = findings
                prediction.parse_ok = True
                prediction.parse_error = None
                break
            except ValueError as exc:
                prediction.parse_ok = False
                prediction.parse_error = str(exc)
                if attempt == 1:
                    prediction.retried_parse = True
                    # call_api does not mutate the session; append the assistant turn
                    # ourselves so the corrective prompt has the failed output in context.
                    session.add_assistant_message([ContentBlock.text_block(text)], cwd=cwd)
                    session.add_user_message(
                        [ContentBlock.text_block(RETRY_PROMPT.format(error=exc))], cwd=cwd
                    )
        prediction.latency_s = round(time.time() - start, 2)
        prediction.raw_text = text
        if not prediction.parse_ok:
            logger.warning("PR #%d: unparseable after retry: %s", record.pr_number, prediction.parse_error)
        return prediction


def _already_done(output_file: Path) -> set:
    if not output_file.exists():
        return set()
    done = set()
    for line in output_file.read_text().splitlines():
        if line.strip():
            done.add(json.loads(line)["pr_number"])
    return done


def summarize(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    parsed = [p for p in predictions if p["parse_ok"]]
    return {
        "predictions": len(predictions),
        "parse_failures": len(predictions) - len(parsed),
        "merge_ready_true": sum(1 for p in parsed if p["merge_ready_as_is"] is True),
        "merge_ready_false": sum(1 for p in parsed if p["merge_ready_as_is"] is False),
        "findings_total": sum(len(p["findings"]) for p in parsed),
        "findings_blocking": sum(
            1 for p in parsed for f in p["findings"] if f["severity"] == "blocking"
        ),
        "anchored_findings": sum(1 for p in parsed for f in p["findings"] if f["anchor"]),
        "input_tokens": sum(p["input_tokens"] for p in predictions),
        "output_tokens": sum(p["output_tokens"] for p in predictions),
        "cost_usd": round(sum(p["cost_usd"] for p in predictions), 4),
    }


async def run(config: RunnerV2Config, logger) -> Optional[Path]:
    if config.mode == "workspace":
        raise SystemExit(
            "workspace mode uses the standard scaffold-config runner:\n"
            "  python -m src.datasets.pr_review_v2.runner_workspace --config configs/pr_review_workspace_v2.yaml"
        )
    if config.mode != "diff_only":
        raise NotImplementedError(f"unknown mode '{config.mode}' (this runner = diff_only)")

    records = load_records(config)
    logger.info("Loaded %d records from %s", len(records), config.records)

    if config.dry_run:
        for record in records:
            print(f"===== PR #{record.pr_number} system =====\n{SYSTEM_PROMPT}\n")
            print(
                f"===== PR #{record.pr_number} user =====\n"
                f"{build_user_prompt(record, budget=config.finding_budget)}\n"
            )
        return None

    output_file = _resolve_output(config)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    done = _already_done(output_file) if config.resume else set()
    todo = [r for r in records if r.pr_number not in done]
    if done:
        logger.info("Resume: %d already done, %d to run", len(done), len(todo))

    llm_config = LLMConfig(
        model_name=config.model_name,
        max_tokens=config.max_tokens,
        thinking_budget_tokens=config.thinking_budget_tokens,
        temperature=config.temperature,
    )
    semaphore = asyncio.Semaphore(config.concurrency)
    written: List[Dict[str, Any]] = []

    async with LLMClient(llm_config, logger=logger) as client:
        tasks = [predict_one(client, config, record, semaphore, logger) for record in todo]
        with output_file.open("a") as fh:
            for future in asyncio.as_completed(tasks):
                prediction = await future
                row = prediction.model_dump(mode="json")
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                fh.flush()
                written.append(row)
                logger.info(
                    "PR #%d: %d findings, merge_ready=%s, %.1fs",
                    prediction.pr_number, len(prediction.findings),
                    prediction.merge_ready_as_is, prediction.latency_s,
                )

    all_rows = [json.loads(line) for line in output_file.read_text().splitlines() if line.strip()]
    summary = summarize(all_rows)
    summary_file = output_file.with_name(output_file.stem + "_summary.json")
    summary_file.write_text(json.dumps(summary, indent=2))
    logger.info("Summary: %s", summary)
    logger.info("Predictions: %s", output_file)
    return output_file


def main(
    config_path: Optional[Path] = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
    logger=None,
) -> Optional[Path]:
    logger = logger or create_logger()
    config_dict: Dict[str, Any] = load_yaml(config_path) if config_path else {}
    if cli_overrides:
        config_dict = deep_merge(config_dict, cli_overrides)
    config = RunnerV2Config.model_validate(config_dict)
    return asyncio.run(run(config, logger))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a model over v2 review records (D1/D2 predictions)")
    parser.add_argument("--config", type=Path, default=None)
    args, remaining = parser.parse_known_args()
    result = main(config_path=args.config, cli_overrides=parse_cli_args(remaining))
    if result:
        print(result)
