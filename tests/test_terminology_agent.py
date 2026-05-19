from paperforge.models import Artifact, PaperMetadata, ResearchJob
from paperforge.terminology_agent import run_terminology_scaffold


def test_terminology_agent_creates_scaffold_without_extracting_terms(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "README.md").write_text("# Sample Paper\n", encoding="utf-8")

    job = _job()
    job.artifacts.append(Artifact("note", "paper-vault/sample-paper/notes/README.md", "Paper note scaffold"))

    updated = run_terminology_scaffold(job)

    terminology_path = notes_dir / "terminology.md"
    content = terminology_path.read_text(encoding="utf-8")
    assert "# Terminology" in content
    assert "- Paper: Sample Paper" in content
    assert "- Draft status: scaffold only; terms not extracted yet." in content
    assert "- Source note: [Paper note scaffold](README.md)" in content
    assert "## Term Name" in content
    assert "- Category:" in content
    assert "- Short explanation:" in content
    assert "- Why it matters in this paper:" in content
    assert "- Related terms:" in content
    assert "- First seen in:" in content
    assert "- Follow-up reading:" in content

    step = updated.steps[-1]
    assert step.id == "knowledge.write_terminology"
    assert step.state == "completed"
    assert step.inputs == ["metadata", "notes/README.md"]
    assert step.outputs == ["paper-vault/sample-paper/notes/terminology.md"]
    assert any(
        artifact.kind == "terminology"
        and artifact.path == "paper-vault/sample-paper/notes/terminology.md"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-terminology.json").exists()


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
        id="job-terminology",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
