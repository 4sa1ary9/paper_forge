from paperforge.doubts_agent import run_doubts_scaffold
from paperforge.models import Artifact, PaperMetadata, ResearchJob


def test_doubts_agent_creates_scaffold_without_generating_questions(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "README.md").write_text("# Sample Paper\n", encoding="utf-8")

    job = _job()
    job.artifacts.append(Artifact("note", "paper-vault/sample-paper/notes/README.md", "Paper note scaffold"))

    updated = run_doubts_scaffold(job)

    doubts_path = notes_dir / "doubts.md"
    content = doubts_path.read_text(encoding="utf-8")
    assert "# Doubts and Follow-up Questions" in content
    assert "- Paper: Sample Paper" in content
    assert "- Draft status: scaffold only; doubts not generated yet." in content
    assert "- Source note: [Paper note scaffold](README.md)" in content
    assert "## Open Questions" in content
    assert "- Not generated yet." in content
    assert "## Confusing Formulas" in content
    assert "## Missing Implementation Details" in content
    assert "## Claims That Need Verification" in content
    assert "## Questions to Ask an Interviewer or Mentor" in content

    step = updated.steps[-1]
    assert step.id == "knowledge.write_doubts"
    assert step.state == "completed"
    assert step.inputs == ["metadata", "notes/README.md"]
    assert step.outputs == ["paper-vault/sample-paper/notes/doubts.md"]
    assert any(
        artifact.kind == "doubts" and artifact.path == "paper-vault/sample-paper/notes/doubts.md"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-doubts.json").exists()


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
        id="job-doubts",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
