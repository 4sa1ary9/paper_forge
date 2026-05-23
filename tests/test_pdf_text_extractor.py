from pathlib import Path

from paperforge.models import Artifact, PaperMetadata, ResearchJob
from paperforge.pdf_text_extractor import ExtractedPdfPage, run_pdf_text_extraction


def test_pdf_text_extractor_writes_evidence_map_from_pdf_pages(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    raw_dir = paper_dir / "raw"
    raw_dir.mkdir(parents=True)
    pdf_path = raw_dir / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n")

    def fake_extractor(path: Path) -> list[ExtractedPdfPage]:
        assert path == pdf_path
        return [
            ExtractedPdfPage(page=1, text="  Introduction\n\nAttention is useful.  "),
            ExtractedPdfPage(page=2, text="Method details\nwith equations."),
        ]

    job = _job()
    job.artifacts.append(Artifact("pdf", "paper-vault/sample-paper/raw/paper.pdf", "Paper PDF"))

    updated = run_pdf_text_extraction(job, extractor=fake_extractor)

    evidence_path = paper_dir / "notes" / "evidence-map.md"
    content = evidence_path.read_text(encoding="utf-8")
    assert "# PDF Text Evidence Map" in content
    assert "- Paper: Sample Paper" in content
    assert "- Extraction status: completed" in content
    assert "- Scope: raw text evidence only; no summary or explanation generated." in content
    assert "| 1 | 33 | yes |" in content
    assert "| 2 | 30 | yes |" in content
    assert "### Page 1" in content
    assert "Introduction Attention is useful." in content
    assert "### Page 2" in content
    assert "Method details with equations." in content

    step = updated.steps[-1]
    assert step.id == "pdf.extract_text_evidence"
    assert step.state == "completed"
    assert step.inputs == ["raw/paper.pdf"]
    assert step.outputs == ["paper-vault/sample-paper/notes/evidence-map.md"]
    assert any(
        artifact.kind == "evidence_map"
        and artifact.path == "paper-vault/sample-paper/notes/evidence-map.md"
        and artifact.label == "PDF text evidence map"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-pdf-text.json").exists()


def test_pdf_text_extractor_writes_partial_report_when_pdf_is_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)

    updated = run_pdf_text_extraction(_job())

    evidence_path = notes_dir / "evidence-map.md"
    content = evidence_path.read_text(encoding="utf-8")
    assert "- Extraction status: partial" in content
    assert "- PDF: missing" in content
    assert "| - | No PDF text extracted | - |" in content

    step = updated.steps[-1]
    assert step.id == "pdf.extract_text_evidence"
    assert step.state == "partial"
    assert step.error == "PDF asset is not available"
    assert step.outputs == ["paper-vault/sample-paper/notes/evidence-map.md"]
    assert updated.status == "partial"


def _job() -> ResearchJob:
    metadata = PaperMetadata(
        slug="sample-paper",
        title="Sample Paper",
        authors=["Ada Lovelace"],
        year=2026,
        venue="arXiv",
        abstract="A sample paper about reliable agent workflows.",
        canonical_url="https://example.test/abs/sample",
        pdf_url="https://example.test/paper.pdf",
        source_url=None,
        github_candidates=[],
        created_at="2026-05-18T00:00:00+00:00",
        status="intake_completed",
    )
    return ResearchJob(
        id="job-pdf-text",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
