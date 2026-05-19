from __future__ import annotations

from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_data_dir, get_paper_vault_dir, relative_to_data_dir, save_job


def run_note_writing(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Note writing requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "README.md"

    step = start_step(
        create_step(
            "note.write_readme",
            "Write paper note scaffold",
            [
                "metadata",
                "notes/external-sources.md",
                "images/manifest.md",
                "notes/code-references.md",
            ],
        )
    )
    job.steps.append(step)

    try:
        output_path.write_text(_readme_markdown(job), encoding="utf-8")
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


def _readme_markdown(job: ResearchJob) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("Note writing requires paper metadata")

    evidence_links = _evidence_links(job)
    lines = [
        f"# {metadata.title}",
        "",
        f"> Paper: {metadata.canonical_url or 'not resolved'}",
        f"> Authors: {_authors(metadata.authors)}",
        f"> Venue: {metadata.venue or 'Unknown'}",
        f"> Year: {metadata.year or 'Unknown'}",
        "> Reading time: not estimated",
        "> Difficulty: not assessed",
        "> Prerequisites: not listed",
        "> Draft status: scaffold only; deep explanation not generated yet.",
        "",
        "## TL;DR",
        "",
        "- Not generated yet. This section needs paper-grounded synthesis.",
        "",
        "## Evidence Inventory",
        "",
        *evidence_links,
        "## Paper Overview",
        "",
        "- Not generated yet.",
        "",
        "## Background and Motivation",
        "",
        "- Not generated yet.",
        "",
        "## Core Method",
        "",
        "- Not generated yet.",
        "",
        "## Code Mapping",
        "",
        "- Not generated yet. See code references when available.",
        "",
        "## Experiments",
        "",
        "- Not generated yet. See extracted image manifest when available.",
        "",
        "## Deep Q&A",
        "",
        "- Not generated yet.",
        "",
        "## Limitations",
        "",
        "- Not generated yet.",
        "",
        "## Practical Takeaways",
        "",
        "- Not generated yet.",
        "",
    ]
    return "\n".join(lines)


def _evidence_links(job: ResearchJob) -> list[str]:
    links: list[str] = []
    external_sources = _existing_path(job, "notes/external-sources.md")
    code_references = _existing_path(job, "notes/code-references.md")
    image_manifest = _existing_path(job, "images/manifest.md")

    if external_sources:
        links.append("- [External source log](external-sources.md)")
    if code_references:
        links.append("- [Code references](code-references.md)")
    if image_manifest:
        links.append("- [Extracted image manifest](../images/manifest.md)")
    if not links:
        links.append("- No supporting artifacts found yet.")
    links.append("")
    return links


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


def _authors(authors: list[str]) -> str:
    return ", ".join(authors) if authors else "Unknown"


def _add_artifact(job: ResearchJob, path: Path) -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "note"
            artifact.label = "Paper note scaffold"
            return
    job.artifacts.append(Artifact("note", artifact_path, "Paper note scaffold"))
