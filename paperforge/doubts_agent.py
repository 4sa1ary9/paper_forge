from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_data_dir, get_paper_vault_dir, relative_to_data_dir, save_job


@dataclass(frozen=True)
class EvidenceLine:
    section: str
    page: int
    kind: str
    text: str


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
    readme_path = notes_dir / "README.md"
    terminology_path = notes_dir / "terminology.md"

    step = start_step(
        create_step(
            "knowledge.write_doubts_evidence",
            "Write doubts evidence draft",
            ["notes/README.md", "notes/terminology.md", "notes/doubts.md"],
        )
    )
    job.steps.append(step)

    missing_inputs = _missing_inputs([readme_path, terminology_path, output_path])
    if missing_inputs:
        finish_step(step, "partial", [], f"Missing doubts evidence inputs: {', '.join(missing_inputs)}")
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    try:
        readme = readme_path.read_text(encoding="utf-8")
        terminology = terminology_path.read_text(encoding="utf-8")
        evidence_lines = _readme_evidence_lines(readme)
        existing_questions = _deep_qa_questions(readme)
        term_questions = _term_questions(terminology)
        if not evidence_lines and not existing_questions and not term_questions:
            finish_step(step, "partial", [], "No evidence-backed doubt sources detected")
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

    method_line = _first_line(evidence_lines, "Core Method")
    experiment_line = _first_line(evidence_lines, "Experiments")
    limitation_line = _first_line(evidence_lines, "Limitations")

    lines = [
        "# Doubts and Follow-up Questions",
        "",
        f"- Paper: {metadata.title}",
        "- Draft status: doubts evidence MVP; questions require human review.",
        "- Source note: [Paper note](README.md)",
        "- Terminology source: [Terminology](terminology.md)",
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
    first_seen_pattern = re.compile(
        r"^- First seen in: `notes/evidence-map\.md`, page (\d+); source section: ([^.]+)\."
    )
    for raw_line in markdown.splitlines():
        if raw_line.startswith("## "):
            current_term = raw_line.removeprefix("## ").strip()
            continue
        match = first_seen_pattern.match(raw_line.strip())
        if match and current_term:
            terms.append(
                TermQuestion(
                    term=current_term,
                    page=int(match.group(1)),
                    source_section=match.group(2).strip(),
                )
            )
    return terms


def _section_body(markdown: str, section: str) -> str:
    pattern = re.compile(rf"^## {re.escape(section)}\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(markdown)
    return match.group(1) if match else ""


def _first_line(lines: list[EvidenceLine], section: str) -> EvidenceLine | None:
    return next((line for line in lines if line.section == section), None)


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
            f"- Term notation check (source: {term.source_section}, page {term.page}): Does `{term.term}` require a formula, variable, or notation explanation?"
            for term in selected
        ),
        "",
    ]


def _implementation_lines(method_line: EvidenceLine | None) -> list[str]:
    if method_line is None:
        return ["- No method evidence was available for implementation follow-up.", ""]
    return [
        (
            f"- Implementation doubt (source: {method_line.section}, page {method_line.page}): "
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
            f"- Experiment doubt (source: {experiment_line.section}, page {experiment_line.page}): "
            "Which metric, baseline, or setup detail must be checked before trusting this result?"
        )
    if limitation_line is not None:
        lines.append(
            f"- Limitation doubt (source: {limitation_line.section}, page {limitation_line.page}): "
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
            f"- Term question (source: {term.source_section}, page {term.page}): What does `{term.term}` mean in this paper?"
            for term in terms[:4]
        ),
        "",
    ]


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
