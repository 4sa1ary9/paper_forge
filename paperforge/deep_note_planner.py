from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_paper_vault_dir, relative_to_data_dir, save_job


@dataclass(frozen=True)
class ReadinessInput:
    label: str
    relative_path: str
    requirement: str
    present: bool


@dataclass(frozen=True)
class SectionReadiness:
    section: str
    status: str
    evidence: str


READINESS_INPUTS = [
    ("Package status", "notes/package-status.md", "required"),
    ("Paper note scaffold", "notes/README.md", "required"),
    ("Paper PDF", "raw/paper.pdf", "recommended"),
    ("PDF text evidence map", "notes/evidence-map.md", "recommended"),
    ("Image manifest", "images/manifest.md", "recommended"),
    ("External source log", "notes/external-sources.md", "recommended"),
    ("Code references", "notes/code-references.md", "recommended"),
]


def run_deep_note_planning(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Deep note planning requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "deep-note-plan.md"

    step = start_step(
        create_step(
            "note.plan_deep_note",
            "Plan deep note readiness",
            [
                "notes/package-status.md",
                "notes/README.md",
                "raw/paper.pdf",
                "notes/evidence-map.md",
                "images/manifest.md",
            ],
        )
    )
    job.steps.append(step)

    try:
        checks = _readiness_inputs(paper_dir)
        output_path.write_text(_deep_note_plan_markdown(job, checks), encoding="utf-8")
    except Exception as error:
        finish_step(step, "failed", [], str(error))
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    _add_artifact(job, output_path)
    outputs = [relative_to_data_dir(output_path)]
    missing_required = _missing(checks, "required")
    missing_recommended = _missing(checks, "recommended")
    if missing_required or missing_recommended:
        finish_step(step, "partial", outputs, "Deep note plan has missing readiness inputs")
        job.status = "partial"
    else:
        finish_step(step, "completed", outputs)

    job.updated_at = now_iso()
    save_job(job)
    return job


def _readiness_inputs(paper_dir: Path) -> list[ReadinessInput]:
    return [
        ReadinessInput(
            label=label,
            relative_path=relative_path,
            requirement=requirement,
            present=(paper_dir / relative_path).exists(),
        )
        for label, relative_path, requirement in READINESS_INPUTS
    ]


def _deep_note_plan_markdown(job: ResearchJob, checks: list[ReadinessInput]) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("Deep note planning requires paper metadata")

    missing_required = _missing(checks, "required")
    missing_recommended = _missing(checks, "recommended")
    planner_status = "partial" if missing_required or missing_recommended else "ready"

    lines = [
        "# Deep Note Plan",
        "",
        f"- Paper: {metadata.title}",
        f"- Planner status: {planner_status}",
        f"- Planned at: {now_iso()}",
        "- Scope: readiness gate only; deep explanation not generated.",
        "- Rule: only sections marked ready should enter later LLM generation.",
        "",
        "## Readiness Inputs",
        "",
        *_inputs_table(checks),
        "## Section Readiness",
        "",
        *_sections_table(_section_readiness(checks)),
        "## Missing Readiness Inputs",
        "",
        *_missing_lines(missing_required, "required"),
        *_missing_lines(missing_recommended, "recommended"),
        "## Next Generation Order",
        "",
        "1. TL;DR",
        "2. Paper Overview",
        "3. Background and Motivation",
        "4. Core Method",
        "5. Experiments",
        "6. Limitations",
        "7. Code Mapping after repository evidence is reviewed",
        "8. Deep Q&A after method, experiment, and limitation notes exist",
        "9. Practical Takeaways after Deep Q&A evidence notes exist",
        "",
    ]
    return "\n".join(lines)


def _inputs_table(checks: list[ReadinessInput]) -> list[str]:
    lines = [
        "| Item | Path | Requirement | Status |",
        "| --- | --- | --- | --- |",
    ]
    for check in checks:
        status = "present" if check.present else "missing"
        lines.append(f"| {check.label} | `{check.relative_path}` | {check.requirement} | {status} |")
    lines.append("")
    return lines


def _sections_table(sections: list[SectionReadiness]) -> list[str]:
    lines = [
        "| Section | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for section in sections:
        lines.append(f"| {section.section} | {section.status} | {section.evidence} |")
    lines.append("")
    return lines


def _section_readiness(checks: list[ReadinessInput]) -> list[SectionReadiness]:
    has_pdf = _present(checks, "raw/paper.pdf")
    has_evidence_map = _present(checks, "notes/evidence-map.md")
    has_manifest = _present(checks, "images/manifest.md")
    has_sources = _present(checks, "notes/external-sources.md")
    has_code = _present(checks, "notes/code-references.md")

    return [
        SectionReadiness("TL;DR", _ready(has_pdf and has_evidence_map), "metadata, PDF text evidence map"),
        SectionReadiness("Paper Overview", _ready(has_pdf and has_evidence_map), "PDF text evidence map"),
        SectionReadiness(
            "Background and Motivation",
            _ready(has_evidence_map and has_sources),
            "PDF text evidence map, external source log",
        ),
        SectionReadiness(
            "Core Method",
            _ready(has_evidence_map and has_manifest),
            "PDF text evidence map, image manifest",
        ),
        SectionReadiness(
            "Code Mapping",
            "review-ready" if has_code else "blocked",
            "code references; clone still requires user confirmation",
        ),
        SectionReadiness("Experiments", _ready(has_evidence_map and has_manifest), "PDF text evidence map, image manifest"),
        SectionReadiness(
            "Deep Q&A",
            _ready(has_evidence_map and has_manifest),
            "generated method, experiment, and limitation evidence notes",
        ),
        SectionReadiness("Limitations", _ready(has_evidence_map), "PDF text evidence map"),
        SectionReadiness(
            "Practical Takeaways",
            _ready(has_evidence_map and has_manifest),
            "generated method, experiment, limitation, and Deep Q&A evidence notes",
        ),
    ]


def _ready(condition: bool) -> str:
    return "ready" if condition else "blocked"


def _present(checks: list[ReadinessInput], relative_path: str) -> bool:
    return any(check.relative_path == relative_path and check.present for check in checks)


def _missing(checks: list[ReadinessInput], requirement: str) -> list[ReadinessInput]:
    return [check for check in checks if check.requirement == requirement and not check.present]


def _missing_lines(checks: list[ReadinessInput], requirement: str) -> list[str]:
    if not checks:
        if requirement == "required":
            return ["No missing readiness inputs.", ""]
        return []

    return [
        *(f"- Missing {requirement} readiness input: `{check.relative_path}`." for check in checks),
        "",
    ]


def _add_artifact(job: ResearchJob, path: Path) -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "note"
            artifact.label = "Deep note plan"
            return
    job.artifacts.append(Artifact("note", artifact_path, "Deep note plan"))
