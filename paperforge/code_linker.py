from __future__ import annotations

import re
from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_data_dir, get_paper_vault_dir, relative_to_data_dir, save_job


GITHUB_REPOSITORY_PATTERN = re.compile(
    r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)",
    flags=re.I,
)


def run_code_linking(job: ResearchJob) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Code linking requires paper metadata")

    paper_dir = get_paper_vault_dir() / job.metadata.slug
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    output_path = notes_dir / "code-references.md"

    step = start_step(
        create_step(
            "code.link_repositories",
            "Link code repositories",
            ["metadata.github_candidates", "notes/external-sources.md"],
        )
    )
    job.steps.append(step)

    candidates = _github_candidates(job)
    output_path.write_text(_code_references_markdown(job, candidates), encoding="utf-8")
    _add_artifact(job, output_path)

    outputs = [relative_to_data_dir(output_path)]
    if candidates:
        finish_step(step, "completed", outputs)
    else:
        finish_step(step, "partial", outputs, "No GitHub repository candidates were found")
        job.status = "partial"

    job.updated_at = now_iso()
    save_job(job)
    return job


def _github_candidates(job: ResearchJob) -> list[str]:
    found: list[str] = []
    if job.metadata is not None:
        found.extend(job.metadata.github_candidates)

    source_log = _external_sources_path(job)
    if source_log and source_log.exists():
        found.extend(_extract_github_urls(source_log.read_text(encoding="utf-8")))

    return _deduplicate(found)


def _extract_github_urls(text: str) -> list[str]:
    urls: list[str] = []
    for match in GITHUB_REPOSITORY_PATTERN.finditer(text):
        owner, repo = match.groups()
        urls.append(f"https://github.com/{owner}/{repo}".rstrip(".,)"))
    return urls


def _external_sources_path(job: ResearchJob) -> Path | None:
    data_dir = get_data_dir()
    for artifact in job.artifacts:
        if artifact.path.endswith("notes/external-sources.md"):
            return data_dir / artifact.path

    if job.metadata is None:
        return None
    return get_paper_vault_dir() / job.metadata.slug / "notes" / "external-sources.md"


def _code_references_markdown(job: ResearchJob, candidates: list[str]) -> str:
    title = job.metadata.title if job.metadata else job.input_text
    lines = [
        "# Code References",
        "",
        f"- Paper: {title}",
        "- Clone decision: not cloned",
        "- Reason: first MVP only records candidates; cloning requires user confirmation.",
        "",
        "## Repository Candidates",
        "",
    ]

    if not candidates:
        lines.extend(
            [
                "- No GitHub repository candidates found yet.",
                "",
                "## Next Manual Step",
                "",
                "- Add an official GitHub URL through Source Enrichment or metadata before cloning.",
                "",
            ]
        )
        return "\n".join(lines)

    for index, url in enumerate(candidates, start=1):
        lines.extend(
            [
                f"### Candidate {index}",
                "",
                f"- Repository URL: {url}",
                "- License: not checked",
                "- Main tech stack: not checked",
                "- Core files: not checked",
                "- Method-to-code mapping: not checked",
                "- Reproduction difficulty: not checked",
                "- Suggested reading path: not checked",
                "- Reliability: candidate",
                "",
            ]
        )
    return "\n".join(lines)


def _deduplicate(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for url in urls:
        clean = url.strip().rstrip("/")
        if not clean or clean in seen:
            continue
        seen.add(clean)
        result.append(clean)
    return result


def _add_artifact(job: ResearchJob, path: Path) -> None:
    artifact_path = relative_to_data_dir(path)
    for artifact in job.artifacts:
        if artifact.path == artifact_path:
            artifact.kind = "code_reference"
            artifact.label = "Code references"
            return
    job.artifacts.append(Artifact("code_reference", artifact_path, "Code references"))
