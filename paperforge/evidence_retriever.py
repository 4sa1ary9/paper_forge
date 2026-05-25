from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_data_dir, get_paper_vault_dir, relative_to_data_dir, save_job


MAX_RESULTS = 5
STOP_WORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "for",
    "from",
    "into",
    "over",
    "section",
    "that",
    "the",
    "this",
    "with",
}


@dataclass(frozen=True)
class IndexedEvidenceChunk:
    chunk_id: str
    page: int
    section_guess: str
    excerpt: str


@dataclass(frozen=True)
class EvidenceSearchResult:
    chunk_id: str
    page: int
    section_guess: str
    score: float
    excerpt: str


def run_evidence_search(job: ResearchJob, query: str) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Evidence search requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "evidence-search.md"

    step = start_step(
        create_step(
            "evidence.search_chunks",
            "Search evidence chunks",
            ["notes/evidence-chunks.md", "evidence search query"],
        )
    )
    job.steps.append(step)

    clean_query = query.strip()
    if not clean_query:
        output_path.write_text(
            _search_markdown(job, clean_query, [], "needs_user_input", "available", "Evidence search query is empty"),
            encoding="utf-8",
        )
        _add_artifact(job, output_path)
        finish_step(step, "needs_user_input", [relative_to_data_dir(output_path)], "Evidence search query is empty")
        job.status = "needs_user_input"
        job.updated_at = now_iso()
        save_job(job)
        return job

    chunks_path = _find_chunks_path(job)
    if chunks_path is None:
        output_path.write_text(
            _search_markdown(job, clean_query, [], "partial", "missing", "Evidence chunks are not available"),
            encoding="utf-8",
        )
        _add_artifact(job, output_path)
        finish_step(step, "partial", [relative_to_data_dir(output_path)], "Evidence chunks are not available")
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    try:
        chunks_markdown = chunks_path.read_text(encoding="utf-8")
        results = search_evidence_chunks(clean_query, chunks_markdown)
        status = "completed" if results else "partial"
        error = None if results else "No matching evidence chunks found"
        output_path.write_text(
            _search_markdown(job, clean_query, results, status, "available", error),
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


def search_evidence_chunks(query: str, chunks_markdown: str, limit: int = MAX_RESULTS) -> list[EvidenceSearchResult]:
    query_terms = _tokens(query)
    if not query_terms:
        return []

    chunks = parse_evidence_chunks(chunks_markdown)
    scored: list[EvidenceSearchResult] = []
    for chunk in chunks:
        score = _score_chunk(query_terms, chunk)
        if score <= 0:
            continue
        scored.append(
            EvidenceSearchResult(
                chunk_id=chunk.chunk_id,
                page=chunk.page,
                section_guess=chunk.section_guess,
                score=round(score, 3),
                excerpt=chunk.excerpt,
            )
        )
    return sorted(scored, key=lambda result: (-result.score, result.page, result.chunk_id))[:limit]


def parse_evidence_chunks(markdown: str) -> list[IndexedEvidenceChunk]:
    chunks: list[IndexedEvidenceChunk] = []
    pattern = re.compile(
        r"^###\s+([A-Za-z0-9-]+)\s*"
        r"\n+- Page:\s+(\d+)\s*"
        r"\n+- Section guess:\s+([^\n]+)\s*"
        r"\n+- Characters:\s+\d+\s*"
        r"\n+```(?:text)?\s*\n(.*?)\n```",
        re.MULTILINE | re.DOTALL,
    )
    for match in pattern.finditer(markdown):
        chunks.append(
            IndexedEvidenceChunk(
                chunk_id=match.group(1).strip(),
                page=int(match.group(2)),
                section_guess=match.group(3).strip(),
                excerpt=_clean_text(match.group(4)),
            )
        )
    return chunks


def _score_chunk(query_terms: list[str], chunk: IndexedEvidenceChunk) -> float:
    text_terms = _tokens(f"{chunk.section_guess} {chunk.excerpt}")
    if not text_terms:
        return 0

    text_counts = Counter(text_terms)
    query_counts = Counter(query_terms)
    score = 0.0
    for term, query_count in query_counts.items():
        term_hits = text_counts.get(term, 0)
        if not term_hits:
            continue
        score += (1 + math.log(term_hits)) * query_count
        if term == chunk.section_guess.lower():
            score += 0.5
    return score


def _search_markdown(
    job: ResearchJob,
    query: str,
    results: list[EvidenceSearchResult],
    status: str,
    chunks_status: str,
    error: str | None,
) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("Evidence search requires paper metadata")

    lines = [
        "# Evidence Search Results",
        "",
        f"- Paper: {metadata.title}",
        f"- Query: `{query}`",
        f"- Search status: {status}",
        f"- Searched at: {now_iso()}",
        f"- Evidence chunks: {chunks_status}",
        "- Scope: local keyword retrieval over evidence chunks; no answer or paper explanation generated.",
    ]
    if error:
        lines.append(f"- Partial reason: {error}")

    lines.extend(
        [
            "",
            "## Result Inventory",
            "",
            *_result_table(results),
            "## Results",
            "",
            *_result_sections(results),
        ]
    )
    return "\n".join(lines)


def _result_table(results: list[EvidenceSearchResult]) -> list[str]:
    lines = [
        "| Chunk ID | Page | Section Guess | Score |",
        "| --- | --- | --- | --- |",
    ]
    if not results:
        lines.append("| - | - | - | No evidence search results generated. |")
        lines.append("")
        return lines

    for result in results:
        lines.append(f"| {result.chunk_id} | {result.page} | {result.section_guess} | {result.score:.3f} |")
    lines.append("")
    return lines


def _result_sections(results: list[EvidenceSearchResult]) -> list[str]:
    if not results:
        return ["No evidence search results generated.", ""]

    lines: list[str] = []
    for result in results:
        lines.extend(
            [
                f"### {result.chunk_id}",
                "",
                f"- Page: {result.page}",
                f"- Section guess: {result.section_guess}",
                f"- Score: {result.score:.3f}",
                f"- Excerpt: {result.excerpt}",
                "",
            ]
        )
    return lines


def _find_chunks_path(job: ResearchJob) -> Path | None:
    data_dir = get_data_dir()
    for artifact in job.artifacts:
        if artifact.path.endswith("notes/evidence-chunks.md"):
            candidate = data_dir / artifact.path
            if candidate.exists():
                return candidate

    if job.metadata is None:
        return None

    fallback = get_paper_vault_dir() / job.metadata.slug / "notes" / "evidence-chunks.md"
    if fallback.exists():
        return fallback
    return None


def _add_artifact(job: ResearchJob, path: Path) -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "evidence_search"
            artifact.label = "Evidence search results"
            return
    job.artifacts.append(Artifact("evidence_search", artifact_path, "Evidence search results"))


def _tokens(value: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 2 and token not in STOP_WORDS
    ]


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
