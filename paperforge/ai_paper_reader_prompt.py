from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_paper_vault_dir, get_project_root, relative_to_data_dir, save_job


PROJECT_SKILL_PATH = "./docs/PAPER_SKILL.md"
CANONICAL_SKILL_PATH = "C:/Users/Administrator/.codex/skills/neversight-skills_feed-ai-paper-reader/SKILL.md"


@dataclass(frozen=True)
class PromptArtifactStatus:
    relative_path: str
    absolute_path: Path
    present: bool


def run_ai_paper_reader_prompt_pack(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("AI paper reader prompt pack requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "ai-paper-reader-prompt.md"

    step = start_step(
        create_step(
            "note.prepare_ai_paper_reader_prompt",
            "Prepare ai-paper-reader prompt",
            [
                "metadata.json",
                "raw/paper.pdf",
                "notes/README.md",
                "notes/evidence-map.md",
                "images/manifest.md",
            ],
        )
    )
    job.steps.append(step)

    try:
        statuses = _artifact_statuses(paper_dir)
        output_path.write_text(_prompt_markdown(job, paper_dir, statuses), encoding="utf-8")
    except Exception as error:
        finish_step(step, "failed", [], str(error))
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    _add_artifact(job, output_path)
    output = relative_to_data_dir(output_path)
    if any(not status.present for status in statuses):
        finish_step(step, "partial", [output], "Some recommended artifacts are missing")
        job.status = "partial"
    else:
        finish_step(step, "completed", [output])

    job.updated_at = now_iso()
    save_job(job)
    return job


def _artifact_statuses(paper_dir: Path) -> list[PromptArtifactStatus]:
    relative_paths = [
        "metadata.json",
        "raw/paper.pdf",
        "notes/README.md",
        "notes/evidence-map.md",
        "images/manifest.md",
    ]
    return [
        PromptArtifactStatus(
            relative_path=relative_path,
            absolute_path=paper_dir / relative_path,
            present=(paper_dir / relative_path).exists(),
        )
        for relative_path in relative_paths
    ]


def _prompt_markdown(job: ResearchJob, paper_dir: Path, statuses: list[PromptArtifactStatus]) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("AI paper reader prompt pack requires paper metadata")

    project_skill_absolute_path = get_project_root() / "docs" / "PAPER_SKILL.md"
    lines = [
        "# AI Paper Reader Prompt Pack",
        "",
        "Copy the prompt below into another Codex conversation.",
        "",
        "```text",
        "You are Codex. Read this project-local skill file before doing any paper analysis:",
        PROJECT_SKILL_PATH,
        "",
        "Also treat this canonical installed skill path as the source of the same ai-paper-reader instructions:",
        CANONICAL_SKILL_PATH,
        "",
        f"Project-local skill absolute path: {project_skill_absolute_path}",
        "",
        "Use the ai-paper-reader structure: metadata, TL;DR, paper overview, background and motivation, core method, experiments, deep Q&A, summary and reflections.",
        "Generate a professional AI paper reading note from the artifacts below.",
        "Do not invent paper content. If a claim cannot be verified from the listed artifacts, mark it as needs verification.",
        "Missing artifacts must be treated as unavailable, not guessed from memory.",
        "",
        f"Paper workspace: {paper_dir}",
        f"Paper title: {metadata.title}",
        f"Authors: {', '.join(metadata.authors) if metadata.authors else 'Unknown'}",
        f"Year: {metadata.year if metadata.year is not None else 'Unknown'}",
        f"Canonical URL: {metadata.canonical_url or 'not resolved'}",
        "",
        "Artifact inventory:",
        *(_artifact_inventory_lines(statuses)),
        "",
        "Required output sections:",
        "1. Metadata",
        "2. TL;DR",
        "3. Paper overview",
        "4. Background and motivation",
        "5. Core method",
        "6. Experiments",
        "7. Deep Q&A",
        "8. Summary and reflections",
        "",
        "Evidence rules:",
        "- Prefer metadata.json, raw/paper.pdf, notes/README.md, notes/evidence-map.md, and images/manifest.md.",
        "- Use page evidence when notes/evidence-map.md is available.",
        "- Use figure references when images/manifest.md is available.",
        "- Keep uncertain or unsupported statements explicitly marked as needs verification.",
        "```",
        "",
        "## Artifact Inventory",
        "",
        *_artifact_table_lines(statuses),
    ]
    return "\n".join(lines)


def _artifact_inventory_lines(statuses: list[PromptArtifactStatus]) -> list[str]:
    lines: list[str] = []
    for status in statuses:
        marker = "present" if status.present else "missing"
        lines.append(f"- {status.relative_path}: {marker} at {status.absolute_path}")
    return lines


def _artifact_table_lines(statuses: list[PromptArtifactStatus]) -> list[str]:
    lines = [
        "| Artifact | Status | Absolute path |",
        "| --- | --- | --- |",
    ]
    for status in statuses:
        marker = "present" if status.present else "missing"
        lines.append(f"| {status.relative_path} | {marker} | `{status.absolute_path}` |")
    lines.append("")
    return lines


def _add_artifact(job: ResearchJob, path: Path) -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "note"
            artifact.label = "AI Paper Reader Prompt"
            return
    job.artifacts.append(Artifact("note", artifact_path, "AI Paper Reader Prompt"))
