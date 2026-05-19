from paperforge.models import Artifact, PaperMetadata, ResearchJob
from paperforge.note_writer import run_note_writing


def test_note_writer_creates_readme_skeleton_from_existing_artifacts(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    notes_dir = paper_dir / "notes"
    images_dir = paper_dir / "images"
    notes_dir.mkdir(parents=True)
    images_dir.mkdir(parents=True)

    (notes_dir / "external-sources.md").write_text("# External Sources\n", encoding="utf-8")
    (notes_dir / "code-references.md").write_text("# Code References\n", encoding="utf-8")
    (images_dir / "manifest.md").write_text("# Extracted Figures\n", encoding="utf-8")

    job = _job()
    job.artifacts.extend(
        [
            Artifact("note", "paper-vault/sample-paper/notes/external-sources.md", "External source log"),
            Artifact("code_reference", "paper-vault/sample-paper/notes/code-references.md", "Code references"),
            Artifact("note", "paper-vault/sample-paper/images/manifest.md", "Extracted image manifest"),
        ]
    )

    updated = run_note_writing(job)

    readme_path = notes_dir / "README.md"
    content = readme_path.read_text(encoding="utf-8")
    assert "# Sample Paper" in content
    assert "> Paper: https://example.test/abs/sample" in content
    assert "> Authors: Ada Lovelace, Grace Hopper" in content
    assert "> Venue: arXiv" in content
    assert "> Year: 2026" in content
    assert "> Draft status: scaffold only; deep explanation not generated yet." in content
    assert "## TL;DR" in content
    assert "- Not generated yet. This section needs paper-grounded synthesis." in content
    assert "- [External source log](external-sources.md)" in content
    assert "- [Code references](code-references.md)" in content
    assert "- [Extracted image manifest](../images/manifest.md)" in content
    assert "## Deep Q&A" in content
    assert "## Practical Takeaways" in content

    step = updated.steps[-1]
    assert step.id == "note.write_readme"
    assert step.state == "completed"
    assert step.inputs == [
        "metadata",
        "notes/external-sources.md",
        "images/manifest.md",
        "notes/code-references.md",
    ]
    assert step.outputs == ["paper-vault/sample-paper/notes/README.md"]
    assert any(
        artifact.kind == "note" and artifact.path == "paper-vault/sample-paper/notes/README.md"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-note.json").exists()


def _job() -> ResearchJob:
    metadata = PaperMetadata(
        slug="sample-paper",
        title="Sample Paper",
        authors=["Ada Lovelace", "Grace Hopper"],
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
        id="job-note",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
