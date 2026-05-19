from __future__ import annotations

from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_data_dir, get_paper_vault_dir, relative_to_data_dir, save_job


def run_source_enrichment(
    job: ResearchJob,
    user_source_urls: list[str] | None = None,
) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Source enrichment requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "external-sources.md"

    step = start_step(
        create_step(
            "source.enrich_external_sources",
            "Enrich external sources",
            ["metadata", "artifacts", "user source URLs"],
        )
    )
    job.steps.append(step)

    try:
        output_path.write_text(
            _external_sources_markdown(job, user_source_urls or []),
            encoding="utf-8",
        )
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


def _external_sources_markdown(job: ResearchJob, user_source_urls: list[str]) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("Source enrichment requires paper metadata")

    lines = [
        "# External Sources",
        "",
        "## Canonical Paper",
        "",
        f"- Title: {metadata.title}",
        f"- URL: {metadata.canonical_url or 'not resolved'}",
        f"- PDF URL: {metadata.pdf_url or 'not resolved'}",
        f"- TeX Source URL: {metadata.source_url or 'not resolved'}",
        "- Source type: paper",
        "- Why useful: primary source for all downstream notes and verification.",
        "- Key points: not extracted yet.",
        "- Reliability: official",
        "",
        "## Local Asset Status",
        "",
        f"- PDF: {_pdf_status(job)}",
        f"- TeX Source: {_tex_source_status(job)}",
        "- Fallback: continue with PDF-based processing.",
        "",
        "## User Provided Sources",
        "",
    ]

    cleaned_urls = [url.strip() for url in user_source_urls if url.strip()]
    if not cleaned_urls:
        lines.append("- No user-provided external sources yet.")
        lines.append("")
        return "\n".join(lines)

    for index, url in enumerate(cleaned_urls, start=1):
        lines.extend(
            [
                f"### Source {index}",
                "",
                f"- URL: {url}",
                "- Source type: external",
                "- Why useful: user-provided candidate for later reading.",
                "- Key points: not extracted yet.",
                "- Reliability: unknown",
                "",
            ]
        )
    return "\n".join(lines)


def _pdf_status(job: ResearchJob) -> str:
    path = _first_existing_artifact_path(job, "pdf")
    if path:
        return f"available at `{path}`"

    if job.metadata is not None:
        fallback = get_paper_vault_dir() / job.metadata.slug / "raw" / "paper.pdf"
        if fallback.exists():
            return f"available at `{relative_to_data_dir(fallback)}`"
    return "missing"


def _tex_source_status(job: ResearchJob) -> str:
    tex_dir = _first_existing_artifact_path(job, "tex_source", path_suffix="tex-source")
    if tex_dir:
        return f"available at `{tex_dir}`"

    archive = _first_existing_artifact_path(job, "tex_source", path_suffix="source.tar.gz")
    if archive:
        return f"archive available at `{archive}`"

    if job.metadata and job.metadata.source_url:
        return "not collected yet"
    return "unavailable"


def _first_existing_artifact_path(job: ResearchJob, kind: str, path_suffix: str | None = None) -> str | None:
    data_dir = get_data_dir()
    for artifact in job.artifacts:
        if artifact.kind != kind:
            continue
        if path_suffix and not artifact.path.endswith(path_suffix):
            continue
        if (data_dir / artifact.path).exists():
            return artifact.path
    return None


def _add_artifact(job: ResearchJob, path: Path) -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "note"
            artifact.label = "External source log"
            return
    job.artifacts.append(Artifact("note", artifact_path, "External source log"))
