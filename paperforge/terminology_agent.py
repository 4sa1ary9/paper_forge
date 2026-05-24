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
    text: str


@dataclass(frozen=True)
class TermCandidate:
    term: str
    section: str
    page: int


STOP_TERMS = {
    "Figure Evidence",
    "Manual Review",
    "Not Generated",
    "Paper Overview",
    "Primary Evidence",
    "Primary Method",
    "Primary Experiment",
    "Primary Limitation",
    "Table Result",
}
TRAILING_STOP_WORDS = {"a", "an", "and", "by", "for", "in", "of", "on", "or", "the", "to", "with"}
LOWERCASE_TERM_SUFFIXES = (
    "attention",
    "complexity",
    "encoding",
    "layer",
    "layers",
    "memory",
    "model",
    "models",
    "network",
    "networks",
    "representation",
    "representations",
    "tokenization",
    "translation",
    "translations",
)


def run_terminology_scaffold(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Terminology scaffold requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "terminology.md"

    step = start_step(
        create_step(
            "knowledge.write_terminology",
            "Write terminology scaffold",
            ["metadata", "notes/README.md"],
        )
    )
    job.steps.append(step)

    try:
        output_path.write_text(_terminology_markdown(job), encoding="utf-8")
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


def run_terminology_evidence(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Terminology evidence writing requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "terminology.md"
    evidence_path = notes_dir / "evidence-map.md"
    readme_path = notes_dir / "README.md"

    step = start_step(
        create_step(
            "knowledge.write_terminology_evidence",
            "Write terminology evidence draft",
            ["notes/evidence-map.md", "notes/README.md", "notes/terminology.md"],
        )
    )
    job.steps.append(step)

    missing_inputs = _missing_inputs([evidence_path, readme_path, output_path])
    if missing_inputs:
        finish_step(step, "partial", [], f"Missing terminology evidence inputs: {', '.join(missing_inputs)}")
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    try:
        evidence_pages = _evidence_page_numbers(evidence_path.read_text(encoding="utf-8"))
        evidence_lines = [
            line
            for line in _readme_evidence_lines(readme_path.read_text(encoding="utf-8"))
            if line.page in evidence_pages
        ]
        terms = _term_candidates(evidence_lines)
        if not terms:
            finish_step(step, "partial", [], "No page-backed terminology candidates detected")
            job.status = "partial"
            job.updated_at = now_iso()
            save_job(job)
            return job
        output_path.write_text(_terminology_evidence_markdown(job, terms), encoding="utf-8")
    except Exception as error:
        finish_step(step, "failed", [], str(error))
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    _add_artifact(job, output_path, "Terminology evidence draft")
    finish_step(step, "completed", [relative_to_data_dir(output_path)])
    job.updated_at = now_iso()
    save_job(job)
    return job


def _terminology_markdown(job: ResearchJob) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("Terminology scaffold requires paper metadata")

    source_note = _source_note_link(job)
    lines = [
        "# Terminology",
        "",
        f"- Paper: {metadata.title}",
        "- Draft status: scaffold only; terms not extracted yet.",
        source_note,
        "",
        "## Term Name",
        "",
        "- Category:",
        "- Short explanation:",
        "- Why it matters in this paper:",
        "- Related terms:",
        "- First seen in:",
        "- Follow-up reading:",
        "",
    ]
    return "\n".join(lines)


def _terminology_evidence_markdown(job: ResearchJob, terms: list[TermCandidate]) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("Terminology evidence writing requires paper metadata")

    lines = [
        "# Terminology",
        "",
        f"- Paper: {metadata.title}",
        "- Draft status: terminology evidence MVP; terms require human review.",
        "- Source note: [Paper note](README.md)",
        "- Evidence map: [PDF text evidence map](evidence-map.md)",
        "",
    ]
    for term in terms:
        lines.extend(
            [
                f"## {term.term}",
                "",
                "- Category: evidence-backed candidate",
                f"- Short explanation: Candidate term detected in {term.section} evidence; human explanation required.",
                f"- Why it matters in this paper: It appears in the cited evidence for {term.section}.",
                "- Related terms: needs human review",
                f"- First seen in: `notes/evidence-map.md`, page {term.page}; source section: {term.section}.",
                f"- Follow-up reading: check `notes/README.md` {term.section} and `notes/evidence-map.md` page {term.page}.",
                "",
            ]
        )
    return "\n".join(lines)


def _missing_inputs(paths: list[Path]) -> list[str]:
    return [path.name for path in paths if not path.exists()]


def _evidence_page_numbers(markdown: str) -> set[int]:
    return {int(match.group(1)) for match in re.finditer(r"^### Page (\d+)\s*$", markdown, re.MULTILINE)}


def _readme_evidence_lines(markdown: str) -> list[EvidenceLine]:
    lines: list[EvidenceLine] = []
    current_section = ""
    evidence_pattern = re.compile(r"^- Page (\d+) [^:\n]+ evidence: (.+)$")
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
                    text=_clean_text(match.group(2)),
                )
            )
    return lines


def _term_candidates(lines: list[EvidenceLine]) -> list[TermCandidate]:
    terms: list[TermCandidate] = []
    seen: set[str] = set()
    for line in lines:
        for term in _candidate_terms(line.text):
            normalized = term.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            terms.append(TermCandidate(term=term, section=line.section, page=line.page))
    return terms


def _candidate_terms(text: str) -> list[str]:
    terms: list[str] = []
    patterns = [
        r"\b(?:[A-Z][a-z]+|[A-Z]{2,})(?:[- ][A-Z][A-Za-z]+|[- ][A-Z]{2,}){1,4}\b",
        r"\b[A-Z]{3,}(?:-[A-Z]{2,})?\b",
        rf"\b[a-z]+(?:-[a-z]+)+(?:\s+(?:{'|'.join(LOWERCASE_TERM_SUFFIXES)}))?\b",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            term = _clean_term(match.group(0))
            if _is_valid_term(term):
                terms.append(term)
    return terms


def _clean_term(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip(" .,:;()[]{}")).strip()


def _is_valid_term(term: str) -> bool:
    if len(term) < 3 or len(term) > 80:
        return False
    if term in STOP_TERMS:
        return False
    if term.lower().startswith(("table ", "figure ", "page ")):
        return False
    if term.startswith(("Introduction ", "Background ", "Conclusion ")):
        return False
    if term.split()[-1].lower() in TRAILING_STOP_WORDS:
        return False
    return any(char.isalpha() for char in term)


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


def _add_artifact(job: ResearchJob, path: Path, label: str = "Terminology scaffold") -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "terminology"
            artifact.label = label
            return
    job.artifacts.append(Artifact("terminology", artifact_path, label))
