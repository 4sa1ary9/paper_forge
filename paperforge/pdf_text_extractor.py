from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_data_dir, get_paper_vault_dir, relative_to_data_dir, save_job


MAX_PAGE_EXCERPT_CHARS = 2000


@dataclass(frozen=True)
class ExtractedPdfPage:
    page: int
    text: str


PdfTextExtractor = Callable[[Path], list[ExtractedPdfPage]]


def run_pdf_text_extraction(
    job: ResearchJob,
    extractor: PdfTextExtractor | None = None,
) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("PDF text extraction requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "evidence-map.md"

    step = start_step(create_step("pdf.extract_text_evidence", "Extract PDF text evidence", ["raw/paper.pdf"]))
    job.steps.append(step)

    pdf_path = _find_pdf_path(job)
    if pdf_path is None:
        output_path.write_text(_evidence_map_markdown(job, [], "partial", "missing"), encoding="utf-8")
        _add_artifact(job, output_path)
        finish_step(step, "partial", [relative_to_data_dir(output_path)], "PDF asset is not available")
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    try:
        pages = (extractor or extract_text_with_pymupdf)(pdf_path)
        status = "completed" if _has_extractable_text(pages) else "partial"
        output_path.write_text(_evidence_map_markdown(job, pages, status, relative_to_data_dir(pdf_path)), encoding="utf-8")
    except Exception as error:
        finish_step(step, "failed", [], str(error))
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    _add_artifact(job, output_path)
    outputs = [relative_to_data_dir(output_path)]
    if status == "completed":
        finish_step(step, "completed", outputs)
    else:
        finish_step(step, "partial", outputs, "No extractable text was found in the PDF")
        job.status = "partial"

    job.updated_at = now_iso()
    save_job(job)
    return job


def extract_text_with_pymupdf(pdf_path: Path) -> list[ExtractedPdfPage]:
    try:
        import pymupdf
    except ImportError as error:
        raise RuntimeError("PyMuPDF is required for PDF text extraction") from error

    pages: list[ExtractedPdfPage] = []
    with pymupdf.open(pdf_path) as document:
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            pages.append(ExtractedPdfPage(page=page_index + 1, text=_clean_text(page.get_text("text") or "")))
    return pages


def _find_pdf_path(job: ResearchJob) -> Path | None:
    data_dir = get_data_dir()
    for artifact in job.artifacts:
        if artifact.kind == "pdf":
            candidate = data_dir / artifact.path
            if candidate.exists():
                return candidate

    if job.metadata is None:
        return None

    fallback = get_paper_vault_dir() / job.metadata.slug / "raw" / "paper.pdf"
    if fallback.exists():
        return fallback
    return None


def _evidence_map_markdown(
    job: ResearchJob,
    pages: list[ExtractedPdfPage],
    status: str,
    pdf_status: str,
) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("PDF text extraction requires paper metadata")

    lines = [
        "# PDF Text Evidence Map",
        "",
        f"- Paper: {metadata.title}",
        f"- Extraction status: {status}",
        f"- Extracted at: {now_iso()}",
        f"- PDF: {pdf_status}",
        "- Scope: raw text evidence only; no summary or explanation generated.",
        "- Rule: downstream notes should cite page numbers from this map.",
        "",
        "## Page Inventory",
        "",
        *_page_inventory_table(pages),
        "## Page Evidence Excerpts",
        "",
        *_page_excerpt_sections(pages),
    ]
    return "\n".join(lines)


def _page_inventory_table(pages: list[ExtractedPdfPage]) -> list[str]:
    lines = [
        "| Page | Characters | Text Available |",
        "| --- | --- | --- |",
    ]
    if not pages:
        lines.append("| - | No PDF text extracted | - |")
        lines.append("")
        return lines

    for page in pages:
        text = _clean_text(page.text)
        available = "yes" if text else "no"
        lines.append(f"| {page.page} | {len(text)} | {available} |")
    lines.append("")
    return lines


def _page_excerpt_sections(pages: list[ExtractedPdfPage]) -> list[str]:
    if not pages:
        return ["- No page text available.", ""]

    lines: list[str] = []
    for page in pages:
        text = _clean_text(page.text)
        excerpt = _excerpt(text)
        lines.extend(
            [
                f"### Page {page.page}",
                "",
                "```text",
                excerpt or "No extractable text on this page.",
                "```",
                "",
            ]
        )
    return lines


def _excerpt(text: str) -> str:
    if len(text) <= MAX_PAGE_EXCERPT_CHARS:
        return text
    return text[:MAX_PAGE_EXCERPT_CHARS].rstrip() + " ..."


def _has_extractable_text(pages: list[ExtractedPdfPage]) -> bool:
    return any(_clean_text(page.text) for page in pages)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _add_artifact(job: ResearchJob, path: Path) -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "evidence_map"
            artifact.label = "PDF text evidence map"
            return
    job.artifacts.append(Artifact("evidence_map", artifact_path, "PDF text evidence map"))
