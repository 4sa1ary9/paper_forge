from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_data_dir, get_paper_vault_dir, relative_to_data_dir, save_job


@dataclass(frozen=True)
class AssessmentSignals:
    has_method: bool
    has_experiment: bool
    has_practical_takeaway: bool
    has_local_code_mapping: bool
    has_code_candidates: bool
    has_risk_evidence: bool


@dataclass(frozen=True)
class InterviewAssessment:
    suitability: str
    evidence_basis: list[str]
    signals: AssessmentSignals


def run_interview_mapping_scaffold(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Interview mapping scaffold requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "interview-project.md"

    step = start_step(
        create_step(
            "project.write_interview_mapping",
            "Write interview project mapping scaffold",
            ["metadata", "notes/README.md", "notes/code-references.md"],
        )
    )
    job.steps.append(step)

    try:
        output_path.write_text(_interview_mapping_markdown(job), encoding="utf-8")
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


def run_interview_mapping_assessment(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Interview mapping assessment requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    readme_path = notes_dir / "README.md"
    code_references_path = notes_dir / "code-references.md"
    doubts_path = notes_dir / "doubts.md"
    mapping_path = notes_dir / "interview-project.md"

    step = start_step(
        create_step(
            "project.assess_interview_mapping",
            "Assess interview project suitability",
            [
                "notes/README.md",
                "notes/code-references.md",
                "notes/doubts.md",
                "notes/interview-project.md",
            ],
        )
    )
    job.steps.append(step)

    missing_inputs = _missing_inputs([readme_path, code_references_path, doubts_path, mapping_path])
    if missing_inputs:
        finish_step(step, "partial", [], f"Missing interview assessment inputs: {', '.join(missing_inputs)}")
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    try:
        readme = readme_path.read_text(encoding="utf-8")
        code_references = code_references_path.read_text(encoding="utf-8")
        doubts = doubts_path.read_text(encoding="utf-8")
        assessment = _assess_interview_project(readme, code_references, doubts)
        mapping_path.write_text(
            _assessment_markdown(job, assessment),
            encoding="utf-8",
        )
    except Exception as error:
        finish_step(step, "failed", [], str(error))
        job.status = "partial"
        job.updated_at = now_iso()
        save_job(job)
        return job

    _add_artifact(job, mapping_path, "Interview project mapping assessment")
    finish_step(step, "completed", [relative_to_data_dir(mapping_path)])
    job.updated_at = now_iso()
    save_job(job)
    return job


def _interview_mapping_markdown(job: ResearchJob) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("Interview mapping scaffold requires paper metadata")

    lines = [
        "# Interview Project Mapping",
        "",
        f"- Paper: {metadata.title}",
        "- Draft status: scaffold only; suitability not assessed yet.",
        _source_note_link(job),
        _code_references_link(job),
        "",
        "## Suitability",
        "",
        "- Suitability: not assessed",
        "",
        "## Why This Can Become a Project",
        "",
        "- Not assessed yet.",
        "",
        "## Why This May Not Be Worth Building",
        "",
        "- Not assessed yet.",
        "",
        "## Minimal Demo Version",
        "",
        "- Not designed yet.",
        "",
        "## Full Version",
        "",
        "- Not designed yet.",
        "",
        "## Technical Highlights",
        "",
        "- Not assessed yet.",
        "",
        "## Risks",
        "",
        "- Not assessed yet.",
        "",
        "## Connection to Existing Projects",
        "",
        "- Not assessed yet.",
        "",
        "## Interview Talking Points",
        "",
        "- Not generated yet.",
        "",
    ]
    return "\n".join(lines)


def _assess_interview_project(readme: str, code_references: str, doubts: str) -> InterviewAssessment:
    signals = AssessmentSignals(
        has_method=_has_page_evidence(_section_body(readme, "Core Method"), "method"),
        has_experiment=_has_page_evidence(_section_body(readme, "Experiments"), "experiment"),
        has_practical_takeaway=_has_generated_section(readme, "Practical Takeaways"),
        has_local_code_mapping="- Mapping status: evidence-backed local scan" in code_references,
        has_code_candidates="Repository URL:" in code_references or "Candidate Code Paths" in code_references,
        has_risk_evidence=_has_generated_section(readme, "Limitations") or _has_doubt_evidence(doubts),
    )

    score = 0
    if signals.has_method:
        score += 2
    if signals.has_experiment:
        score += 1
    if signals.has_practical_takeaway:
        score += 1
    if signals.has_local_code_mapping:
        score += 2
    elif signals.has_code_candidates:
        score += 1
    if signals.has_risk_evidence:
        score -= 1

    if score >= 5 and signals.has_method and signals.has_local_code_mapping:
        suitability = "high"
    elif score >= 3 and signals.has_method:
        suitability = "medium"
    elif score >= 1:
        suitability = "low"
    else:
        suitability = "not recommended"

    evidence_basis: list[str] = []
    if signals.has_method:
        evidence_basis.append("method evidence")
    if signals.has_experiment:
        evidence_basis.append("experiment evidence")
    if signals.has_practical_takeaway:
        evidence_basis.append("practical takeaway evidence")
    if signals.has_local_code_mapping:
        evidence_basis.append("local code mapping evidence")
    elif signals.has_code_candidates:
        evidence_basis.append("code candidate evidence")
    if not evidence_basis:
        evidence_basis.append("insufficient evidence")

    return InterviewAssessment(
        suitability=suitability,
        evidence_basis=evidence_basis,
        signals=signals,
    )


def _assessment_markdown(job: ResearchJob, assessment: InterviewAssessment) -> str:
    metadata = job.metadata
    if metadata is None:
        raise ValueError("Interview mapping assessment requires paper metadata")

    lines = [
        "# Interview Project Mapping",
        "",
        f"- Paper: {metadata.title}",
        "- Draft status: interview assessment MVP; needs human review before interview use.",
        _source_note_link(job),
        _code_references_link(job),
        "",
        "## Suitability",
        "",
        f"- Suitability: {assessment.suitability}",
        f"- Evidence basis: {_evidence_basis_text(assessment.evidence_basis)}.",
        "- Confidence boundary: deterministic MVP assessment, not a final project decision.",
        "",
        "## Why This Can Become a Project",
        "",
        *_project_strength_lines(assessment.signals),
        "",
        "## Why This May Not Be Worth Building",
        "",
        *_project_weakness_lines(assessment.signals),
        "",
        "## Minimal Demo Version",
        "",
        *_minimal_demo_lines(assessment.signals),
        "",
        "## Full Version",
        "",
        "- Full version: not designed in this MVP.",
        "- Next step: only expand after the minimal demo is validated against paper and code evidence.",
        "",
        "## Technical Highlights",
        "",
        *_technical_highlight_lines(assessment.signals),
        "",
        "## Risks",
        "",
        *_risk_lines(assessment.signals),
        "",
        "## Connection to Existing Projects",
        "",
        *_connection_lines(assessment.signals),
        "",
        "## Interview Talking Points",
        "",
        *_talking_point_lines(assessment.suitability, assessment.signals),
        "",
    ]
    return "\n".join(lines)


def _project_strength_lines(signals: AssessmentSignals) -> list[str]:
    lines: list[str] = []
    if signals.has_method:
        lines.append("- Method evidence exists in `notes/README.md`, so the demo can anchor on a paper-backed mechanism.")
    if signals.has_experiment:
        lines.append("- Experiment evidence exists, so evaluation claims can be tied back to paper evidence.")
    if signals.has_local_code_mapping:
        lines.append("- Candidate code evidence: `notes/code-references.md` has local file-level mapping candidates.")
    elif signals.has_code_candidates:
        lines.append("- Code candidate evidence exists, but local implementation mapping still needs confirmation.")
    if not lines:
        lines.append("- No strong project evidence detected yet.")
    return lines


def _project_weakness_lines(signals: AssessmentSignals) -> list[str]:
    lines: list[str] = []
    if not signals.has_local_code_mapping:
        lines.append("- Code mapping is not locally evidence-backed yet, so implementation scope is uncertain.")
    if signals.has_risk_evidence:
        lines.append("- Limitation or doubt evidence exists; final claims need conservative wording.")
    if not signals.has_experiment:
        lines.append("- Experiment evidence is missing or weak, so evaluation design may require manual work.")
    if not lines:
        lines.append("- Main weakness: assessment is still MVP-level and requires human review.")
    return lines


def _minimal_demo_lines(signals: AssessmentSignals) -> list[str]:
    lines = [
        "- Minimal demo scope: implement or present one method slice tied to the Core Method evidence.",
        "- Required proof: link the demo behavior back to `notes/README.md` and keep unsupported claims out.",
    ]
    if signals.has_local_code_mapping:
        lines.append("- Starting point: inspect candidate code paths from `notes/code-references.md` before writing new code.")
    else:
        lines.append("- Starting point: choose the smallest method component manually because local code mapping is not ready.")
    lines.append("- Out of scope: full paper reproduction, benchmark replication, and production-ready deployment.")
    return lines


def _technical_highlight_lines(signals: AssessmentSignals) -> list[str]:
    lines: list[str] = []
    if signals.has_method:
        lines.append("- Explain the paper method using the Core Method evidence instead of broad summary claims.")
    if signals.has_local_code_mapping:
        lines.append("- Show how the selected code path corresponds to the method evidence at file level.")
    if signals.has_experiment:
        lines.append("- Discuss evaluation only where the paper note has experiment evidence.")
    if not lines:
        lines.append("- Technical highlights are not ready; gather method, code, and experiment evidence first.")
    return lines


def _risk_lines(signals: AssessmentSignals) -> list[str]:
    lines: list[str] = []
    if signals.has_risk_evidence:
        lines.append("- Risk: limitation or doubt evidence exists; keep final claims conservative.")
    if not signals.has_local_code_mapping:
        lines.append("- Risk: without local code mapping, implementation effort may be underestimated.")
    lines.append("- Risk: this assessment does not replace manual review of paper claims or repository quality.")
    return lines


def _connection_lines(signals: AssessmentSignals) -> list[str]:
    if signals.has_local_code_mapping:
        return [
            "- Existing code connection: local file-level mapping candidates are available in `notes/code-references.md`.",
            "- Use these paths as reading entry points, not as final proof of implementation correspondence.",
        ]
    if signals.has_code_candidates:
        return [
            "- Existing code connection: repository candidates exist, but they need local scan or manual inspection.",
        ]
    return ["- Existing code connection: not established yet."]


def _talking_point_lines(suitability: str, signals: AssessmentSignals) -> list[str]:
    lines = [
        f"- Positioning: describe this as a `{suitability}` interview project candidate, not as a finished project.",
        "- Evidence story: paper evidence -> code candidate -> minimal demo boundary -> remaining risks.",
    ]
    if signals.has_risk_evidence:
        lines.append("- Be ready to explain what remains uncertain and how you would validate it.")
    return lines


def _evidence_basis_text(evidence_basis: list[str]) -> str:
    return ", ".join(evidence_basis)


def _missing_inputs(paths: list[Path]) -> list[str]:
    return [path.name for path in paths if not path.exists()]


def _section_body(markdown: str, section: str) -> str:
    pattern = re.compile(rf"^## {re.escape(section)}\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(markdown)
    return match.group(1) if match else ""


def _has_page_evidence(section_body: str, evidence_kind: str) -> bool:
    return re.search(rf"- Page \d+ {re.escape(evidence_kind)} evidence:", section_body) is not None


def _has_generated_section(markdown: str, section: str) -> bool:
    body = _section_body(markdown, section)
    return bool(body.strip()) and "Not generated yet." not in body


def _has_doubt_evidence(markdown: str) -> bool:
    return "source:" in markdown or "page evidence" in markdown or "question" in markdown.lower()


def _source_note_link(job: ResearchJob) -> str:
    if _existing_path(job, "notes/README.md"):
        return "- Source note: [Paper note scaffold](README.md)"
    return "- Source note: not available yet"


def _code_references_link(job: ResearchJob) -> str:
    if _existing_path(job, "notes/code-references.md"):
        return "- Code references: [Code references](code-references.md)"
    return "- Code references: not available yet"


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


def _add_artifact(job: ResearchJob, path: Path, label: str = "Interview project mapping scaffold") -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "interview_mapping"
            artifact.label = label
            return
    job.artifacts.append(Artifact("interview_mapping", artifact_path, label))
