from __future__ import annotations

import json
import os
from pathlib import Path

from paperforge.models import AgentStep, Artifact, PaperMetadata, ResearchJob, to_dict


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_data_dir() -> Path:
    configured = os.getenv("PAPERFORGE_DATA_DIR", ".paperforge-data")
    return (get_project_root() / configured).resolve()


def get_paper_vault_dir() -> Path:
    return get_data_dir() / "paper-vault"


def get_jobs_dir() -> Path:
    return get_data_dir() / "jobs"


def ensure_storage() -> None:
    get_jobs_dir().mkdir(parents=True, exist_ok=True)
    get_paper_vault_dir().mkdir(parents=True, exist_ok=True)


def save_job(job: ResearchJob) -> None:
    ensure_storage()
    path = get_jobs_dir() / f"{job.id}.json"
    path.write_text(json.dumps(to_dict(job), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def list_jobs() -> list[ResearchJob]:
    ensure_storage()
    jobs: list[ResearchJob] = []
    for path in get_jobs_dir().glob("*.json"):
        jobs.append(research_job_from_dict(json.loads(path.read_text(encoding="utf-8"))))
    return sorted(jobs, key=lambda job: job.created_at, reverse=True)


def relative_to_data_dir(path: Path) -> str:
    return path.resolve().relative_to(get_data_dir()).as_posix()


def research_job_from_dict(data: dict) -> ResearchJob:
    metadata_data = data.get("metadata")
    metadata = paper_metadata_from_dict(metadata_data) if isinstance(metadata_data, dict) else None

    return ResearchJob(
        id=data.get("id", ""),
        input_text=data.get("input_text") or data.get("input") or "",
        status=data.get("status", "partial"),
        paper_slug=data.get("paper_slug") or data.get("paperSlug"),
        created_at=data.get("created_at") or data.get("createdAt") or "",
        updated_at=data.get("updated_at") or data.get("updatedAt") or "",
        metadata=metadata,
        steps=[agent_step_from_dict(item) for item in data.get("steps", [])],
        artifacts=[artifact_from_dict(item) for item in data.get("artifacts", [])],
    )


def paper_metadata_from_dict(data: dict) -> PaperMetadata:
    return PaperMetadata(
        slug=data.get("slug", ""),
        title=data.get("title", ""),
        authors=data.get("authors", []),
        year=data.get("year"),
        venue=data.get("venue"),
        abstract=data.get("abstract"),
        canonical_url=data.get("canonical_url") or data.get("canonicalUrl"),
        pdf_url=data.get("pdf_url") or data.get("pdfUrl"),
        source_url=data.get("source_url") or data.get("sourceUrl"),
        github_candidates=data.get("github_candidates") or data.get("githubCandidates") or [],
        created_at=data.get("created_at") or data.get("createdAt") or "",
        status=data.get("status", "intake_partial"),
    )


def agent_step_from_dict(data: dict) -> AgentStep:
    return AgentStep(
        id=data.get("id", ""),
        name=data.get("name", ""),
        state=data.get("state", "partial"),
        inputs=data.get("inputs", []),
        outputs=data.get("outputs", []),
        started_at=data.get("started_at") or data.get("startedAt"),
        ended_at=data.get("ended_at") or data.get("endedAt"),
        error=data.get("error"),
    )


def artifact_from_dict(data: dict) -> Artifact:
    return Artifact(
        kind=data.get("kind", "note"),
        path=data.get("path", ""),
        label=data.get("label", ""),
    )
