from pathlib import Path

from paperforge.models import Artifact, PaperMetadata, ResearchJob
from paperforge.pdf_image_extractor import ExtractedPdfImage, run_pdf_image_extraction


def test_pdf_image_extractor_writes_images_manifest_and_artifacts(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    raw_dir = paper_dir / "raw"
    raw_dir.mkdir(parents=True)
    pdf_path = raw_dir / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n")

    def extractor(pdf_path: Path, images_dir: Path) -> list[ExtractedPdfImage]:
        image_path = images_dir / "fig001_page1_img1.png"
        image_path.write_bytes(b"png bytes")
        return [
            ExtractedPdfImage(
                path=image_path,
                page=1,
                width=640,
                height=480,
                source_xref=42,
            )
        ]

    job = _job()
    job.artifacts.append(Artifact("pdf", "paper-vault/sample-paper/raw/paper.pdf", "Paper PDF"))

    updated = run_pdf_image_extraction(job, extractor=extractor)

    image_path = paper_dir / "images" / "fig001_page1_img1.png"
    manifest_path = paper_dir / "images" / "manifest.md"
    assert image_path.read_bytes() == b"png bytes"
    manifest = manifest_path.read_text(encoding="utf-8")
    assert "# Extracted Figures" in manifest
    assert "| 1 | `fig001_page1_img1.png` | 1 | 640x480 | 42 |" in manifest

    step = updated.steps[-1]
    assert step.id == "pdf.extract_images"
    assert step.state == "completed"
    assert step.inputs == ["raw/paper.pdf"]
    assert "paper-vault/sample-paper/images/fig001_page1_img1.png" in step.outputs
    assert "paper-vault/sample-paper/images/manifest.md" in step.outputs

    artifact_paths = {artifact.path for artifact in updated.artifacts}
    assert "paper-vault/sample-paper/images/fig001_page1_img1.png" in artifact_paths
    assert "paper-vault/sample-paper/images/manifest.md" in artifact_paths
    assert (tmp_path / "jobs" / "job-image.json").exists()


def test_pdf_image_extractor_skips_when_pdf_is_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    job = _job()

    updated = run_pdf_image_extraction(job, extractor=lambda pdf_path, images_dir: [])

    step = updated.steps[-1]
    assert step.id == "pdf.extract_images"
    assert step.state == "skipped"
    assert step.error == "PDF asset is not available"
    assert updated.status == "partial"


def _job() -> ResearchJob:
    metadata = PaperMetadata(
        slug="sample-paper",
        title="Sample Paper",
        authors=["Ada Lovelace"],
        year=2026,
        venue="arXiv",
        abstract="A sample paper.",
        canonical_url="https://example.test/abs/sample",
        pdf_url="https://example.test/paper.pdf",
        source_url=None,
        github_candidates=[],
        created_at="2026-05-18T00:00:00+00:00",
        status="intake_completed",
    )
    return ResearchJob(
        id="job-image",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
