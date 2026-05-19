from __future__ import annotations

from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_data_dir, get_paper_vault_dir, relative_to_data_dir, save_job


def run_doubts_scaffold(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Doubts scaffold requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "doubts.md"

    step = start_step(
        create_step(
            "knowledge.write_doubts",
            "Write doubts scaffold",
            ["metadata", "notes/README.md"],
        )
    )
    job.steps.append(step)

    try:
        output_path.write_text(_doubts_markdown(job), encoding="utf-8")
    except Exception as error:
        finish_step(step, "failed", [], str(error))
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    _add_artifact(job, output_path)
    finish_step(step, "completed", [relative_to_data_dir(output_path)])
    job.updated_at = now_iso()
    save_job(job)
    return job


def _doubts_markdown(job: ResearchJob) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("Doubts scaffold requires paper metadata")

    lines = [
        "# Doubts and Follow-up Questions",
        "",
        f"- Paper: {metadata.title}",
        "- Draft status: scaffold only; doubts not generated yet.",
        _source_note_link(job),
        "",
        "## Open Questions",
        "",
        "- Not generated yet.",
        "",
        "## Confusing Formulas",
        "",
        "- Not generated yet.",
        "",
        "## Missing Implementation Details",
        "",
        "- Not generated yet.",
        "",
        "## Claims That Need Verification",
        "",
        "- Not generated yet.",
        "",
        "## Questions to Ask an Interviewer or Mentor",
        "",
        "- Not generated yet.",
        "",
    ]
    return "\n".join(lines)


def _source_note_link(job: ResearchJob) -> str:
    if _existing_path(job, "notes/README.md"):
        return "- Source note: [Paper note scaffold](README.md)"
    return "- Source note: not available yet"


def _existing_path(job: ResearchJob, suffix: str) -> Path | None:
    data_dir = get_data_dir()
    for artifact in job.artifacts:
        if artifact.path.endswith(suffix):
            candidate = data_dir / artifact.path
            if candidate.exists():
                return candidate
    if job.metadata is None:
        return None
    fallback = get_paper_vault_dir() / job.metadata.slug / suffix
    if fallback.exists():
        return fallback
    return None


def _add_artifact(job: ResearchJob, path: Path) -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "doubts"
            artifact.label = "Doubts scaffold"
            return
    job.artifacts.append(Artifact("doubts", artifact_path, "Doubts scaffold"))
