from paperforge.deep_note_writer import run_deep_note_writing
from paperforge.models import PaperMetadata, ResearchJob


def test_deep_note_writer_updates_ready_sections_with_page_evidence(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)

    readme_path = notes_dir / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Sample Paper",
                "",
                "> Draft status: scaffold only; deep explanation not generated yet.",
                "",
                "## TL;DR",
                "",
                "- Not generated yet.",
                "",
                "## Evidence Inventory",
                "",
                "- [PDF text evidence map](evidence-map.md)",
                "",
                "## Paper Overview",
                "",
                "- Not generated yet.",
                "",
                "## Background and Motivation",
                "",
                "- Not generated yet.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (notes_dir / "deep-note-plan.md").write_text(
        "\n".join(
            [
                "# Deep Note Plan",
                "",
                "| Section | Status | Evidence |",
                "| --- | --- | --- |",
                "| TL;DR | ready | metadata, PDF text evidence map |",
                "| Paper Overview | ready | PDF text evidence map |",
                "| Background and Motivation | blocked | PDF text evidence map, external source log |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (notes_dir / "evidence-map.md").write_text(
        "\n".join(
            [
                "# PDF Text Evidence Map",
                "",
                "### Page 1",
                "",
                "```text",
                "Sample Paper introduces a reliable workflow. It collects evidence before generating notes.",
                "```",
                "",
                "### Page 2",
                "",
                "```text",
                "The system uses structured steps to keep outputs auditable.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    updated = run_deep_note_writing(_job())

    content = readme_path.read_text(encoding="utf-8")
    assert "> Draft status: conservative deep note MVP; full deep explanation not generated yet." in content
    assert "## TL;DR" in content
    assert (
        "- Evidence-grounded draft (needs human review): Sample Paper introduces a reliable workflow. "
        "(Evidence: `notes/evidence-map.md`, page 1)."
    ) in content
    assert "## Paper Overview" in content
    assert "- Primary evidence pages: 1, 2." in content
    assert "- Page 2 evidence: The system uses structured steps to keep outputs auditable." in content
    assert "## Background and Motivation\n\n- Not generated yet." in content

    step = updated.steps[-1]
    assert step.id == "note.write_deep_note_mvp"
    assert step.state == "completed"
    assert step.inputs == ["notes/deep-note-plan.md", "notes/evidence-map.md", "notes/README.md"]
    assert step.outputs == ["paper-vault/sample-paper/notes/README.md"]
    assert any(
        artifact.kind == "note"
        and artifact.path == "paper-vault/sample-paper/notes/README.md"
        and artifact.label == "Paper note with deep note MVP"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-deep-note-writer.json").exists()


def test_deep_note_writer_leaves_readme_unchanged_when_target_sections_are_blocked(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)

    readme_path = notes_dir / "README.md"
    original_readme = "# Sample Paper\n\n## TL;DR\n\n- Not generated yet.\n"
    readme_path.write_text(original_readme, encoding="utf-8")
    (notes_dir / "deep-note-plan.md").write_text(
        "\n".join(
            [
                "# Deep Note Plan",
                "",
                "| Section | Status | Evidence |",
                "| --- | --- | --- |",
                "| TL;DR | blocked | metadata, PDF text evidence map |",
                "| Paper Overview | blocked | PDF text evidence map |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (notes_dir / "evidence-map.md").write_text(
        "# PDF Text Evidence Map\n\n### Page 1\n\n```text\nEvidence exists.\n```\n",
        encoding="utf-8",
    )

    updated = run_deep_note_writing(_job())

    assert readme_path.read_text(encoding="utf-8") == original_readme
    step = updated.steps[-1]
    assert step.id == "note.write_deep_note_mvp"
    assert step.state == "partial"
    assert step.error == "No target sections are ready for deep note writing"
    assert updated.status == "partial"


def test_deep_note_writer_skips_boilerplate_evidence_pages(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)

    readme_path = notes_dir / "README.md"
    readme_path.write_text("# Sample Paper\n\n## TL;DR\n\n- Not generated yet.\n", encoding="utf-8")
    (notes_dir / "deep-note-plan.md").write_text(
        "\n".join(
            [
                "# Deep Note Plan",
                "",
                "| Section | Status | Evidence |",
                "| --- | --- | --- |",
                "| TL;DR | ready | metadata, PDF text evidence map |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (notes_dir / "evidence-map.md").write_text(
        "\n".join(
            [
                "# PDF Text Evidence Map",
                "",
                "### Page 1",
                "",
                "```text",
                "Provided proper attribution is provided, Google hereby grants permission to reproduce tables.",
                "```",
                "",
                "### Page 2",
                "",
                "```text",
                "Introduction This paper proposes a new sequence transduction architecture based entirely on attention.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    run_deep_note_writing(_job())

    content = readme_path.read_text(encoding="utf-8")
    assert "Google hereby grants permission" not in content
    assert (
        "Introduction This paper proposes a new sequence transduction architecture based entirely on attention. "
        "(Evidence: `notes/evidence-map.md`, page 2)."
    ) in content


def test_deep_note_writer_preserves_backslashes_in_evidence_text(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)

    readme_path = notes_dir / "README.md"
    readme_path.write_text("# Sample Paper\n\n## TL;DR\n\n- Not generated yet.\n", encoding="utf-8")
    (notes_dir / "deep-note-plan.md").write_text(
        "# Deep Note Plan\n\n| Section | Status | Evidence |\n| --- | --- | --- |\n| TL;DR | ready | evidence |\n",
        encoding="utf-8",
    )
    (notes_dir / "evidence-map.md").write_text(
        "# PDF Text Evidence Map\n\n### Page 1\n\n```text\nThe method uses \\alpha weights.\n```\n",
        encoding="utf-8",
    )

    run_deep_note_writing(_job())

    assert "The method uses \\alpha weights." in readme_path.read_text(encoding="utf-8")


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
        id="job-deep-note-writer",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
