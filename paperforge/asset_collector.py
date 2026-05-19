from __future__ import annotations

import tarfile
import urllib.request
from collections.abc import Callable
from pathlib import Path

from paperforge.models import Artifact, ResearchJob
from paperforge.steps import create_step, finish_step, now_iso, start_step
from paperforge.storage import get_paper_vault_dir, relative_to_data_dir, save_job


Downloader = Callable[[str], bytes]


def run_asset_collection(job: ResearchJob, downloader: Downloader | None = None) -> ResearchJob:
    if job.metadata is None:
        raise ValueError("Asset collection requires paper metadata")

    fetch = downloader or download_url
    paper_dir = get_paper_vault_dir() / job.metadata.slug
    raw_dir = paper_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = raw_dir / "paper.pdf"
    source_path = raw_dir / "source.tar.gz"
    tex_source_dir = raw_dir / "tex-source"

    pdf_step = _run_download_step(
        job=job,
        step_id="asset.collect_pdf",
        name="Download PDF",
        url=job.metadata.pdf_url,
        target_path=pdf_path,
        input_name="metadata.pdf_url",
        missing_url_message="No PDF URL in metadata",
        downloader=fetch,
    )
    if pdf_step.state == "completed":
        _add_artifact(job, "pdf", pdf_path, "Paper PDF")

    source_step = _run_download_step(
        job=job,
        step_id="asset.collect_source",
        name="Download TeX source",
        url=job.metadata.source_url,
        target_path=source_path,
        input_name="metadata.source_url",
        missing_url_message="No TeX source URL in metadata",
        downloader=fetch,
    )
    if source_step.state == "completed":
        _add_artifact(job, "tex_source", source_path, "TeX source archive")

    extract_step = _run_extract_step(job, source_path, tex_source_dir)
    if extract_step.state == "completed":
        _add_artifact(job, "tex_source", tex_source_dir, "Extracted TeX source")

    job.status = _asset_collection_status(pdf_step.state, source_step.state, extract_step.state)
    job.updated_at = now_iso()
    save_job(job)
    return job


def download_url(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PaperForgeAgent/0.1 contact=local-dev",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _run_download_step(
    job: ResearchJob,
    step_id: str,
    name: str,
    url: str | None,
    target_path: Path,
    input_name: str,
    missing_url_message: str,
    downloader: Downloader,
):
    step = start_step(create_step(step_id, name, [input_name]))
    job.steps.append(step)

    if target_path.exists():
        finish_step(step, "completed", [relative_to_data_dir(target_path)])
        return step

    if not url:
        finish_step(step, "skipped", [], missing_url_message)
        return step

    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(downloader(url))
    except Exception as error:
        finish_step(step, "failed", [], str(error))
        return step

    finish_step(step, "completed", [relative_to_data_dir(target_path)])
    return step


def _run_extract_step(job: ResearchJob, source_path: Path, tex_source_dir: Path):
    step = start_step(create_step("asset.extract_source", "Extract TeX source", ["raw/source.tar.gz"]))
    job.steps.append(step)

    if tex_source_dir.exists() and any(tex_source_dir.iterdir()):
        finish_step(step, "completed", [relative_to_data_dir(tex_source_dir)])
        return step

    if not source_path.exists():
        finish_step(step, "skipped", [], "Source archive is not available")
        return step

    try:
        tex_source_dir.mkdir(parents=True, exist_ok=True)
        _extract_archive(source_path, tex_source_dir)
    except Exception as error:
        finish_step(step, "failed", [], str(error))
        return step

    finish_step(step, "completed", [relative_to_data_dir(tex_source_dir)])
    return step


def _extract_archive(source_path: Path, target_dir: Path) -> None:
    target_root = target_dir.resolve()
    with tarfile.open(source_path, mode="r:*") as archive:
        for member in archive.getmembers():
            member_path = (target_root / member.name).resolve()
            member_path.relative_to(target_root)
        archive.extractall(target_root, filter="data")


def _add_artifact(job: ResearchJob, kind: str, path: Path, label: str) -> None:
    artifact_path = relative_to_data_dir(path)
    if any(artifact.path == artifact_path for artifact in job.artifacts):
        return
    job.artifacts.append(Artifact(kind, artifact_path, label))


def _asset_collection_status(pdf_state: str, source_state: str, extract_state: str) -> str:
    if pdf_state != "completed":
        return "partial"
    if source_state == "failed" or extract_state == "failed":
        return "partial"
    return "completed"
