from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_data_dir, get_paper_vault_dir, relative_to_data_dir, save_job


DEFAULT_MAX_CHUNK_CHARS = 900
EMPTY_PAGE_SENTINELS = {
    "No extractable text on this page.",
    "No page text available.",
}


@dataclass(frozen=True)
class EvidenceMapPage:
    page: int
    text: str


@dataclass(frozen=True)
class EvidenceChunk:
    id: str
    page: int
    section_guess: str
    character_count: int
    text: str


def run_evidence_chunk_extraction(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Evidence chunk extraction requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "evidence-chunks.md"

    step = start_step(create_step("pdf.extract_evidence_chunks", "Extract evidence chunks", ["notes/evidence-map.md"]))
    job.steps.append(step)

    evidence_map_path = _find_evidence_map_path(job)
    if evidence_map_path is None:
        output_path.write_text(
            _evidence_chunks_markdown(job, [], "partial", "missing", "Evidence map is not available"),
            encoding="utf-8",
        )
        _add_artifact(job, output_path)
        finish_step(step, "partial", [relative_to_data_dir(output_path)], "Evidence map is not available")
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    try:
        markdown = evidence_map_path.read_text(encoding="utf-8")
        pages = parse_evidence_map_pages(markdown)
        chunks = _build_chunks(pages, DEFAULT_MAX_CHUNK_CHARS)
        empty_pages = [page.page for page in pages if not _is_extractable_page_text(page.text)]
        status = "completed" if chunks and not empty_pages else "partial"
        error = _partial_error(chunks, empty_pages)
        output_path.write_text(
            _evidence_chunks_markdown(job, chunks, status, "available", error),
            encoding="utf-8",
        )
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
        finish_step(step, "partial", outputs, error)
        job.status = "partial"

    job.updated_at = now_iso()
    save_job(job)
    return job


def build_evidence_chunks_from_markdown(markdown: str, max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS) -> list[EvidenceChunk]:
    return _build_chunks(parse_evidence_map_pages(markdown), max_chunk_chars)


def parse_evidence_map_pages(markdown: str) -> list[EvidenceMapPage]:
    pages: list[EvidenceMapPage] = []
    pattern = re.compile(
        r"^### Page\s+(\d+)\s*\n+```(?:text)?\s*\n(.*?)\n```",
        re.MULTILINE | re.DOTALL,
    )
    for match in pattern.finditer(markdown):
        text = match.group(2).strip()
        pages.append(EvidenceMapPage(page=int(match.group(1)), text=text))
    return pages


def guess_section(text: str) -> str:
    lowered = text.lower()
    if _contains_any(lowered, ["limitation", "limitations", "future work", "failure", "constraint", "risk"]):
        return "limitation"
    if _contains_any(lowered, ["experiment", "experiments", "evaluation", "benchmark", "result", "results", "ablation", "table"]):
        return "experiment"
    if _contains_any(
        lowered,
        [
            "method",
            "model",
            "architecture",
            "algorithm",
            "approach",
            "training",
            "objective",
            "attention",
            "encoder",
            "decoder",
        ],
    ):
        return "method"
    if _contains_any(lowered, ["introduction", "background", "motivation", "abstract"]):
        return "introduction"
    return "unknown"


def _build_chunks(pages: list[EvidenceMapPage], max_chunk_chars: int) -> list[EvidenceChunk]:
    chunks: list[EvidenceChunk] = []
    for page in pages:
        page_text = _clean_page_text(page.text)
        if not _is_extractable_page_text(page_text):
            continue
        page_chunks = _split_page_text(page_text, max_chunk_chars)
        last_section_guess = "unknown"
        for chunk_index, chunk_text in enumerate(page_chunks, start=1):
            section_guess = guess_section(chunk_text)
            if section_guess == "unknown":
                section_guess = last_section_guess
            elif section_guess != "unknown":
                last_section_guess = section_guess
            chunks.append(
                EvidenceChunk(
                    id=f"p{page.page:03d}-c{chunk_index:03d}",
                    page=page.page,
                    section_guess=section_guess,
                    character_count=len(chunk_text),
                    text=chunk_text,
                )
            )
    return chunks


def _split_page_text(text: str, max_chunk_chars: int) -> list[str]:
    paragraphs = _merge_section_headings(_paragraphs(text))
    chunks: list[str] = []
    for paragraph in paragraphs:
        chunks.extend(_split_long_paragraph(paragraph, max_chunk_chars))
    return [chunk for chunk in chunks if chunk]


def _paragraphs(text: str) -> list[str]:
    return [_clean_paragraph(part) for part in re.split(r"\n\s*\n+", text) if _clean_paragraph(part)]


def _merge_section_headings(paragraphs: list[str]) -> list[str]:
    merged: list[str] = []
    index = 0
    while index < len(paragraphs):
        paragraph = paragraphs[index]
        if index + 1 < len(paragraphs) and _looks_like_section_heading(paragraph):
            merged.append(f"{paragraph}\n\n{paragraphs[index + 1]}")
            index += 2
            continue
        merged.append(paragraph)
        index += 1
    return merged


def _looks_like_section_heading(text: str) -> bool:
    if len(text) > 80 or re.search(r"[.!?;:]", text):
        return False
    return guess_section(text) != "unknown"


def _split_long_paragraph(paragraph: str, max_chunk_chars: int) -> list[str]:
    if len(paragraph) <= max_chunk_chars:
        return [paragraph]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in paragraph.split():
        extra = len(word) + (1 if current else 0)
        if current and current_len + extra > max_chunk_chars:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
            continue
        current.append(word)
        current_len += extra
    if current:
        chunks.append(" ".join(current))
    return chunks


def _evidence_chunks_markdown(
    job: ResearchJob,
    chunks: list[EvidenceChunk],
    status: str,
    evidence_map_status: str,
    error: str | None,
) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("Evidence chunk extraction requires paper metadata")

    lines = [
        "# Evidence Chunks",
        "",
        f"- Paper: {metadata.title}",
        f"- Extraction status: {status}",
        f"- Extracted at: {now_iso()}",
        "- Source: `notes/evidence-map.md`",
        f"- Evidence map: {evidence_map_status}",
        "- Scope: chunk-level evidence only; no summary or explanation generated.",
        "- Rule: downstream generation should cite chunk ids when available.",
    ]
    if error:
        lines.append(f"- Partial reason: {error}")
    lines.extend(
        [
            "",
            "## Chunk Inventory",
            "",
            *_chunk_inventory_table(chunks),
            "## Chunk Evidence",
            "",
            *_chunk_sections(chunks),
        ]
    )
    return "\n".join(lines)


def _chunk_inventory_table(chunks: list[EvidenceChunk]) -> list[str]:
    lines = [
        "| Chunk ID | Page | Section Guess | Characters |",
        "| --- | --- | --- | --- |",
    ]
    if not chunks:
        lines.append("| - | - | - | No evidence chunks generated. |")
        lines.append("")
        return lines

    for chunk in chunks:
        lines.append(f"| {chunk.id} | {chunk.page} | {chunk.section_guess} | {chunk.character_count} |")
    lines.append("")
    return lines


def _chunk_sections(chunks: list[EvidenceChunk]) -> list[str]:
    if not chunks:
        return ["No evidence chunks generated.", ""]

    lines: list[str] = []
    for chunk in chunks:
        lines.extend(
            [
                f"### {chunk.id}",
                "",
                f"- Page: {chunk.page}",
                f"- Section guess: {chunk.section_guess}",
                f"- Characters: {chunk.character_count}",
                "",
                "```text",
                chunk.text,
                "```",
                "",
            ]
        )
    return lines


def _find_evidence_map_path(job: ResearchJob) -> Path | None:
    data_dir = get_data_dir()
    for artifact in job.artifacts:
        if artifact.path.endswith("notes/evidence-map.md"):
            candidate = data_dir / artifact.path
            if candidate.exists():
                return candidate

    if job.metadata is None:
        return None

    fallback = get_paper_vault_dir() / job.metadata.slug / "notes" / "evidence-map.md"
    if fallback.exists():
        return fallback
    return None


def _add_artifact(job: ResearchJob, path: Path) -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "evidence_chunks"
            artifact.label = "Evidence chunks"
            return
    job.artifacts.append(Artifact("evidence_chunks", artifact_path, "Evidence chunks"))


def _partial_error(chunks: list[EvidenceChunk], empty_pages: list[int]) -> str | None:
    if not chunks:
        return "No evidence chunks generated"
    if empty_pages:
        pages = ", ".join(str(page) for page in empty_pages)
        return f"Some pages had no extractable text: {pages}"
    return None


def _clean_page_text(text: str) -> str:
    return text.strip()


def _clean_paragraph(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _is_extractable_page_text(text: str) -> bool:
    cleaned = text.strip()
    return bool(cleaned) and cleaned not in EMPTY_PAGE_SENTINELS


def _contains_any(text: str, needles: list[str]) -> bool:
    return any(re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", text) for needle in needles)
