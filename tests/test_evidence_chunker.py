from paperforge.evidence_chunker import build_evidence_chunks_from_markdown, run_evidence_chunk_extraction
from paperforge.models import PaperMetadata, ResearchJob


def test_evidence_chunker_parses_pages_and_builds_stable_chunks():
    markdown = """# PDF Text Evidence Map

## Page Evidence Excerpts

### Page 1

```text
Introduction

This paper studies reliable evidence maps for paper reading workflows.

Method

The method splits page excerpts into smaller chunks with stable ids.
```

### Page 2

```text
Experiments

The experiment section reports benchmark results and ablation evidence.

Limitations

The limitation section describes missing coverage and future work.
```
"""

    chunks = build_evidence_chunks_from_markdown(markdown, max_chunk_chars=120)

    assert [chunk.id for chunk in chunks] == [
        "p001-c001",
        "p001-c002",
        "p002-c001",
        "p002-c002",
    ]
    assert chunks[0].page == 1
    assert chunks[0].section_guess == "introduction"
    assert chunks[1].section_guess == "method"
    assert chunks[2].section_guess == "experiment"
    assert chunks[3].section_guess == "limitation"
    assert chunks[0].character_count == len(chunks[0].text)
    assert "paper reading workflows" in chunks[0].text


def test_evidence_chunker_splits_long_paragraph_by_reasonable_length():
    markdown = """# PDF Text Evidence Map

## Page Evidence Excerpts

### Page 1

```text
Method details include attention layers, encoder blocks, decoder blocks, positional embeddings, residual paths, and normalization choices for a compact architecture description.
```
"""

    chunks = build_evidence_chunks_from_markdown(markdown, max_chunk_chars=80)

    assert [chunk.id for chunk in chunks] == ["p001-c001", "p001-c002", "p001-c003"]
    assert all(chunk.page == 1 for chunk in chunks)
    assert all(chunk.section_guess == "method" for chunk in chunks)
    assert all(chunk.character_count <= 80 for chunk in chunks)


def test_evidence_chunk_extraction_writes_markdown_artifact_and_job(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "evidence-map.md").write_text(
        """# PDF Text Evidence Map

## Page Evidence Excerpts

### Page 1

```text
Introduction

This paper introduces chunk evidence.
```

### Page 2

```text
Experiments

The experiments compare chunk retrieval quality.
```
""",
        encoding="utf-8",
    )

    updated = run_evidence_chunk_extraction(_job())

    chunks_path = notes_dir / "evidence-chunks.md"
    content = chunks_path.read_text(encoding="utf-8")
    assert "# Evidence Chunks" in content
    assert "- Extraction status: completed" in content
    assert "- Source: `notes/evidence-map.md`" in content
    assert "| p001-c001 | 1 | introduction |" in content
    assert "| p002-c001 | 2 | experiment |" in content
    assert "This paper introduces chunk evidence." in content
    assert "The experiments compare chunk retrieval quality." in content
    assert "- Scope: chunk-level evidence only; no summary or explanation generated." in content

    step = updated.steps[-1]
    assert step.id == "pdf.extract_evidence_chunks"
    assert step.state == "completed"
    assert step.inputs == ["notes/evidence-map.md"]
    assert step.outputs == ["paper-vault/sample-paper/notes/evidence-chunks.md"]
    assert any(
        artifact.kind == "evidence_chunks"
        and artifact.path == "paper-vault/sample-paper/notes/evidence-chunks.md"
        and artifact.label == "Evidence chunks"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-evidence-chunks.json").exists()


def test_evidence_chunk_extraction_writes_partial_report_when_evidence_map_is_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)

    updated = run_evidence_chunk_extraction(_job())

    chunks_path = notes_dir / "evidence-chunks.md"
    content = chunks_path.read_text(encoding="utf-8")
    assert "- Extraction status: partial" in content
    assert "- Evidence map: missing" in content
    assert "No evidence chunks generated." in content

    step = updated.steps[-1]
    assert step.id == "pdf.extract_evidence_chunks"
    assert step.state == "partial"
    assert step.error == "Evidence map is not available"
    assert step.outputs == ["paper-vault/sample-paper/notes/evidence-chunks.md"]
    assert updated.status == "partial"
    assert any(
        artifact.kind == "evidence_chunks"
        and artifact.label == "Evidence chunks"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-evidence-chunks.json").exists()


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
        id="job-evidence-chunks",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
