from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from paperforge.intake_agent import run_paper_intake
from paperforge.models import ResearchJob, StepState
from paperforge.steps import now_iso
from paperforge.storage import get_data_dir


BatchIntakeRunner = Callable[..., ResearchJob]


@dataclass(frozen=True)
class BatchIntakeItem:
    input: str
    job_id: str | None
    slug: str | None
    status: str
    error: str | None = None


@dataclass(frozen=True)
class BatchIntakeResult:
    batch_id: str
    created_at: str
    status: StepState
    total_inputs: int
    items: list[BatchIntakeItem]
    json_path: Path
    summary_path: Path


def run_batch_intake(
    multiline_input: str,
    *,
    intake_runner: BatchIntakeRunner | None = None,
    use_query_planner: bool = True,
) -> BatchIntakeResult:
    inputs = _paper_inputs(multiline_input)
    batch_id = f"batch-{uuid.uuid4().hex[:12]}"
    created_at = now_iso()
    batches_dir = get_data_dir() / "batches"
    batches_dir.mkdir(parents=True, exist_ok=True)
    json_path = batches_dir / f"{batch_id}.json"
    summary_path = batches_dir / f"{batch_id}-summary.md"

    runner = intake_runner or run_paper_intake
    items: list[BatchIntakeItem] = []
    for input_text in inputs:
        try:
            job = runner(input_text, use_query_planner=use_query_planner)
            items.append(
                BatchIntakeItem(
                    input=input_text,
                    job_id=job.id,
                    slug=job.paper_slug,
                    status=job.status,
                    error=None,
                )
            )
        except Exception as error:
            items.append(
                BatchIntakeItem(
                    input=input_text,
                    job_id=None,
                    slug=None,
                    status="failed",
                    error=str(error),
                )
            )

    status = _batch_status(items)
    result = BatchIntakeResult(
        batch_id=batch_id,
        created_at=created_at,
        status=status,
        total_inputs=len(inputs),
        items=items,
        json_path=json_path,
        summary_path=summary_path,
    )
    _write_batch_json(result)
    summary_path.write_text(_batch_summary_markdown(result), encoding="utf-8")
    return result


def _paper_inputs(multiline_input: str) -> list[str]:
    return [line.strip() for line in multiline_input.splitlines() if line.strip()]


def _batch_status(items: list[BatchIntakeItem]) -> StepState:
    if not items:
        return "needs_user_input"
    if all(item.status == "completed" for item in items):
        return "completed"
    return "partial"


def _write_batch_json(result: BatchIntakeResult) -> None:
    payload = {
        "batch_id": result.batch_id,
        "created_at": result.created_at,
        "status": result.status,
        "total_inputs": result.total_inputs,
        "items": [asdict(item) for item in result.items],
        "summary_path": result.summary_path.name,
    }
    result.json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _batch_summary_markdown(result: BatchIntakeResult) -> str:
    lines = [
        "# Batch Intake Summary",
        "",
        f"- Batch ID: `{result.batch_id}`",
        f"- Status: {result.status}",
        f"- Created at: {result.created_at}",
        f"- Total paper inputs: {result.total_inputs}",
        "- Scope: Sequential intake only; no parallel execution and no literature review summary.",
        "",
        "## Papers",
        "",
        "| Input | Job ID | Slug | Status | Error |",
        "| --- | --- | --- | --- | --- |",
    ]
    if not result.items:
        lines.append("| - | - | - | needs_user_input | No non-empty paper inputs provided. |")
        lines.append("")
        return "\n".join(lines)

    for item in result.items:
        lines.append(
            "| "
            + " | ".join(
                [
                    _table_cell(item.input),
                    _table_cell(item.job_id or "-"),
                    _table_cell(item.slug or "-"),
                    _table_cell(item.status),
                    _table_cell(item.error or "-"),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
