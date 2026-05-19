from __future__ import annotations

import json
import uuid
from pathlib import Path

from paperforge.arxiv_client import resolve_paper_metadata
from paperforge.models import Artifact, PaperMetadata, ResearchJob
from paperforge.slug import slugify_title
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import (
    get_paper_vault_dir,
    relative_to_data_dir,
    save_job,
)


def run_paper_intake(input_text: str) -> ResearchJob:
    created_at = now_iso()
    job = ResearchJob(
        id=str(uuid.uuid4()),
        input_text=input_text,
        status="running",
        paper_slug=None,
        created_at=created_at,
        updated_at=created_at,
        metadata=None,
        steps=[
            create_step("intake.resolve_identity", "Resolve paper identity", ["user input"]),
            create_step("workspace.create_paper_folder", "Create paper workspace", ["paper metadata"]),
            create_step("workspace.write_metadata", "Write metadata artifact", ["paper workspace"]),
        ],
        artifacts=[],
    )

    step = start_step(job.steps[0])
    try:
        metadata = resolve_paper_metadata(input_text)
        finish_step(step, "completed", ["arXiv metadata"])
    except Exception as error:
        metadata = _fallback_metadata(input_text, error)
        finish_step(step, "partial", ["fallback metadata"], str(error))

    job.metadata = metadata
    job.paper_slug = metadata.slug

    paper_dir = get_paper_vault_dir() / metadata.slug
    raw_dir = paper_dir / "raw"
    images_dir = paper_dir / "images"
    notes_dir = paper_dir / "notes"

    step = start_step(job.steps[1])
    raw_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    notes_dir.mkdir(parents=True, exist_ok=True)
    finish_step(step, "completed", [relative_to_data_dir(paper_dir)])

    step = start_step(job.steps[2])
    metadata_path = paper_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(_metadata_to_json(metadata), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    external_sources_path = notes_dir / "external-sources.md"
    external_sources_path.write_text(_external_sources_markdown(metadata), encoding="utf-8")

    job.artifacts = [
        Artifact("metadata", relative_to_data_dir(metadata_path), "Paper metadata"),
        Artifact("note", relative_to_data_dir(external_sources_path), "External source log"),
    ]
    finish_step(step, "completed", [artifact.path for artifact in job.artifacts])

    job.status = "completed" if metadata.status == "intake_completed" else "partial"
    job.updated_at = now_iso()
    save_job(job)
    return job


def _fallback_metadata(input_text: str, error: Exception) -> PaperMetadata:
    title = input_text.strip()
    return PaperMetadata(
        slug=slugify_title(title),
        title=title,
        authors=[],
        year=None,
        venue=None,
        abstract=f"Metadata resolution needs review: {error}",
        canonical_url=None,
        pdf_url=None,
        source_url=None,
        github_candidates=[],
        created_at=now_iso(),
        status="intake_partial",
    )


def _metadata_to_json(metadata: PaperMetadata) -> dict:
    return {
        "slug": metadata.slug,
        "title": metadata.title,
        "authors": metadata.authors,
        "year": metadata.year,
        "venue": metadata.venue,
        "abstract": metadata.abstract,
        "canonical_url": metadata.canonical_url,
        "pdf_url": metadata.pdf_url,
        "source_url": metadata.source_url,
        "github_candidates": metadata.github_candidates,
        "created_at": metadata.created_at,
        "status": metadata.status,
    }


def _external_sources_markdown(metadata: PaperMetadata) -> str:
    lines = [
        "# External Sources",
        "",
        "## Canonical Paper",
        "",
        f"- Title: {metadata.title}",
        f"- URL: {metadata.canonical_url or 'not resolved'}",
        f"- PDF: {metadata.pdf_url or 'not resolved'}",
        f"- TeX Source: {metadata.source_url or 'not resolved'}",
        "- Reliability: official",
        "",
    ]
    return "\n".join(lines)

