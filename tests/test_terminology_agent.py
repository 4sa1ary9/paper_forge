from paperforge.models import Artifact, PaperMetadata, ResearchJob
from paperforge import terminology_agent
from paperforge.terminology_agent import run_terminology_scaffold


def test_terminology_agent_creates_scaffold_without_extracting_terms(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "README.md").write_text("# Sample Paper\n", encoding="utf-8")

    job = _job()
    job.artifacts.append(Artifact("note", "paper-vault/sample-paper/notes/README.md", "Paper note scaffold"))

    updated = run_terminology_scaffold(job)

    terminology_path = notes_dir / "terminology.md"
    content = terminology_path.read_text(encoding="utf-8")
    assert "# Terminology" in content
    assert "- Paper: Sample Paper" in content
    assert "- Draft status: scaffold only; terms not extracted yet." in content
    assert "- Source note: [Paper note scaffold](README.md)" in content
    assert "## Term Name" in content
    assert "- Category:" in content
    assert "- Short explanation:" in content
    assert "- Why it matters in this paper:" in content
    assert "- Related terms:" in content
    assert "- First seen in:" in content
    assert "- Follow-up reading:" in content

    step = updated.steps[-1]
    assert step.id == "knowledge.write_terminology"
    assert step.state == "completed"
    assert step.inputs == ["metadata", "notes/README.md"]
    assert step.outputs == ["paper-vault/sample-paper/notes/terminology.md"]
    assert any(
        artifact.kind == "terminology"
        and artifact.path == "paper-vault/sample-paper/notes/terminology.md"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-terminology.json").exists()


def test_terminology_evidence_writes_only_page_backed_terms(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "README.md").write_text(
        "\n".join(
            [
                "# Sample Paper",
                "",
                "## Core Method",
                "",
                "- Page 2 method evidence: Model Architecture uses Scaled Dot-Product Attention in an encoder-decoder model.",
                "",
                "## Experiments",
                "",
                "- Page 6 experiment evidence: Table 2 reports BLEU results on translation benchmarks.",
                "",
                "## Practical Takeaways",
                "",
                "- Method takeaway (source: Core Method, page 2): Use this evidence as the starting point.",
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
                "### Page 2",
                "",
                "```text",
                "Model Architecture uses Scaled Dot-Product Attention in an encoder-decoder model.",
                "```",
                "",
                "### Page 6",
                "",
                "```text",
                "Table 2 reports BLEU results on translation benchmarks.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (notes_dir / "terminology.md").write_text(
        "# Terminology\n\n- Draft status: scaffold only; terms not extracted yet.\n",
        encoding="utf-8",
    )

    updated = terminology_agent.run_terminology_evidence(_job())

    content = (notes_dir / "terminology.md").read_text(encoding="utf-8")
    assert "- Draft status: terminology evidence MVP; terms require human review." in content
    assert "## Model Architecture" in content
    assert "## Scaled Dot-Product Attention" in content
    assert "## BLEU" in content
    assert "- First seen in: `notes/evidence-map.md`, page 2; source section: Core Method." in content
    assert "- First seen in: `notes/evidence-map.md`, page 6; source section: Experiments." in content
    assert "starting point" not in content

    step = updated.steps[-1]
    assert step.id == "knowledge.write_terminology_evidence"
    assert step.state == "completed"
    assert step.inputs == ["notes/evidence-map.md", "notes/README.md", "notes/terminology.md"]
    assert step.outputs == ["paper-vault/sample-paper/notes/terminology.md"]
    assert any(
        artifact.kind == "terminology"
        and artifact.path == "paper-vault/sample-paper/notes/terminology.md"
        and artifact.label == "Terminology evidence draft"
        for artifact in updated.artifacts
    )


def test_terminology_evidence_is_partial_when_inputs_are_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "terminology.md").write_text("# Terminology\n", encoding="utf-8")

    updated = terminology_agent.run_terminology_evidence(_job())

    step = updated.steps[-1]
    assert step.id == "knowledge.write_terminology_evidence"
    assert step.state == "partial"
    assert step.error == "Missing terminology evidence inputs: evidence-map.md, README.md"
    assert updated.status == "partial"


def test_terminology_evidence_rejects_phrase_fragments(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "README.md").write_text(
        "\n".join(
            [
                "# Sample Paper",
                "",
                "## Background and Motivation",
                "",
                "- Page 2 motivation evidence: Introduction Recurrent neural networks and long short-term memory are common baselines.",
                "",
                "## Experiments",
                "",
                "- Page 6 experiment evidence: The table compares per-layer complexity and training cost.",
                "",
                "## Limitations",
                "",
                "- Page 7 limitation evidence: The method is compared with state-of-the-art models on translation tasks.",
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
                "### Page 2",
                "",
                "```text",
                "Introduction Recurrent neural networks and long short-term memory are common baselines.",
                "```",
                "",
                "### Page 6",
                "",
                "```text",
                "The table compares per-layer complexity and training cost.",
                "```",
                "",
                "### Page 7",
                "",
                "```text",
                "The method is compared with state-of-the-art models on translation tasks.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (notes_dir / "terminology.md").write_text("# Terminology\n", encoding="utf-8")

    terminology_agent.run_terminology_evidence(_job())

    content = (notes_dir / "terminology.md").read_text(encoding="utf-8")
    assert "## Introduction Recurrent" not in content
    assert "## per-layer complexity and" not in content
    assert "## state-of-the-art models on" not in content
    assert "## short-term memory" in content
    assert "## per-layer complexity" in content
    assert "## state-of-the-art models" in content


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
        id="job-terminology",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
