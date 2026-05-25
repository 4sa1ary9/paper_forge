from paperforge.evidence_retriever import search_evidence_chunks, run_evidence_search
from paperforge.models import PaperMetadata, ResearchJob


def test_evidence_retriever_hits_method_chunk():
    chunks_markdown = """# Evidence Chunks

## Chunk Evidence

### p001-c001

- Page: 1
- Section guess: introduction
- Characters: 42

```text
Introduction text about the problem.
```

### p002-c001

- Page: 2
- Section guess: method
- Characters: 88

```text
Method section describes attention layers, encoder blocks, and residual normalization.
```
"""

    results = search_evidence_chunks("attention encoder method", chunks_markdown)

    assert results[0].chunk_id == "p002-c001"
    assert results[0].page == 2
    assert results[0].score > 0
    assert "attention layers" in results[0].excerpt


def test_evidence_retriever_hits_experiment_chunk():
    chunks_markdown = """# Evidence Chunks

## Chunk Evidence

### p002-c001

- Page: 2
- Section guess: method
- Characters: 60

```text
The method uses a compact encoder architecture.
```

### p006-c001

- Page: 6
- Section guess: experiment
- Characters: 91

```text
Experiments compare benchmark accuracy, ablation results, and training setup details.
```
"""

    results = search_evidence_chunks("benchmark ablation results", chunks_markdown)

    assert results[0].chunk_id == "p006-c001"
    assert results[0].page == 6
    assert results[0].score > 0
    assert "ablation results" in results[0].excerpt


def test_evidence_search_writes_markdown_artifact_and_job(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    notes_dir = paper_dir / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "evidence-chunks.md").write_text(
        """# Evidence Chunks

## Chunk Evidence

### p003-c001

- Page: 3
- Section guess: method
- Characters: 78

```text
The method uses retrieval-aware attention over chunk evidence.
```

### p007-c001

- Page: 7
- Section guess: experiment
- Characters: 82

```text
The experiments report benchmark retrieval quality and ablation evidence.
```
""",
        encoding="utf-8",
    )

    updated = run_evidence_search(_job(), "retrieval benchmark")

    output_path = notes_dir / "evidence-search.md"
    content = output_path.read_text(encoding="utf-8")
    assert "# Evidence Search Results" in content
    assert "- Query: `retrieval benchmark`" in content
    assert "- Search status: completed" in content
    assert "| p007-c001 | 7 |" in content
    assert "| p003-c001 | 3 |" in content
    assert "Score:" in content
    assert "Excerpt:" in content
    assert "benchmark retrieval quality" in content

    step = updated.steps[-1]
    assert step.id == "evidence.search_chunks"
    assert step.state == "completed"
    assert step.inputs == ["notes/evidence-chunks.md", "evidence search query"]
    assert step.outputs == ["paper-vault/sample-paper/notes/evidence-search.md"]
    assert any(
        artifact.kind == "evidence_search"
        and artifact.path == "paper-vault/sample-paper/notes/evidence-search.md"
        and artifact.label == "Evidence search results"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-evidence-search.json").exists()


def test_evidence_search_writes_partial_report_when_chunks_are_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)

    updated = run_evidence_search(_job(), "method")

    output_path = notes_dir / "evidence-search.md"
    content = output_path.read_text(encoding="utf-8")
    assert "- Search status: partial" in content
    assert "- Evidence chunks: missing" in content
    assert "No evidence search results generated." in content

    step = updated.steps[-1]
    assert step.id == "evidence.search_chunks"
    assert step.state == "partial"
    assert step.error == "Evidence chunks are not available"
    assert step.outputs == ["paper-vault/sample-paper/notes/evidence-search.md"]
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
        id="job-evidence-search",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
