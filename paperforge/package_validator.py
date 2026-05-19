from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_paper_vault_dir, relative_to_data_dir, save_job


@dataclass(frozen=True)
class PackageCheck:
    label: str
    relative_path: str
    requirement: str
    present: bool


REQUIRED_ARTIFACTS = [
    ("Metadata", "metadata.json"),
    ("External source log", "notes/external-sources.md"),
    ("Code references", "notes/code-references.md"),
    ("Paper note", "notes/README.md"),
    ("Terminology", "notes/terminology.md"),
    ("Doubts", "notes/doubts.md"),
    ("Interview mapping", "notes/interview-project.md"),
]

RECOMMENDED_ARTIFACTS = [
    ("Paper PDF", "raw/paper.pdf"),
    ("Image manifest", "images/manifest.md"),
]

OPTIONAL_ARTIFACTS = [
    ("TeX source archive", "raw/source.tar.gz"),
    ("Extracted TeX source", "raw/tex-source"),
]


def run_package_validation(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Package validation requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "package-status.md"

    step = start_step(
        create_step(
            "package.validate_research_package",
            "Validate research package",
            ["paper workspace"],
        )
    )
    job.steps.append(step)

    try:
        checks = _package_checks(paper_dir)
        output_path.write_text(_package_status_markdown(job, checks), encoding="utf-8")
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
    if missing_required:
        finish_step(step, "partial", outputs, "Research package is missing required artifacts")
        job.status = "partial"
    elif missing_recommended:
        finish_step(step, "partial", outputs, "Research package has warnings")
        job.status = "partial"
    else:
        finish_step(step, "completed", outputs)

    job.updated_at = now_iso()
    save_job(job)
    return job


def _package_checks(paper_dir: Path) -> list[PackageCheck]:
    checks: list[PackageCheck] = []
    checks.extend(_checks_for(paper_dir, REQUIRED_ARTIFACTS, "required"))
    checks.extend(_checks_for(paper_dir, RECOMMENDED_ARTIFACTS, "recommended"))
    checks.extend(_checks_for(paper_dir, OPTIONAL_ARTIFACTS, "optional"))
    return checks


def _checks_for(
    paper_dir: Path,
    artifacts: list[tuple[str, str]],
    requirement: str,
) -> list[PackageCheck]:
    return [
        PackageCheck(
            label=label,
            relative_path=relative_path,
            requirement=requirement,
            present=(paper_dir / relative_path).exists(),
        )
        for label, relative_path in artifacts
    ]


def _package_status_markdown(job: ResearchJob, checks: list[PackageCheck]) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("Package validation requires paper metadata")

    missing_required = _missing(checks, "required")
    missing_recommended = _missing(checks, "recommended")
    package_status = "partial" if missing_required or missing_recommended else "complete"

    lines = [
        "# Research Package Status",
        "",
        f"- Paper: {metadata.title}",
        f"- Package status: {package_status}",
        f"- Validated at: {now_iso()}",
        "- Scope: file presence only; content quality not assessed.",
        "",
        "## Required Artifacts",
        "",
        *_checks_table(_checks_by_requirement(checks, "required")),
        "## Recommended Artifacts",
        "",
        *_checks_table(_checks_by_requirement(checks, "recommended")),
        "## Optional Artifacts",
        "",
        *_checks_table(_checks_by_requirement(checks, "optional")),
        "## Missing Required",
        "",
        *_missing_lines(missing_required, "required"),
        "## Warnings",
        "",
        *_missing_lines(missing_recommended, "recommended"),
        "## Optional Missing",
        "",
        *_missing_lines(_missing(checks, "optional"), "optional"),
    ]
    return "\n".join(lines)


def _checks_table(checks: list[PackageCheck]) -> list[str]:
    lines = [
        "| Item | Path | Requirement | Status |",
        "| --- | --- | --- | --- |",
    ]
    for check in checks:
        status = "present" if check.present else "missing"
        lines.append(f"| {check.label} | `{check.relative_path}` | {check.requirement} | {status} |")
    lines.append("")
    return lines


def _checks_by_requirement(checks: list[PackageCheck], requirement: str) -> list[PackageCheck]:
    return [check for check in checks if check.requirement == requirement]


def _missing(checks: list[PackageCheck], requirement: str) -> list[PackageCheck]:
    return [check for check in checks if check.requirement == requirement and not check.present]


def _missing_lines(checks: list[PackageCheck], requirement: str) -> list[str]:
    if not checks:
        label = "warnings" if requirement == "recommended" else f"missing {requirement} artifacts"
        return [f"No {label}.", ""]

    lines: list[str] = []
    for check in checks:
        lines.append(f"- Missing {requirement} artifact: `{check.relative_path}`.")
    lines.append("")
    return lines


def _add_artifact(job: ResearchJob, path: Path) -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "package_status"
            artifact.label = "Research package status"
            return
    job.artifacts.append(Artifact("package_status", artifact_path, "Research package status"))
