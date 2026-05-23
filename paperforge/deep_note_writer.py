from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_paper_vault_dir, relative_to_data_dir, save_job


TARGET_SECTIONS = ["TL;DR", "Paper Overview"]
MAX_EVIDENCE_SENTENCE_CHARS = 220
BOILERPLATE_MARKERS = [
    "provided proper attribution",
    "hereby grants permission",
    "permission to reproduce",
    "copyright",
    "licensed under",
]


@dataclass(frozen=True)
class EvidencePage:
    page: int
    text: str


def run_deep_note_writing(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Deep note writing requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    readme_path = notes_dir / "README.md"
    plan_path = notes_dir / "deep-note-plan.md"
    evidence_path = notes_dir / "evidence-map.md"

    step = start_step(
        create_step(
            "note.write_deep_note_mvp",
            "Write deep note MVP",
            ["notes/deep-note-plan.md", "notes/evidence-map.md", "notes/README.md"],
        )
    )
    job.steps.append(step)

    missing_inputs = _missing_inputs([plan_path, evidence_path, readme_path])
    if missing_inputs:
        finish_step(step, "partial", [], f"Missing deep note writing inputs: {', '.join(missing_inputs)}")
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    try:
        readiness = _section_readiness(plan_path.read_text(encoding="utf-8"))
        ready_sections = [section for section in TARGET_SECTIONS if readiness.get(section) == "ready"]
        if not ready_sections:
            finish_step(step, "partial", [], "No target sections are ready for deep note writing")
            job.status = "partial"
            job.updated_at = now_iso()
            save_job(job)
            return job

        pages = _content_pages(_evidence_pages(evidence_path.read_text(encoding="utf-8")))
        if not pages:
            finish_step(step, "partial", [], "No page evidence is available for deep note writing")
            job.status = "partial"
            job.updated_at = now_iso()
            save_job(job)
            return job

        readme = _update_draft_status(readme_path.read_text(encoding="utf-8"))
        for section in ready_sections:
            readme = _replace_section(readme, section, _section_lines(section, pages))
        readme_path.write_text(readme, encoding="utf-8")
    except Exception as error:
        finish_step(step, "failed", [], str(error))
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    _add_artifact(job, readme_path)
    finish_step(step, "completed", [relative_to_data_dir(readme_path)])
    job.updated_at = now_iso()
    save_job(job)
    return job


def _missing_inputs(paths: list[Path]) -> list[str]:
    return [path.name for path in paths if not path.exists()]


def _section_readiness(markdown: str) -> dict[str, str]:
    readiness: dict[str, str] = {}
    for line in markdown.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        section, status = cells[0], cells[1]
        if section in TARGET_SECTIONS:
            readiness[section] = status
    return readiness


def _evidence_pages(markdown: str) -> list[EvidencePage]:
    pages: list[EvidencePage] = []
    pattern = re.compile(r"^### Page (\d+)\s+```text\s*(.*?)\s*```", re.MULTILINE | re.DOTALL)
    for match in pattern.finditer(markdown):
        text = _clean_text(match.group(2))
        if text and text != "No extractable text on this page.":
            pages.append(EvidencePage(page=int(match.group(1)), text=text))
    return pages


def _content_pages(pages: list[EvidencePage]) -> list[EvidencePage]:
    filtered = [page for page in pages if not _looks_like_boilerplate(page.text)]
    return filtered or pages


def _looks_like_boilerplate(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in BOILERPLATE_MARKERS)


def _section_lines(section: str, pages: list[EvidencePage]) -> list[str]:
    if section == "TL;DR":
        first_page = pages[0]
        return [
            (
                "- Evidence-grounded draft (needs human review): "
                f"{_evidence_sentence(first_page.text)} "
                f"(Evidence: `notes/evidence-map.md`, page {first_page.page})."
            ),
            "- Manual review: confirm this draft against the paper before treating it as final.",
        ]

    overview_pages = pages[:2]
    page_list = ", ".join(str(page.page) for page in overview_pages)
    lines = [
        f"- Primary evidence pages: {page_list}.",
    ]
    for page in overview_pages:
        lines.append(f"- Page {page.page} evidence: {_evidence_sentence(page.text)}")
    lines.append("- Manual review: expand these evidence notes into a real overview before final use.")
    return lines


def _replace_section(markdown: str, section: str, lines: list[str]) -> str:
    replacement_body = "\n".join(lines).rstrip() + "\n\n"
    pattern = re.compile(rf"(^## {re.escape(section)}\n)(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    if pattern.search(markdown):
        return pattern.sub(lambda match: f"{match.group(1)}\n{replacement_body}", markdown, count=1)
    return markdown.rstrip() + f"\n\n## {section}\n\n{replacement_body}"


def _update_draft_status(markdown: str) -> str:
    status = "> Draft status: conservative deep note MVP; full deep explanation not generated yet."
    pattern = re.compile(r"^> Draft status: .*$", re.MULTILINE)
    if pattern.search(markdown):
        return pattern.sub(status, markdown, count=1)
    return markdown.replace("\n", f"\n\n{status}\n", 1)


def _evidence_sentence(text: str) -> str:
    cleaned = _clean_text(text)
    sentence_match = re.match(r"(.+?[.!?])(?:\s|$)", cleaned)
    sentence = sentence_match.group(1) if sentence_match else cleaned
    if len(sentence) <= MAX_EVIDENCE_SENTENCE_CHARS:
        return sentence
    return sentence[:MAX_EVIDENCE_SENTENCE_CHARS].rstrip() + " ..."


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _add_artifact(job: ResearchJob, path: Path) -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "note"
            artifact.label = "Paper note with deep note MVP"
            return
    job.artifacts.append(Artifact("note", artifact_path, "Paper note with deep note MVP"))
