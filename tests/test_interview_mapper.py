from paperforge.interview_mapper import run_interview_mapping_assessment, run_interview_mapping_scaffold
from paperforge.models import Artifact, PaperMetadata, ResearchJob


def test_interview_mapper_creates_scaffold_without_assessing_suitability(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "README.md").write_text("# Sample Paper\n", encoding="utf-8")
    (notes_dir / "code-references.md").write_text("# Code References\n", encoding="utf-8")

    job = _job()
    job.artifacts.extend(
        [
            Artifact("note", "paper-vault/sample-paper/notes/README.md", "Paper note scaffold"),
            Artifact("code_reference", "paper-vault/sample-paper/notes/code-references.md", "Code references"),
        ]
    )

    updated = run_interview_mapping_scaffold(job)

    mapping_path = notes_dir / "interview-project.md"
    content = mapping_path.read_text(encoding="utf-8")
    assert "# Interview Project Mapping" in content
    assert "- Paper: Sample Paper" in content
    assert "- Draft status: scaffold only; suitability not assessed yet." in content
    assert "- Source note: [Paper note scaffold](README.md)" in content
    assert "- Code references: [Code references](code-references.md)" in content
    assert "## Suitability" in content
    assert "- Suitability: not assessed" in content
    assert "## Why This Can Become a Project" in content
    assert "## Why This May Not Be Worth Building" in content
    assert "## Minimal Demo Version" in content
    assert "## Full Version" in content
    assert "## Technical Highlights" in content
    assert "## Risks" in content
    assert "## Connection to Existing Projects" in content
    assert "## Interview Talking Points" in content

    step = updated.steps[-1]
    assert step.id == "project.write_interview_mapping"
    assert step.state == "completed"
    assert step.inputs == ["metadata", "notes/README.md", "notes/code-references.md"]
    assert step.outputs == ["paper-vault/sample-paper/notes/interview-project.md"]
    assert any(
        artifact.kind == "interview_mapping"
        and artifact.path == "paper-vault/sample-paper/notes/interview-project.md"
        for artifact in updated.artifacts
    )
    assert (tmp_path / "jobs" / "job-interview.json").exists()


def test_interview_mapping_assessment_writes_evidence_based_suitability(monkeypatch, tmp_path):
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
                "- Page 2 method evidence: The agent architecture uses retrieval and ranking to select grounded evidence.",
                "",
                "## Experiments",
                "",
                "- Page 5 experiment evidence: The evaluation compares the agent with baseline workflows.",
                "",
                "## Limitations",
                "",
                "- Page 7 limitation evidence: The system needs human review for reliability risks.",
                "",
                "## Practical Takeaways",
                "",
                "- Method takeaway (source: Core Method, page 2): Use this evidence as the starting point.",
            ]
        ),
        encoding="utf-8",
    )
    (notes_dir / "code-references.md").write_text(
        "\n".join(
            [
                "# Code References",
                "",
                "## Code Mapping Evidence",
                "",
                "- Mapping status: evidence-backed local scan",
                "1. `paperforge/retrieval_agent.py`",
                "   - Matched method terms: `retrieval`, `ranking`",
            ]
        ),
        encoding="utf-8",
    )
    (notes_dir / "doubts.md").write_text(
        "\n".join(
            [
                "# Doubts",
                "",
                "## Open Questions",
                "",
                "- Method question (source: Core Method, page 2): Which retrieval detail needs review?",
            ]
        ),
        encoding="utf-8",
    )
    (notes_dir / "interview-project.md").write_text("# Interview Project Mapping\n", encoding="utf-8")

    updated = run_interview_mapping_assessment(_job())

    mapping_path = notes_dir / "interview-project.md"
    content = mapping_path.read_text(encoding="utf-8")
    assert "- Draft status: interview assessment MVP; needs human review before interview use." in content
    assert "## Suitability" in content
    assert "- Suitability: high" in content
    assert "- Evidence basis: method evidence, experiment evidence, practical takeaway evidence, local code mapping evidence." in content
    assert "## Minimal Demo Version" in content
    assert "- Minimal demo scope: implement or present one method slice tied to the Core Method evidence." in content
    assert "- Candidate code evidence: `notes/code-references.md` has local file-level mapping candidates." in content
    assert "## Risks" in content
    assert "- Risk: limitation or doubt evidence exists; keep final claims conservative." in content
    assert "Not assessed yet." not in content

    step = updated.steps[-1]
    assert step.id == "project.assess_interview_mapping"
    assert step.state == "completed"
    assert step.inputs == [
        "notes/README.md",
        "notes/code-references.md",
        "notes/doubts.md",
        "notes/interview-project.md",
    ]
    assert step.outputs == ["paper-vault/sample-paper/notes/interview-project.md"]


def test_interview_mapping_assessment_marks_partial_when_inputs_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "README.md").write_text("# Sample Paper\n", encoding="utf-8")
    (notes_dir / "interview-project.md").write_text("# Interview Project Mapping\n", encoding="utf-8")

    updated = run_interview_mapping_assessment(_job())

    step = updated.steps[-1]
    assert step.id == "project.assess_interview_mapping"
    assert step.state == "partial"
    assert step.error == "Missing interview assessment inputs: code-references.md, doubts.md"
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
        id="job-interview",
        input_text="sample",
        status="completed",
        paper_slug=metadata.slug,
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
