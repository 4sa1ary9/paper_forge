from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from paperforge.evidence_retriever import IndexedEvidenceChunk, parse_evidence_chunks
from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_data_dir, get_paper_vault_dir, relative_to_data_dir, save_job


@dataclass(frozen=True)
class EvidenceLine:
    section: str
    page: int
    kind: str
    text: str
    chunk_id: str | None = None


@dataclass(frozen=True)
class ExistingQuestion:
    source_section: str
    page: int
    question: str


@dataclass(frozen=True)
class TermQuestion:
    term: str
    source_section: str
    page: int
    chunk_id: str | None = None


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


def run_doubts_evidence(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Doubts evidence writing requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "doubts.md"
    chunks_path = notes_dir / "evidence-chunks.md"
    readme_path = notes_dir / "README.md"
    terminology_path = notes_dir / "terminology.md"

    step = start_step(
        create_step(
            "knowledge.write_doubts_evidence",
            "Write doubts evidence draft",
            ["notes/evidence-chunks.md", "notes/README.md", "notes/terminology.md", "notes/doubts.md"],
        )
    )
    job.steps.append(step)

    if chunks_path.exists():
        missing_inputs = _missing_inputs([terminology_path, output_path])
    else:
        missing_inputs = _missing_inputs([readme_path, terminology_path, output_path])
    if missing_inputs:
        finish_step(step, "partial", [], f"Missing doubts evidence inputs: {', '.join(missing_inputs)}")
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    try:
        terminology = terminology_path.read_text(encoding="utf-8")
        if chunks_path.exists():
            chunks = parse_evidence_chunks(chunks_path.read_text(encoding="utf-8"))
            evidence_lines = _chunk_evidence_lines(chunks)
            existing_questions: list[ExistingQuestion] = []
            term_questions = [term for term in _term_questions(terminology) if term.chunk_id]
            no_sources_error = "No chunk-backed doubt sources detected"
        else:
            readme = readme_path.read_text(encoding="utf-8")
            evidence_lines = _readme_evidence_lines(readme)
            existing_questions = _deep_qa_questions(readme)
            term_questions = _term_questions(terminology)
            no_sources_error = "No evidence-backed doubt sources detected"
        if not evidence_lines and not existing_questions and not term_questions:
            finish_step(step, "partial", [], no_sources_error)
            job.status = "partial"
            job.updated_at = now_iso()
            save_job(job)
            return job
        output_path.write_text(
            _doubts_evidence_markdown(job, evidence_lines, existing_questions, term_questions),
            encoding="utf-8",
        )
    except Exception as error:
        finish_step(step, "failed", [], str(error))
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    _add_artifact(job, output_path, "Doubts evidence draft")
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


def _doubts_evidence_markdown(
    job: ResearchJob,
    evidence_lines: list[EvidenceLine],
    existing_questions: list[ExistingQuestion],
    term_questions: list[TermQuestion],
) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("Doubts evidence writing requires paper metadata")

    method_line = _first_line(evidence_lines, {"Core Method", "method"})
    experiment_line = _first_line(evidence_lines, {"Experiments", "experiment"})
    limitation_line = _first_line(evidence_lines, {"Limitations", "limitation"})

    lines = [
        "# Doubts and Follow-up Questions",
        "",
        f"- Paper: {metadata.title}",
        "- Draft status: doubts evidence MVP; questions require human review.",
        "- Source note: [Paper note](README.md)",
        "- Terminology source: [Terminology](terminology.md)",
        *_evidence_source_lines(evidence_lines, term_questions),
        "",
        "## Open Questions",
        "",
        *_open_question_lines(existing_questions),
        "## Confusing Formulas",
        "",
        *_confusing_formula_lines(term_questions),
        "## Missing Implementation Details",
        "",
        *_implementation_lines(method_line),
        "## Claims That Need Verification",
        "",
        *_verification_lines(experiment_line, limitation_line),
        "## Terminology Questions",
        "",
        *_term_question_lines(term_questions),
        "## Questions to Ask an Interviewer or Mentor",
        "",
        "- Manual review: answer these questions only after checking the cited source pages.",
        "",
    ]
    return "\n".join(lines)


def _missing_inputs(paths: list[Path]) -> list[str]:
    return [path.name for path in paths if not path.exists()]


def _readme_evidence_lines(markdown: str) -> list[EvidenceLine]:
    lines: list[EvidenceLine] = []
    current_section = ""
    evidence_pattern = re.compile(r"^- Page (\d+) ([^:\n]+) evidence: (.+)$")
    for raw_line in markdown.splitlines():
        if raw_line.startswith("## "):
            current_section = raw_line.removeprefix("## ").strip()
            continue
        match = evidence_pattern.match(raw_line.strip())
        if match and current_section:
            lines.append(
                EvidenceLine(
                    section=current_section,
                    page=int(match.group(1)),
                    kind=match.group(2).strip(),
                    text=_clean_text(match.group(3)),
                )
            )
    return lines


def _chunk_evidence_lines(chunks: list[IndexedEvidenceChunk]) -> list[EvidenceLine]:
    target_sections = {"method", "experiment", "limitation"}
    lines: list[EvidenceLine] = []
    for chunk in chunks:
        section = chunk.section_guess.strip()
        if section.lower() not in target_sections:
            continue
        lines.append(
            EvidenceLine(
                section=section,
                page=chunk.page,
                kind="chunk",
                text=chunk.excerpt,
                chunk_id=chunk.chunk_id,
            )
        )
    return lines


def _deep_qa_questions(markdown: str) -> list[ExistingQuestion]:
    questions: list[ExistingQuestion] = []
    body = _section_body(markdown, "Deep Q&A")
    pattern = re.compile(r"^- [^(]+\(source: ([^,]+), page (\d+)\): (.+)$")
    for line in body.splitlines():
        match = pattern.match(line.strip())
        if match:
            questions.append(
                ExistingQuestion(
                    source_section=match.group(1).strip(),
                    page=int(match.group(2)),
                    question=_clean_text(match.group(3)),
                )
            )
    return questions


def _term_questions(markdown: str) -> list[TermQuestion]:
    terms: list[TermQuestion] = []
    current_term = ""
    evidence_map_pattern = re.compile(
        r"^- First seen in: `notes/evidence-map\.md`, page (\d+); source section: ([^.]+)\."
    )
    chunks_pattern = re.compile(
        r"^- First seen in: `notes/evidence-chunks\.md`, chunk `([^`]+)`, page (\d+); source section: ([^.]+)\."
    )
    for raw_line in markdown.splitlines():
        if raw_line.startswith("## "):
            current_term = raw_line.removeprefix("## ").strip()
            continue
        chunk_match = chunks_pattern.match(raw_line.strip())
        if chunk_match and current_term:
            terms.append(
                TermQuestion(
                    term=current_term,
                    page=int(chunk_match.group(2)),
                    source_section=chunk_match.group(3).strip(),
                    chunk_id=chunk_match.group(1).strip(),
                )
            )
            continue
        map_match = evidence_map_pattern.match(raw_line.strip())
        if map_match and current_term:
            terms.append(
                TermQuestion(
                    term=current_term,
                    page=int(map_match.group(1)),
                    source_section=map_match.group(2).strip(),
                )
            )
    return terms


def _section_body(markdown: str, section: str) -> str:
    pattern = re.compile(rf"^## {re.escape(section)}\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(markdown)
    return match.group(1) if match else ""


def _first_line(lines: list[EvidenceLine], sections: set[str]) -> EvidenceLine | None:
    normalized_sections = {section.lower() for section in sections}
    return next((line for line in lines if line.section.lower() in normalized_sections), None)


def _evidence_source_lines(evidence_lines: list[EvidenceLine], term_questions: list[TermQuestion]) -> list[str]:
    if any(line.chunk_id for line in evidence_lines) or any(term.chunk_id for term in term_questions):
        return ["- Evidence chunks: [Paragraph evidence chunks](evidence-chunks.md)"]
    return []


def _open_question_lines(questions: list[ExistingQuestion]) -> list[str]:
    if not questions:
        return ["- No generated Deep Q&A questions were available.", ""]
    return [
        *(
            f"- {_question_label(question.source_section)} (source: {question.source_section}, page {question.page}): {question.question}"
            for question in questions[:3]
        ),
        "",
    ]


def _question_label(source_section: str) -> str:
    if source_section == "Core Method":
        return "Method question"
    if source_section == "Experiments":
        return "Experiment question"
    if source_section == "Limitations":
        return "Limitation question"
    return "Follow-up question"


def _confusing_formula_lines(terms: list[TermQuestion]) -> list[str]:
    if not terms:
        return ["- No evidence-backed terminology entries were available for formula or notation follow-up.", ""]
    selected = terms[:2]
    return [
        *(
            f"- Term notation check (source: {_source_ref(term.source_section, term.page, term.chunk_id)}): Does `{term.term}` require a formula, variable, or notation explanation?"
            for term in selected
        ),
        "",
    ]


def _implementation_lines(method_line: EvidenceLine | None) -> list[str]:
    if method_line is None:
        return ["- No method evidence was available for implementation follow-up.", ""]
    return [
        (
            f"- Implementation doubt (source: {_source_ref(method_line.section, method_line.page, method_line.chunk_id)}): "
            "What concrete implementation detail is still missing for this method evidence?"
        ),
        "",
    ]


def _verification_lines(
    experiment_line: EvidenceLine | None,
    limitation_line: EvidenceLine | None,
) -> list[str]:
    lines: list[str] = []
    if experiment_line is not None:
        lines.append(
            f"- Experiment doubt (source: {_source_ref(experiment_line.section, experiment_line.page, experiment_line.chunk_id)}): "
            "Which metric, baseline, or setup detail must be checked before trusting this result?"
        )
    if limitation_line is not None:
        lines.append(
            f"- Limitation doubt (source: {_source_ref(limitation_line.section, limitation_line.page, limitation_line.chunk_id)}): "
            "What condition could make this limitation important in practice?"
        )
    if not lines:
        lines.append("- No experiment or limitation evidence was available for verification follow-up.")
    lines.append("")
    return lines


def _term_question_lines(terms: list[TermQuestion]) -> list[str]:
    if not terms:
        return ["- No evidence-backed terminology entries were available.", ""]
    return [
        *(
            f"- Term question (source: {_source_ref(term.source_section, term.page, term.chunk_id)}): What does `{term.term}` mean in this paper?"
            for term in terms[:4]
        ),
        "",
    ]


def _source_ref(section: str, page: int, chunk_id: str | None) -> str:
    if chunk_id:
        return f"{section}, chunk `{chunk_id}`, page {page}"
    return f"{section}, page {page}"


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


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


def _add_artifact(job: ResearchJob, path: Path, label: str = "Doubts scaffold") -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "doubts"
            artifact.label = label
            return
    job.artifacts.append(Artifact("doubts", artifact_path, label))
