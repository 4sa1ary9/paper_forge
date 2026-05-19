from paperforge.interview_mapper import run_interview_mapping_scaffold
from paperforge.models import Artifact, PaperMetadata, ResearchJob


def test_interview_mapper_creates_scaffold_without_assessing_suitability(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "README.md").write_text("# Sample Paper\n", encoding="utf-8")
    (notes_dir / "code-references.md").write_text("# Code References\n", encoding="utf-8")

    job = _job()
    job.artifacts.extend(
        [
            Artifact("note", "paper-vault/sample-paper/notes/README.md", "Paper note scaffold"),
            Artifact("code_reference", "paper-vault/sample-paper/notes/code-references.md", "Code references"),
        ]
    )

    updated = run_interview_mapping_scaffold(job)

    mapping_path = notes_dir / "interview-project.md"
    content = mapping_path.read_text(encoding="utf-8")
    assert "# Interview Project Mapping" in content
    assert "- Paper: Sample Paper" in content
    assert "- Draft status: scaffold only; suitability not assessed yet." in content
    assert "- Source note: [Paper note scaffold](README.md)" in content
    assert "- Code references: [Code references](code-references.md)" in content
    assert "## Suitability" in content
    assert "- Suitability: not assessed" in content
    assert "## Why This Can Become a Project" in content
    assert "## Why This May Not Be Worth Building" in content
    assert "## Minimal Demo Version" in content
    assert "## Full Version" in content
    assert "## Technical Highlights" in content
    assert "## Risks" in content
    assert "## Connection to Existing Projects" in content
    assert "## Interview Talking Points" in content

    step = updated.steps[-1]
    assert step.id == "project.write_interview_mapping"
    assert step.state == "completed"
    assert step.inputs == ["metadata", "notes/README.md", "notes/code-references.md"]
    assert step.outputs == ["paper-vault/sample-paper/notes/interview-project.md"]
    assert any(
        artifact.kind == "interview_mapping"
        and artifact.path == "paper-vault/sample-paper/notes/interview-project.md"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-interview.json").exists()


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
        id="job-interview",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
