from paperforge import doubts_agent
from paperforge.doubts_agent import run_doubts_scaffold
from paperforge.models import Artifact, PaperMetadata, ResearchJob


def test_doubts_agent_creates_scaffold_without_generating_questions(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "README.md").write_text("# Sample Paper\n", encoding="utf-8")

    job = _job()
    job.artifacts.append(Artifact("note", "paper-vault/sample-paper/notes/README.md", "Paper note scaffold"))

    updated = run_doubts_scaffold(job)

    doubts_path = notes_dir / "doubts.md"
    content = doubts_path.read_text(encoding="utf-8")
    assert "# Doubts and Follow-up Questions" in content
    assert "- Paper: Sample Paper" in content
    assert "- Draft status: scaffold only; doubts not generated yet." in content
    assert "- Source note: [Paper note scaffold](README.md)" in content
    assert "## Open Questions" in content
    assert "- Not generated yet." in content
    assert "## Confusing Formulas" in content
    assert "## Missing Implementation Details" in content
    assert "## Claims That Need Verification" in content
    assert "## Questions to Ask an Interviewer or Mentor" in content

    step = updated.steps[-1]
    assert step.id == "knowledge.write_doubts"
    assert step.state == "completed"
    assert step.inputs == ["metadata", "notes/README.md"]
    assert step.outputs == ["paper-vault/sample-paper/notes/doubts.md"]
    assert any(
        artifact.kind == "doubts" and artifact.path == "paper-vault/sample-paper/notes/doubts.md"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-doubts.json").exists()


def test_doubts_evidence_writes_questions_from_notes_and_terms(monkeypatch, tmp_path):
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
                "## Limitations",
                "",
                "- Page 7 limitation evidence: Future work should test whether the method fails under noisy inputs.",
                "",
                "## Deep Q&A",
                "",
                "- Method question (source: Core Method, page 2): Which method detail needs manual explanation?",
                "- Experiment question (source: Experiments, page 6): Which metric should be checked?",
                "- Limitation question (source: Limitations, page 7): Which deployment condition matters?",
                "",
                "## Practical Takeaways",
                "",
                "- Method takeaway (source: Core Method, page 2): Use this evidence as the starting point.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (notes_dir / "terminology.md").write_text(
        "\n".join(
            [
                "# Terminology",
                "",
                "## Scaled Dot-Product Attention",
                "",
                "- First seen in: `notes/evidence-map.md`, page 2; source section: Core Method.",
                "",
                "## BLEU",
                "",
                "- First seen in: `notes/evidence-map.md`, page 6; source section: Experiments.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (notes_dir / "doubts.md").write_text(
        "# Doubts and Follow-up Questions\n\n- Draft status: scaffold only; doubts not generated yet.\n",
        encoding="utf-8",
    )

    updated = doubts_agent.run_doubts_evidence(_job())

    content = (notes_dir / "doubts.md").read_text(encoding="utf-8")
    assert "- Draft status: doubts evidence MVP; questions require human review." in content
    assert "## Open Questions" in content
    assert (
        "- Method question (source: Core Method, page 2): Which method detail needs manual explanation?"
        in content
    )
    assert "- Experiment question (source: Experiments, page 6): Which metric should be checked?" in content
    assert "- Limitation question (source: Limitations, page 7): Which deployment condition matters?" in content
    assert "## Missing Implementation Details" in content
    assert (
        "- Implementation doubt (source: Core Method, page 2): What concrete implementation detail is still "
        "missing for this method evidence?"
    ) in content
    assert "## Claims That Need Verification" in content
    assert (
        "- Experiment doubt (source: Experiments, page 6): Which metric, baseline, or setup detail must be "
        "checked before trusting this result?"
    ) in content
    assert (
        "- Limitation doubt (source: Limitations, page 7): What condition could make this limitation important "
        "in practice?"
    ) in content
    assert "## Terminology Questions" in content
    assert (
        "- Term question (source: Core Method, page 2): What does `Scaled Dot-Product Attention` mean in this paper?"
        in content
    )
    assert "- Manual review: answer these questions only after checking the cited source pages." in content
    assert "starting point" not in content

    step = updated.steps[-1]
    assert step.id == "knowledge.write_doubts_evidence"
    assert step.state == "completed"
    assert step.inputs == ["notes/README.md", "notes/terminology.md", "notes/doubts.md"]
    assert step.outputs == ["paper-vault/sample-paper/notes/doubts.md"]
    assert any(
        artifact.kind == "doubts"
        and artifact.path == "paper-vault/sample-paper/notes/doubts.md"
        and artifact.label == "Doubts evidence draft"
        for artifact in updated.artifacts
    )


def test_doubts_evidence_is_partial_when_inputs_are_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "doubts.md").write_text("# Doubts and Follow-up Questions\n", encoding="utf-8")

    updated = doubts_agent.run_doubts_evidence(_job())

    step = updated.steps[-1]
    assert step.id == "knowledge.write_doubts_evidence"
    assert step.state == "partial"
    assert step.error == "Missing doubts evidence inputs: README.md, terminology.md"
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
        id="job-doubts",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
