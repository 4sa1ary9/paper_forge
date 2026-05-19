from paperforge.code_linker import run_code_linking
from paperforge.models import Artifact, PaperMetadata, ResearchJob


def test_code_linker_writes_github_candidates_from_metadata_and_source_log(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)
    external_sources_path = notes_dir / "external-sources.md"
    external_sources_path.write_text(
        "\n".join(
            [
                "# External Sources",
                "",
                "- URL: https://github.com/example/paper-code",
                "- URL: https://example.test/tutorial",
            ]
        ),
        encoding="utf-8",
    )

    job = _job()
    job.artifacts.append(
        Artifact("note", "paper-vault/sample-paper/notes/external-sources.md", "External source log")
    )

    updated = run_code_linking(job)

    code_references_path = notes_dir / "code-references.md"
    content = code_references_path.read_text(encoding="utf-8")
    assert "# Code References" in content
    assert "https://github.com/example/paper-code" in content
    assert "https://github.com/example/metadata-code" in content
    assert "- Clone decision: not cloned" in content
    assert "- Reason: first MVP only records candidates; cloning requires user confirmation." in content

    step = updated.steps[-1]
    assert step.id == "code.link_repositories"
    assert step.state == "completed"
    assert step.inputs == ["metadata.github_candidates", "notes/external-sources.md"]
    assert step.outputs == ["paper-vault/sample-paper/notes/code-references.md"]

    assert any(
        artifact.path == "paper-vault/sample-paper/notes/code-references.md"
        and artifact.kind == "code_reference"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-code.json").exists()


def test_code_linker_marks_partial_when_no_github_candidates(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    job = _job(github_candidates=[])

    updated = run_code_linking(job)

    step = updated.steps[-1]
    assert step.id == "code.link_repositories"
    assert step.state == "partial"
    assert step.error == "No GitHub repository candidates were found"
    assert updated.status == "partial"


def _job(github_candidates: list[str] | None = None) -> ResearchJob:
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
        github_candidates=github_candidates
        if github_candidates is not None
        else ["https://github.com/example/metadata-code"],
        created_at="2026-05-18T00:00:00+00:00",
        status="intake_completed",
    )
    return ResearchJob(
        id="job-code",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
