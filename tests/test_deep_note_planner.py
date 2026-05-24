from paperforge.deep_note_planner import run_deep_note_planning
from paperforge.models import PaperMetadata, ResearchJob


def test_deep_note_planner_writes_ready_plan_from_existing_package(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    notes_dir = paper_dir / "notes"
    raw_dir = paper_dir / "raw"
    images_dir = paper_dir / "images"
    notes_dir.mkdir(parents=True)
    raw_dir.mkdir(parents=True)
    images_dir.mkdir(parents=True)

    (paper_dir / "metadata.json").write_text('{"title": "Sample Paper"}\n', encoding="utf-8")
    (raw_dir / "paper.pdf").write_bytes(b"%PDF-1.7\n")
    (images_dir / "manifest.md").write_text("# Extracted Figures\n", encoding="utf-8")
    for filename in [
        "external-sources.md",
        "code-references.md",
        "README.md",
        "terminology.md",
        "doubts.md",
        "interview-project.md",
        "package-status.md",
        "evidence-map.md",
    ]:
        (notes_dir / filename).write_text(f"# {filename}\n", encoding="utf-8")

    updated = run_deep_note_planning(_job())

    plan_path = notes_dir / "deep-note-plan.md"
    content = plan_path.read_text(encoding="utf-8")
    assert "# Deep Note Plan" in content
    assert "- Paper: Sample Paper" in content
    assert "- Planner status: ready" in content
    assert "- Scope: readiness gate only; deep explanation not generated." in content
    assert "| Package status | `notes/package-status.md` | required | present |" in content
    assert "| Paper PDF | `raw/paper.pdf` | recommended | present |" in content
    assert "| PDF text evidence map | `notes/evidence-map.md` | recommended | present |" in content
    assert "| TL;DR | ready | metadata, PDF text evidence map |" in content
    assert "| Core Method | ready | PDF text evidence map, image manifest |" in content
    assert "| Deep Q&A | ready | generated method, experiment, and limitation evidence notes |" in content
    assert (
        "| Practical Takeaways | ready | generated method, experiment, limitation, and Deep Q&A evidence notes |"
        in content
    )
    assert "9. Practical Takeaways after Deep Q&A evidence notes exist" in content
    assert "No missing readiness inputs." in content

    step = updated.steps[-1]
    assert step.id == "note.plan_deep_note"
    assert step.state == "completed"
    assert step.inputs == [
        "notes/package-status.md",
        "notes/README.md",
        "raw/paper.pdf",
        "notes/evidence-map.md",
        "images/manifest.md",
    ]
    assert step.outputs == ["paper-vault/sample-paper/notes/deep-note-plan.md"]
    assert any(
        artifact.kind == "note"
        and artifact.path == "paper-vault/sample-paper/notes/deep-note-plan.md"
        and artifact.label == "Deep note plan"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-deep-plan.json").exists()


def test_deep_note_planner_marks_partial_when_readiness_inputs_are_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "README.md").write_text("# Sample Paper\n", encoding="utf-8")

    updated = run_deep_note_planning(_job())

    content = (notes_dir / "deep-note-plan.md").read_text(encoding="utf-8")
    assert "- Planner status: partial" in content
    assert "| Package status | `notes/package-status.md` | required | missing |" in content
    assert "| Paper PDF | `raw/paper.pdf` | recommended | missing |" in content
    assert "| PDF text evidence map | `notes/evidence-map.md` | recommended | missing |" in content
    assert "| Image manifest | `images/manifest.md` | recommended | missing |" in content
    assert "| TL;DR | blocked | metadata, PDF text evidence map |" in content
    assert "| Core Method | blocked | PDF text evidence map, image manifest |" in content
    assert "| Experiments | blocked | PDF text evidence map, image manifest |" in content
    assert "| Deep Q&A | blocked | generated method, experiment, and limitation evidence notes |" in content
    assert (
        "| Practical Takeaways | blocked | generated method, experiment, limitation, and Deep Q&A evidence notes |"
        in content
    )
    assert "- Missing required readiness input: `notes/package-status.md`." in content
    assert "- Missing recommended readiness input: `raw/paper.pdf`." in content
    assert "- Missing recommended readiness input: `notes/evidence-map.md`." in content
    assert "- Missing recommended readiness input: `images/manifest.md`." in content

    step = updated.steps[-1]
    assert step.id == "note.plan_deep_note"
    assert step.state == "partial"
    assert step.error == "Deep note plan has missing readiness inputs"
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
        id="job-deep-plan",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
