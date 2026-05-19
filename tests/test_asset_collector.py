import io
import tarfile

from paperforge.asset_collector import run_asset_collection
from paperforge.models import PaperMetadata, ResearchJob


def test_asset_collector_downloads_pdf_source_and_extracts_tex(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    source_bytes = _source_archive_bytes({"main.tex": "\\documentclass{article}\n"})
    downloads = {
        "https://example.test/paper.pdf": b"%PDF-1.7\n",
        "https://example.test/source.tar.gz": source_bytes,
    }

    job = _job(
        pdf_url="https://example.test/paper.pdf",
        source_url="https://example.test/source.tar.gz",
    )

    updated = run_asset_collection(job, downloader=lambda url: downloads[url])

    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    assert (paper_dir / "raw" / "paper.pdf").read_bytes() == b"%PDF-1.7\n"
    assert (paper_dir / "raw" / "source.tar.gz").read_bytes() == source_bytes
    assert (paper_dir / "raw" / "tex-source" / "main.tex").read_text(encoding="utf-8") == (
        "\\documentclass{article}\n"
    )

    steps = {step.id: step for step in updated.steps}
    assert steps["asset.collect_pdf"].state == "completed"
    assert steps["asset.collect_pdf"].inputs == ["metadata.pdf_url"]
    assert steps["asset.collect_source"].state == "completed"
    assert steps["asset.collect_source"].inputs == ["metadata.source_url"]
    assert steps["asset.extract_source"].state == "completed"
    assert steps["asset.extract_source"].inputs == ["raw/source.tar.gz"]

    artifact_paths = {artifact.path for artifact in updated.artifacts}
    assert "paper-vault/sample-paper/raw/paper.pdf" in artifact_paths
    assert "paper-vault/sample-paper/raw/source.tar.gz" in artifact_paths
    assert "paper-vault/sample-paper/raw/tex-source" in artifact_paths
    assert (tmp_path / "jobs" / "job-asset.json").exists()


def test_asset_collector_allows_missing_tex_source_url(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    job = _job(
        pdf_url="https://example.test/paper.pdf",
        source_url=None,
    )

    updated = run_asset_collection(job, downloader=lambda url: b"%PDF-1.7\n")

    steps = {step.id: step for step in updated.steps}
    assert steps["asset.collect_pdf"].state == "completed"
    assert steps["asset.collect_source"].state == "skipped"
    assert steps["asset.extract_source"].state == "skipped"
    assert updated.status == "completed"


def test_asset_collector_records_source_download_failure(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    job = _job(
        pdf_url="https://example.test/paper.pdf",
        source_url="https://example.test/source.tar.gz",
    )

    def downloader(url: str) -> bytes:
        if url.endswith("paper.pdf"):
            return b"%PDF-1.7\n"
        raise RuntimeError("source unavailable")

    updated = run_asset_collection(job, downloader=downloader)

    steps = {step.id: step for step in updated.steps}
    assert steps["asset.collect_pdf"].state == "completed"
    assert steps["asset.collect_source"].state == "failed"
    assert steps["asset.collect_source"].error == "source unavailable"
    assert steps["asset.extract_source"].state == "skipped"
    assert updated.status == "partial"


def _job(pdf_url: str | None, source_url: str | None) -> ResearchJob:
    metadata = PaperMetadata(
        slug="sample-paper",
        title="Sample Paper",
        authors=["Ada Lovelace"],
        year=2026,
        venue="arXiv",
        abstract="A sample paper.",
        canonical_url="https://example.test/abs/sample",
        pdf_url=pdf_url,
        source_url=source_url,
        github_candidates=[],
        created_at="2026-05-18T00:00:00+00:00",
        status="intake_completed",
    )
    return ResearchJob(
        id="job-asset",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )


def _source_archive_bytes(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()
