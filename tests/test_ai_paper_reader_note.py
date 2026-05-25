from paperforge.ai_paper_reader_note import run_ai_paper_reader_note_generation
from paperforge.models import Artifact, PaperMetadata, ResearchJob


def test_ai_paper_reader_note_generation_calls_reader_model_and_writes_artifact(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = _create_workspace(tmp_path, include_pdf=True, include_evidence=True, include_manifest=True)
    client = FakeChatClient("# Generated Note\n\nThis is grounded in the provided artifacts.")

    updated = run_ai_paper_reader_note_generation(_job(), client=client, model="deepseek-v4-pro")

    note_path = paper_dir / "notes" / "ai-paper-reader-note.md"
    prompt_path = paper_dir / "notes" / "ai-paper-reader-generation-prompt.md"
    assert note_path.read_text(encoding="utf-8").startswith("# Generated Note")
    assert prompt_path.exists()
    assert client.model == "deepseek-v4-pro"
    rendered_messages = "\n".join(message["content"] for message in client.messages)
    assert "AI 论文阅读笔记生成器" in rendered_messages
    assert str(paper_dir / "metadata.json") in rendered_messages
    assert str(paper_dir / "raw" / "paper.pdf") in rendered_messages
    assert str(paper_dir / "notes" / "evidence-map.md") in rendered_messages
    assert "Do not invent paper content" in rendered_messages

    step = updated.steps[-1]
    assert step.id == "note.generate_ai_paper_reader_note"
    assert step.state == "completed"
    assert step.outputs == [
        "paper-vault/sample-paper/notes/ai-paper-reader-note.md",
        "paper-vault/sample-paper/notes/ai-paper-reader-generation-prompt.md",
    ]
    assert any(
        artifact.label == "AI Paper Reader Note"
        and artifact.path == "paper-vault/sample-paper/notes/ai-paper-reader-note.md"
        for artifact in updated.artifacts
    )
    assert any(
        artifact.label == "AI Paper Reader Generation Prompt"
        and artifact.path == "paper-vault/sample-paper/notes/ai-paper-reader-generation-prompt.md"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-reader-note.json").exists()


def test_ai_paper_reader_note_uses_evidence_chunks_when_available(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PAPERFORGE_LLM_API_KEY", "sk-test-secret")
    paper_dir = _create_workspace(
        tmp_path,
        include_pdf=True,
        include_evidence=True,
        include_evidence_chunks=True,
        include_manifest=True,
    )
    client = FakeChatClient("# Chunk-grounded Note\n")

    run_ai_paper_reader_note_generation(_job(), client=client, model="deepseek-v4-pro")

    prompt_content = (paper_dir / "notes" / "ai-paper-reader-generation-prompt.md").read_text(encoding="utf-8")
    rendered_messages = "\n".join(message["content"] for message in client.messages)
    assert "notes/evidence-chunks.md" in prompt_content
    assert str(paper_dir / "notes" / "evidence-chunks.md") in rendered_messages
    assert "p002-c001" in rendered_messages
    assert "Chunk evidence about the core method." in rendered_messages
    assert "Prefer notes/evidence-chunks.md" in rendered_messages
    assert "Prioritize chunk id citations" in rendered_messages
    assert "mark it as needs verification" in rendered_messages
    assert "do not fill paper details from model memory" in rendered_messages
    assert "sk-test-secret" not in rendered_messages
    assert "sk-test-secret" not in prompt_content


def test_ai_paper_reader_note_falls_back_to_evidence_map_when_chunks_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = _create_workspace(
        tmp_path,
        include_pdf=True,
        include_evidence=True,
        include_evidence_chunks=False,
        include_manifest=True,
    )
    client = FakeChatClient("# Page-grounded Note\n")

    run_ai_paper_reader_note_generation(_job(), client=client, model="deepseek-v4-pro")

    prompt_content = (paper_dir / "notes" / "ai-paper-reader-generation-prompt.md").read_text(encoding="utf-8")
    assert "notes/evidence-map.md" in prompt_content
    assert "Page 1: sample evidence" in prompt_content
    assert "### notes/evidence-chunks.md" not in prompt_content
    assert "| notes/evidence-chunks.md | present |" not in prompt_content


def test_ai_paper_reader_note_marks_missing_llm_config_as_needs_user_input(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("paperforge.llm_client.get_project_root", lambda: tmp_path)
    monkeypatch.delenv("PAPERFORGE_LLM_API_KEY", raising=False)
    monkeypatch.delenv("PAPERFORGE_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("PAPERFORGE_READER_MODEL", raising=False)
    paper_dir = _create_workspace(tmp_path, include_pdf=True, include_evidence=True, include_manifest=True)

    updated = run_ai_paper_reader_note_generation(_job())

    assert not (paper_dir / "notes" / "ai-paper-reader-note.md").exists()
    step = updated.steps[-1]
    assert step.id == "note.generate_ai_paper_reader_note"
    assert step.state == "needs_user_input"
    assert "PAPERFORGE_LLM" in step.error
    assert updated.status == "needs_user_input"


def test_ai_paper_reader_note_marks_missing_artifacts_partial(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = _create_workspace(tmp_path, include_pdf=False, include_evidence=False, include_manifest=False)
    client = FakeChatClient("# Partial Note\n")

    updated = run_ai_paper_reader_note_generation(_job(), client=client, model="deepseek-v4-pro")

    prompt_content = (paper_dir / "notes" / "ai-paper-reader-generation-prompt.md").read_text(encoding="utf-8")
    assert "| raw/paper.pdf | missing |" in prompt_content
    assert "| notes/evidence-map.md | missing |" in prompt_content
    assert "| images/manifest.md | missing |" in prompt_content
    assert updated.steps[-1].state == "partial"
    assert updated.steps[-1].error == "Some recommended artifacts are missing"
    assert updated.status == "partial"


class FakeChatClient:
    def __init__(self, response):
        self.response = response
        self.messages = []
        self.model = None

    def chat(self, messages, *, model=None, temperature=0.2):
        self.messages = messages
        self.model = model
        return self.response


def _create_workspace(
    tmp_path,
    *,
    include_pdf: bool,
    include_evidence: bool,
    include_evidence_chunks: bool = False,
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
        (notes_dir / "evidence-map.md").write_text("# Evidence Map\nPage 1: sample evidence\n", encoding="utf-8")
    if include_evidence_chunks:
        (notes_dir / "evidence-chunks.md").write_text(
            """# Evidence Chunks

## Chunk Evidence

### p002-c001

- Page: 2
- Section guess: method
- Characters: 37

```text
Chunk evidence about the core method.
```
""",
            encoding="utf-8",
        )
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
        id="job-reader-note",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-24T00:00:00+00:00",
        updated_at="2026-05-24T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[Artifact("metadata", "paper-vault/sample-paper/metadata.json", "Paper metadata")],
    )
