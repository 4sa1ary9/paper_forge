from paperforge.models import Artifact, PaperMetadata, ResearchJob
from paperforge.source_enrichment import run_source_enrichment


def test_source_enrichment_keeps_pdf_path_when_tex_source_is_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    raw_dir = paper_dir / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "paper.pdf").write_bytes(b"%PDF-1.7\n")

    job = _job(source_url=None)
    job.artifacts.append(Artifact("pdf", "paper-vault/sample-paper/raw/paper.pdf", "Paper PDF"))

    updated = run_source_enrichment(
        job,
        user_source_urls=["https://example.test/tutorial"],
    )

    source_log = paper_dir / "notes" / "external-sources.md"
    content = source_log.read_text(encoding="utf-8")
    assert "## Local Asset Status" in content
    assert "- PDF: available at `paper-vault/sample-paper/raw/paper.pdf`" in content
    assert "- TeX Source: unavailable" in content
    assert "- Fallback: continue with PDF-based processing." in content
    assert "- URL: https://example.test/tutorial" in content

    step = updated.steps[-1]
    assert step.id == "source.enrich_external_sources"
    assert step.state == "completed"
    assert step.outputs == ["paper-vault/sample-paper/notes/external-sources.md"]
    assert any(artifact.path == "paper-vault/sample-paper/notes/external-sources.md" for artifact in updated.artifacts)
    assert (tmp_path / "jobs" / "job-source").with_suffix(".json").exists()


def _job(source_url: str | None) -> ResearchJob:
    metadata = PaperMetadata(
        slug="sample-paper",
        title="Sample Paper",
        authors=["Ada Lovelace"],
        year=2026,
        venue="arXiv",
        abstract="A sample paper.",
        canonical_url="https://example.test/abs/sample",
        pdf_url="https://example.test/paper.pdf",
        source_url=source_url,
        github_candidates=[],
        created_at="2026-05-18T00:00:00+00:00",
        status="intake_completed",
    )
    return ResearchJob(
        id="job-source",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
