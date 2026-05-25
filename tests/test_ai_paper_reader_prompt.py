from paperforge.ai_paper_reader_prompt import run_ai_paper_reader_prompt_pack
from paperforge.models import Artifact, PaperMetadata, ResearchJob


CANONICAL_SKILL_PATH = "C:/Users/Administrator/.codex/skills/neversight-skills_feed-ai-paper-reader/SKILL.md"


def test_prompt_pack_contains_skill_and_artifact_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = _create_workspace(tmp_path, include_pdf=True, include_evidence=True, include_manifest=True)
    job = _job()
    job.artifacts.append(Artifact("evidence_map", "paper-vault/sample-paper/notes/evidence-map.md", "PDF text evidence map"))

    updated = run_ai_paper_reader_prompt_pack(job)

    prompt_path = paper_dir / "notes" / "ai-paper-reader-prompt.md"
    content = prompt_path.read_text(encoding="utf-8")
    assert "./docs/PAPER_SKILL.md" in content
    assert CANONICAL_SKILL_PATH in content
    assert str(paper_dir) in content
    assert str(paper_dir / "metadata.json") in content
    assert str(paper_dir / "raw" / "paper.pdf") in content
    assert str(paper_dir / "notes" / "README.md") in content
    assert str(paper_dir / "notes" / "evidence-map.md") in content
    assert str(paper_dir / "images" / "manifest.md") in content
    assert "metadata, TL;DR, paper overview, background and motivation, core method, experiments, deep Q&A, summary and reflections" in content
    assert "Do not invent paper content" in content

    step = updated.steps[-1]
    assert step.id == "note.prepare_ai_paper_reader_prompt"
    assert step.state == "completed"
    assert step.outputs == ["paper-vault/sample-paper/notes/ai-paper-reader-prompt.md"]
    assert any(
        artifact.label == "AI Paper Reader Prompt"
        and artifact.path == "paper-vault/sample-paper/notes/ai-paper-reader-prompt.md"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-prompt.json").exists()


def test_prompt_pack_marks_missing_pdf_and_evidence_map(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = _create_workspace(tmp_path, include_pdf=False, include_evidence=False, include_manifest=False)

    updated = run_ai_paper_reader_prompt_pack(_job())

    content = (paper_dir / "notes" / "ai-paper-reader-prompt.md").read_text(encoding="utf-8")
    assert "| raw/paper.pdf | missing |" in content
    assert "| notes/evidence-map.md | missing |" in content
    assert "| images/manifest.md | missing |" in content
    assert "Missing artifacts must be treated as unavailable, not guessed from memory." in content
    assert updated.steps[-1].state == "partial"
    assert updated.steps[-1].error == "Some recommended artifacts are missing"
    assert updated.status == "partial"


def test_prompt_pack_updates_existing_artifact(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    _create_workspace(tmp_path, include_pdf=True, include_evidence=True, include_manifest=True)
    job = _job()
    job.artifacts.append(Artifact("note", "paper-vault/sample-paper/notes/ai-paper-reader-prompt.md", "Old prompt label"))

    updated = run_ai_paper_reader_prompt_pack(job)

    matching = [
        artifact
        for artifact in updated.artifacts
        if artifact.path == "paper-vault/sample-paper/notes/ai-paper-reader-prompt.md"
    ]
    assert len(matching) == 1
    assert matching[0].label == "AI Paper Reader Prompt"


def _create_workspace(
    tmp_path,
    *,
    include_pdf: bool,
    include_evidence: bool,
    include_manifest: bool,
):
    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    notes_dir = paper_dir / "notes"
    raw_dir = paper_dir / "raw"
    images_dir = paper_dir / "images"
    notes_dir.mkdir(parents=True)
    raw_dir.mkdir(parents=True)
    images_dir.mkdir(parents=True)

    (paper_dir / "metadata.json").write_text('{"title": "Sample Paper"}\n', encoding="utf-8")
    (notes_dir / "README.md").write_text("# Sample Paper\n", encoding="utf-8")
    if include_pdf:
        (raw_dir / "paper.pdf").write_bytes(b"%PDF-1.7\n")
    if include_evidence:
        (notes_dir / "evidence-map.md").write_text("# Evidence Map\n", encoding="utf-8")
    if include_manifest:
        (images_dir / "manifest.md").write_text("# Image Manifest\n", encoding="utf-8")
    return paper_dir


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
        created_at="2026-05-24T00:00:00+00:00",
        status="intake_completed",
    )
    return ResearchJob(
        id="job-prompt",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-24T00:00:00+00:00",
        updated_at="2026-05-24T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
