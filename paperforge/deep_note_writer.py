from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_paper_vault_dir, relative_to_data_dir, save_job


TARGET_SECTIONS = [
    "TL;DR",
    "Paper Overview",
    "Background and Motivation",
    "Core Method",
    "Experiments",
    "Limitations",
    "Deep Q&A",
    "Practical Takeaways",
]
VISUAL_EVIDENCE_SECTIONS = {"Core Method", "Experiments"}
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


@dataclass(frozen=True)
class FigureEvidence:
    file_name: str
    page: int


def run_deep_note_writing(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Deep note writing requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    readme_path = notes_dir / "README.md"
    plan_path = notes_dir / "deep-note-plan.md"
    evidence_path = notes_dir / "evidence-map.md"
    manifest_path = paper_dir / "images" / "manifest.md"

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
        ready_visual_sections = [section for section in ready_sections if section in VISUAL_EVIDENCE_SECTIONS]
        if ready_visual_sections and not manifest_path.exists():
            finish_step(step, "partial", [], f"Image manifest is required for {ready_visual_sections[0]} writing")
            job.status = "partial"
            job.updated_at = now_iso()
            save_job(job)
            return job
        if ready_visual_sections:
            step.inputs.append("images/manifest.md")

        pages = _content_pages(_evidence_pages(evidence_path.read_text(encoding="utf-8")))
        if not pages:
            finish_step(step, "partial", [], "No page evidence is available for deep note writing")
            job.status = "partial"
            job.updated_at = now_iso()
            save_job(job)
            return job

        figures = (
            _figure_evidence(manifest_path.read_text(encoding="utf-8"))
            if ready_visual_sections
            else []
        )
        readme = _update_draft_status(readme_path.read_text(encoding="utf-8"))
        for section in ready_sections:
            readme = _replace_section(readme, section, _section_lines(section, pages, figures, readme))
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


def _figure_evidence(markdown: str) -> list[FigureEvidence]:
    figures: list[FigureEvidence] = []
    for line in markdown.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() in {"index", "---"}:
            continue
        file_name = cells[1].strip("`")
        if not file_name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue
        try:
            page = int(cells[2])
        except ValueError:
            continue
        figures.append(FigureEvidence(file_name=file_name, page=page))
    return figures


def _content_pages(pages: list[EvidencePage]) -> list[EvidencePage]:
    filtered = [page for page in pages if not _looks_like_boilerplate(page.text)]
    return filtered or pages


def _looks_like_boilerplate(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in BOILERPLATE_MARKERS)


def _section_lines(
    section: str,
    pages: list[EvidencePage],
    figures: list[FigureEvidence] | None = None,
    readme: str = "",
) -> list[str]:
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

    if section == "Background and Motivation":
        background_pages = _background_pages(pages)
        page_list = ", ".join(str(page.page) for page in background_pages)
        lines = [
            f"- Primary background evidence pages: {page_list}.",
        ]
        for page in background_pages:
            lines.append(f"- Page {page.page} motivation evidence: {_evidence_sentence(page.text)}")
        lines.append("- Manual review: confirm these excerpts actually describe the paper background and motivation.")
        return lines

    if section == "Core Method":
        method_pages = _method_pages(pages)
        page_list = ", ".join(str(page.page) for page in method_pages)
        lines = [
            f"- Primary method evidence pages: {page_list}.",
        ]
        for page in method_pages:
            lines.append(f"- Page {page.page} method evidence: {_evidence_sentence(page.text)}")
        lines.append(f"- Figure evidence: `../images/manifest.md` {_figure_summary(figures or [])}.")
        lines.append("- Manual review: confirm these excerpts and figures actually describe the core method.")
        return lines

    if section == "Experiments":
        experiment_pages = _experiment_pages(pages)
        table_pages = _table_result_pages(pages)
        training_pages = _training_detail_pages(pages)
        lines = [
            f"- Primary experiment evidence pages: {_page_list(experiment_pages)}.",
        ]
        for page in experiment_pages:
            lines.append(f"- Page {page.page} experiment evidence: {_evidence_sentence(page.text)}")
        lines.append(f"- Table/result evidence pages: {_page_list_or_note(table_pages)}.")
        lines.append(f"- Training detail evidence pages: {_page_list_or_note(training_pages)}.")
        lines.append(f"- Figure/table evidence: `../images/manifest.md` {_figure_summary(figures or [])}.")
        lines.append("- Manual review: confirm these excerpts and visuals actually describe the experiments.")
        return lines

    if section == "Limitations":
        limitation_pages = _limitation_pages(pages)
        lines = [
            f"- Primary limitation evidence pages: {_page_list(limitation_pages)}.",
        ]
        for page in limitation_pages:
            lines.append(f"- Page {page.page} limitation evidence: {_evidence_sentence(page.text)}")
        lines.append("- Manual review: confirm these excerpts actually describe limitations, risks, or future work.")
        return lines

    if section == "Deep Q&A":
        return _deep_qa_lines(readme)

    if section == "Practical Takeaways":
        return _practical_takeaway_lines(readme)

    overview_pages = pages[:2]
    page_list = ", ".join(str(page.page) for page in overview_pages)
    lines = [
        f"- Primary evidence pages: {page_list}.",
    ]
    for page in overview_pages:
        lines.append(f"- Page {page.page} evidence: {_evidence_sentence(page.text)}")
    lines.append("- Manual review: expand these evidence notes into a real overview before final use.")
    return lines


def _background_pages(pages: list[EvidencePage]) -> list[EvidencePage]:
    preferred = [
        page
        for page in pages
        if _looks_like_background(page.text) and not _looks_like_figure_caption(page.text)
    ]
    if preferred:
        return preferred[:2]

    non_figure_pages = [page for page in pages if not _looks_like_figure_caption(page.text)]
    return (non_figure_pages or pages)[:2]


def _method_pages(pages: list[EvidencePage]) -> list[EvidencePage]:
    preferred = [page for page in pages if _looks_like_core_method(page.text)]
    return (preferred or pages)[:2]


def _experiment_pages(pages: list[EvidencePage]) -> list[EvidencePage]:
    preferred = [
        page
        for page in pages
        if _looks_like_experiment(page.text) and not _looks_like_figure_caption(page.text)
    ]
    if preferred:
        return preferred[:2]

    non_figure_pages = [page for page in pages if not _looks_like_figure_caption(page.text)]
    return (non_figure_pages or pages)[:2]


def _table_result_pages(pages: list[EvidencePage]) -> list[EvidencePage]:
    return [page for page in pages if _looks_like_table_or_result(page.text)][:2]


def _training_detail_pages(pages: list[EvidencePage]) -> list[EvidencePage]:
    return [page for page in pages if _looks_like_training_detail(page.text)][:2]


def _limitation_pages(pages: list[EvidencePage]) -> list[EvidencePage]:
    preferred = [
        page
        for page in pages
        if _looks_like_limitation(page.text) and not _looks_like_figure_caption(page.text)
    ]
    if preferred:
        return preferred[:2]

    non_figure_pages = [page for page in pages if not _looks_like_figure_caption(page.text)]
    return (non_figure_pages or pages)[:2]


def _looks_like_background(text: str) -> bool:
    return _has_marker(text, ["introduction", "motivation", "background"])


def _looks_like_core_method(text: str) -> bool:
    markers = [
        "method",
        "methods",
        "model",
        "models",
        "architecture",
        "architectures",
        "algorithm",
        "algorithms",
        "attention",
        "encoder",
        "encoders",
        "decoder",
        "decoders",
    ]
    return _has_marker(text, markers)


def _looks_like_experiment(text: str) -> bool:
    markers = [
        "experiment",
        "experiments",
        "evaluation",
        "evaluations",
        "benchmark",
        "benchmarks",
        "baseline",
        "baselines",
        "result",
        "results",
        "ablation",
        "ablations",
        "table",
        "tables",
    ]
    return _has_marker(text, markers)


def _looks_like_table_or_result(text: str) -> bool:
    markers = [
        "table",
        "tables",
        "result",
        "results",
        "ablation",
        "ablations",
        "accuracy",
        "accuracies",
        "bleu",
        "score",
        "scores",
    ]
    return _has_marker(text, markers)


def _looks_like_training_detail(text: str) -> bool:
    markers = [
        "training",
        "dataset",
        "datasets",
        "optimizer",
        "optimizers",
        "learning rate",
        "batch",
        "batches",
        "epoch",
        "epochs",
        "hyperparameter",
        "hyperparameters",
    ]
    return _has_marker(text, markers)


def _looks_like_limitation(text: str) -> bool:
    markers = [
        "limitation",
        "limitations",
        "future work",
        "future works",
        "fail",
        "fails",
        "failure",
        "failures",
        "constraint",
        "constraints",
        "risk",
        "risks",
        "drawback",
        "drawbacks",
    ]
    return _has_marker(text, markers)


def _looks_like_figure_caption(text: str) -> bool:
    return _clean_text(text).lower().startswith("figure ")


def _has_marker(text: str, markers: list[str]) -> bool:
    lowered = text.lower()
    return any(
        re.search(rf"(?<![a-z0-9]){re.escape(marker)}(?![a-z0-9])", lowered)
        for marker in markers
    )


def _page_list(pages: list[EvidencePage]) -> str:
    return ", ".join(str(page.page) for page in pages)


def _page_list_or_note(pages: list[EvidencePage]) -> str:
    if not pages:
        return "not detected in page-level excerpts"
    return _page_list(pages)


def _figure_summary(figures: list[FigureEvidence]) -> str:
    if not figures:
        return "has no parsed figure rows; manually inspect it before finalizing this section"

    selected = figures[:2]
    figure_text = " and ".join(f"`{figure.file_name}` from page {figure.page}" for figure in selected)
    return f"lists {figure_text}"


def _deep_qa_lines(readme: str) -> list[str]:
    questions: list[str] = []
    sources = [
        (
            "Core Method",
            "Method question",
            "Which method detail in this evidence still needs manual explanation before finalizing the note?",
        ),
        (
            "Experiments",
            "Experiment question",
            "Which result, baseline, or training setting in this evidence needs verification?",
        ),
        (
            "Limitations",
            "Limitation question",
            "What limitation, risk, or future-work item should be checked before using this paper as project evidence?",
        ),
    ]
    for source_section, label, question in sources:
        page = _first_evidence_page(_section_body(readme, source_section))
        if page is not None:
            questions.append(f"- {label} (source: {source_section}, page {page}): {question}")

    if not questions:
        return [
            "- No generated method, experiment, or limitation evidence notes were available for Deep Q&A.",
            "- Manual review: generate source sections first, then rerun this step.",
        ]

    questions.append("- Manual review: answer these questions only after checking the cited source pages.")
    return questions


def _practical_takeaway_lines(readme: str) -> list[str]:
    lines: list[str] = []
    sources = [
        (
            "Core Method",
            "Method takeaway",
            "Use this evidence as the starting point for explaining the paper's core mechanism.",
        ),
        (
            "Experiments",
            "Experiment takeaway",
            "Verify what was measured before drawing practical conclusions from the result evidence.",
        ),
        (
            "Limitations",
            "Limitation takeaway",
            "Treat this evidence as a constraint or risk to check before applying the method.",
        ),
    ]
    for source_section, label, takeaway in sources:
        page = _first_evidence_page(_section_body(readme, source_section))
        if page is not None:
            lines.append(f"- {label} (source: {source_section}, page {page}): {takeaway}")

    if _has_generated_deep_qa(readme):
        lines.append(
            "- Learning follow-up (source: Deep Q&A): Answer the generated questions before turning these notes "
            "into project or interview claims."
        )

    if not lines:
        return [
            "- No generated method, experiment, limitation, or Deep Q&A evidence notes were available for Practical Takeaways.",
            "- Manual review: generate source sections first, then rerun this step.",
        ]

    lines.append("- Manual review: these takeaways are evidence prompts, not project recommendations.")
    return lines


def _has_generated_deep_qa(readme: str) -> bool:
    body = _section_body(readme, "Deep Q&A")
    if not body.strip():
        return False
    return "source:" in body and "Not generated yet." not in body


def _section_body(markdown: str, section: str) -> str:
    pattern = re.compile(rf"^## {re.escape(section)}\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(markdown)
    return match.group(1) if match else ""


def _first_evidence_page(section_body: str) -> int | None:
    match = re.search(r"- Page (\d+) [^:\n]+ evidence:", section_body)
    return int(match.group(1)) if match else None


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
