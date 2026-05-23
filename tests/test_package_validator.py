from paperforge.models import PaperMetadata, ResearchJob
from paperforge.package_validator import run_package_validation


def test_package_validator_writes_complete_status_with_optional_tex_missing(monkeypatch, tmp_path):
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
        "evidence-map.md",
    ]:
        (notes_dir / filename).write_text(f"# {filename}\n", encoding="utf-8")

    updated = run_package_validation(_job())

    status_path = notes_dir / "package-status.md"
    content = status_path.read_text(encoding="utf-8")
    assert "# Research Package Status" in content
    assert "- Package status: complete" in content
    assert "| Metadata | `metadata.json` | required | present |" in content
    assert "| Paper PDF | `raw/paper.pdf` | recommended | present |" in content
    assert "| Image manifest | `images/manifest.md` | recommended | present |" in content
    assert "| PDF text evidence map | `notes/evidence-map.md` | recommended | present |" in content
    assert "| TeX source archive | `raw/source.tar.gz` | optional | missing |" in content
    assert "No missing required artifacts." in content
    assert "No warnings." in content

    step = updated.steps[-1]
    assert step.id == "package.validate_research_package"
    assert step.state == "completed"
    assert step.inputs == ["paper workspace"]
    assert step.outputs == ["paper-vault/sample-paper/notes/package-status.md"]
    assert any(
        artifact.kind == "package_status"
        and artifact.path == "paper-vault/sample-paper/notes/package-status.md"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-package.json").exists()


def test_package_validator_warns_when_pdf_and_image_manifest_are_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True)

    (paper_dir / "metadata.json").write_text('{"title": "Sample Paper"}\n', encoding="utf-8")
    for filename in [
        "external-sources.md",
        "code-references.md",
        "README.md",
        "terminology.md",
        "doubts.md",
        "interview-project.md",
    ]:
        (notes_dir / filename).write_text(f"# {filename}\n", encoding="utf-8")

    updated = run_package_validation(_job())

    content = (notes_dir / "package-status.md").read_text(encoding="utf-8")
    assert "- Package status: partial" in content
    assert "| Paper PDF | `raw/paper.pdf` | recommended | missing |" in content
    assert "| Image manifest | `images/manifest.md` | recommended | missing |" in content
    assert "- Missing recommended artifact: `raw/paper.pdf`." in content
    assert "- Missing recommended artifact: `images/manifest.md`." in content
    assert "- Missing recommended artifact: `notes/evidence-map.md`." in content
    assert "| TeX source archive | `raw/source.tar.gz` | optional | missing |" in content
    assert "No missing required artifacts." in content

    step = updated.steps[-1]
    assert step.state == "partial"
    assert step.error == "Research package has warnings"
    assert updated.status == "partial"


def test_package_validator_marks_missing_required_notes_as_partial(monkeypatch, tmp_path):
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
    (notes_dir / "external-sources.md").write_text("# External Sources\n", encoding="utf-8")

    updated = run_package_validation(_job())

    content = (notes_dir / "package-status.md").read_text(encoding="utf-8")
    assert "- Package status: partial" in content
    assert "| Paper note | `notes/README.md` | required | missing |" in content
    assert "- Missing required artifact: `notes/README.md`." in content
    assert "- Missing required artifact: `notes/code-references.md`." in content
    assert "- Missing required artifact: `notes/terminology.md`." in content
    assert "- Missing required artifact: `notes/doubts.md`." in content
    assert "- Missing required artifact: `notes/interview-project.md`." in content

    step = updated.steps[-1]
    assert step.state == "partial"
    assert step.error == "Research package is missing required artifacts"
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
        id="job-package",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
