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


def test_deep_note_writer_updates_ready_background_section(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)

    readme_path = notes_dir / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Sample Paper",
                "",
                "## TL;DR",
                "",
                "- Not generated yet.",
                "",
                "## Paper Overview",
                "",
                "- Not generated yet.",
                "",
                "## Background and Motivation",
                "",
                "- Not generated yet.",
                "",
                "## Core Method",
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
                "| TL;DR | blocked | metadata, PDF text evidence map |",
                "| Paper Overview | blocked | PDF text evidence map |",
                "| Background and Motivation | ready | PDF text evidence map, external source log |",
                "| Core Method | blocked | PDF text evidence map, image manifest |",
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
                "Introduction Existing systems struggle to keep research notes grounded in evidence.",
                "```",
                "",
                "### Page 2",
                "",
                "```text",
                "The motivation is to keep every generated note traceable to source pages.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    updated = run_deep_note_writing(_job())

    content = readme_path.read_text(encoding="utf-8")
    assert "## TL;DR\n\n- Not generated yet." in content
    assert "## Paper Overview\n\n- Not generated yet." in content
    assert "## Background and Motivation" in content
    assert "- Primary background evidence pages: 1, 2." in content
    assert "- Page 1 motivation evidence: Introduction Existing systems struggle to keep research notes grounded in evidence." in content
    assert "- Page 2 motivation evidence: The motivation is to keep every generated note traceable to source pages." in content
    assert "- Manual review: confirm these excerpts actually describe the paper background and motivation." in content
    assert "## Core Method\n\n- Not generated yet." in content

    step = updated.steps[-1]
    assert step.id == "note.write_deep_note_mvp"
    assert step.state == "completed"


def test_deep_note_writer_prefers_background_pages_over_figure_pages(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)

    readme_path = notes_dir / "README.md"
    readme_path.write_text("# Sample Paper\n\n## Background and Motivation\n\n- Not generated yet.\n", encoding="utf-8")
    (notes_dir / "deep-note-plan.md").write_text(
        "\n".join(
            [
                "# Deep Note Plan",
                "",
                "| Section | Status | Evidence |",
                "| --- | --- | --- |",
                "| Background and Motivation | ready | PDF text evidence map, external source log |",
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
                "Introduction This paper starts from a limitation in current research workflows.",
                "```",
                "",
                "### Page 2",
                "",
                "```text",
                "Figure 1: The model architecture.",
                "```",
                "",
                "### Page 3",
                "",
                "```text",
                "The motivation is to make generated notes easier to audit.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    run_deep_note_writing(_job())

    content = readme_path.read_text(encoding="utf-8")
    assert "- Primary background evidence pages: 1, 3." in content
    assert "Figure 1: The model architecture." not in content


def test_deep_note_writer_updates_ready_core_method_with_page_and_figure_evidence(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    notes_dir = paper_dir / "notes"
    images_dir = paper_dir / "images"
    notes_dir.mkdir(parents=True)
    images_dir.mkdir(parents=True)

    readme_path = notes_dir / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Sample Paper",
                "",
                "## TL;DR",
                "",
                "- Not generated yet.",
                "",
                "## Background and Motivation",
                "",
                "- Not generated yet.",
                "",
                "## Core Method",
                "",
                "- Not generated yet.",
                "",
                "## Experiments",
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
                "| TL;DR | blocked | metadata, PDF text evidence map |",
                "| Background and Motivation | blocked | PDF text evidence map, external source log |",
                "| Core Method | ready | PDF text evidence map, image manifest |",
                "| Experiments | blocked | PDF text evidence map, image manifest |",
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
                "Introduction This paper starts from a limitation in current workflows.",
                "```",
                "",
                "### Page 2",
                "",
                "```text",
                "Model Architecture The method stacks self-attention and feed-forward layers in an encoder-decoder model.",
                "```",
                "",
                "### Page 3",
                "",
                "```text",
                "Scaled Dot-Product Attention computes weights from query and key compatibility before combining values.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (images_dir / "manifest.md").write_text(
        "\n".join(
            [
                "# Extracted Figures",
                "",
                "| Index | File | Page | Size | Source |",
                "| --- | --- | --- | --- | --- |",
                "| 1 | `fig001_page2_img1.png` | 2 | 640x480 | 42 |",
                "| 2 | `fig002_page3_img1.png` | 3 | 320x240 | 43 |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    updated = run_deep_note_writing(_job())

    content = readme_path.read_text(encoding="utf-8")
    assert "## TL;DR\n\n- Not generated yet." in content
    assert "## Background and Motivation\n\n- Not generated yet." in content
    assert "## Core Method" in content
    assert "- Primary method evidence pages: 2, 3." in content
    assert (
        "- Page 2 method evidence: Model Architecture The method stacks self-attention and feed-forward layers "
        "in an encoder-decoder model."
    ) in content
    assert (
        "- Figure evidence: `../images/manifest.md` lists `fig001_page2_img1.png` from page 2 and "
        "`fig002_page3_img1.png` from page 3."
    ) in content
    assert "- Manual review: confirm these excerpts and figures actually describe the core method." in content
    assert "## Experiments\n\n- Not generated yet." in content

    step = updated.steps[-1]
    assert step.id == "note.write_deep_note_mvp"
    assert step.state == "completed"


def test_deep_note_writer_requires_image_manifest_for_ready_core_method(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)

    readme_path = notes_dir / "README.md"
    original_readme = "# Sample Paper\n\n## Core Method\n\n- Not generated yet.\n"
    readme_path.write_text(original_readme, encoding="utf-8")
    (notes_dir / "deep-note-plan.md").write_text(
        "\n".join(
            [
                "# Deep Note Plan",
                "",
                "| Section | Status | Evidence |",
                "| --- | --- | --- |",
                "| Core Method | ready | PDF text evidence map, image manifest |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (notes_dir / "evidence-map.md").write_text(
        "# PDF Text Evidence Map\n\n### Page 1\n\n```text\nModel Architecture The method has evidence.\n```\n",
        encoding="utf-8",
    )

    updated = run_deep_note_writing(_job())

    assert readme_path.read_text(encoding="utf-8") == original_readme
    step = updated.steps[-1]
    assert step.id == "note.write_deep_note_mvp"
    assert step.state == "partial"
    assert step.error == "Image manifest is required for Core Method writing"
    assert updated.status == "partial"


def test_deep_note_writer_updates_ready_experiments_with_page_and_visual_evidence(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    notes_dir = paper_dir / "notes"
    images_dir = paper_dir / "images"
    notes_dir.mkdir(parents=True)
    images_dir.mkdir(parents=True)

    readme_path = notes_dir / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Sample Paper",
                "",
                "## Core Method",
                "",
                "- Not generated yet.",
                "",
                "## Experiments",
                "",
                "- Not generated yet.",
                "",
                "## Limitations",
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
                "| Core Method | blocked | PDF text evidence map, image manifest |",
                "| Experiments | ready | PDF text evidence map, image manifest |",
                "| Limitations | blocked | PDF text evidence map |",
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
                "Introduction This paper starts from a limitation in current workflows.",
                "```",
                "",
                "### Page 2",
                "",
                "```text",
                "Experiments compare the model against strong baselines on translation benchmarks.",
                "```",
                "",
                "### Page 3",
                "",
                "```text",
                "Table 1 reports BLEU results and ablation scores for different model variants.",
                "```",
                "",
                "### Page 4",
                "",
                "```text",
                "Training details include batch size, optimizer settings, and learning rate schedule.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (images_dir / "manifest.md").write_text(
        "\n".join(
            [
                "# Extracted Figures",
                "",
                "| Index | File | Page | Size | Source |",
                "| --- | --- | --- | --- | --- |",
                "| 1 | `fig001_page3_img1.png` | 3 | 640x480 | 42 |",
                "| 2 | `fig002_page4_img1.png` | 4 | 320x240 | 43 |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    updated = run_deep_note_writing(_job())

    content = readme_path.read_text(encoding="utf-8")
    assert "## Core Method\n\n- Not generated yet." in content
    assert "## Experiments" in content
    assert "- Primary experiment evidence pages: 2, 3." in content
    assert "- Page 2 experiment evidence: Experiments compare the model against strong baselines on translation benchmarks." in content
    assert "- Table/result evidence pages: 3." in content
    assert "- Training detail evidence pages: 4." in content
    assert (
        "- Figure/table evidence: `../images/manifest.md` lists `fig001_page3_img1.png` from page 3 and "
        "`fig002_page4_img1.png` from page 4."
    ) in content
    assert "- Manual review: confirm these excerpts and visuals actually describe the experiments." in content
    assert "## Limitations\n\n- Not generated yet." in content

    step = updated.steps[-1]
    assert step.id == "note.write_deep_note_mvp"
    assert step.state == "completed"
    assert step.inputs == [
        "notes/deep-note-plan.md",
        "notes/evidence-map.md",
        "notes/README.md",
        "images/manifest.md",
    ]


def test_deep_note_writer_does_not_treat_substring_matches_as_experiment_evidence(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    notes_dir = paper_dir / "notes"
    images_dir = paper_dir / "images"
    notes_dir.mkdir(parents=True)
    images_dir.mkdir(parents=True)

    readme_path = notes_dir / "README.md"
    readme_path.write_text("# Sample Paper\n\n## Experiments\n\n- Not generated yet.\n", encoding="utf-8")
    (notes_dir / "deep-note-plan.md").write_text(
        "\n".join(
            [
                "# Deep Note Plan",
                "",
                "| Section | Status | Evidence |",
                "| --- | --- | --- |",
                "| Experiments | ready | PDF text evidence map, image manifest |",
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
                "The attention layer computes output values, resulting in final values.",
                "```",
                "",
                "### Page 2",
                "",
                "```text",
                "Self-attention could yield more interpretable models.",
                "```",
                "",
                "### Page 3",
                "",
                "```text",
                "Table 2 reports BLEU results on translation benchmarks.",
                "```",
                "",
                "### Page 4",
                "",
                "```text",
                "Training data uses WMT 2014 datasets with batched sentence pairs.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (images_dir / "manifest.md").write_text(
        "\n".join(
            [
                "# Extracted Figures",
                "",
                "| Index | File | Page | Size | Source |",
                "| --- | --- | --- | --- | --- |",
                "| 1 | `fig001_page3_img1.png` | 3 | 640x480 | 42 |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    run_deep_note_writing(_job())

    content = readme_path.read_text(encoding="utf-8")
    assert "- Primary experiment evidence pages: 3." in content
    assert "resulting in final values" not in content
    assert "interpretable models" not in content
    assert "- Table/result evidence pages: 3." in content
    assert "- Training detail evidence pages: 4." in content


def test_deep_note_writer_updates_ready_limitations_with_page_evidence(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)

    readme_path = notes_dir / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Sample Paper",
                "",
                "## Experiments",
                "",
                "- Not generated yet.",
                "",
                "## Limitations",
                "",
                "- Not generated yet.",
                "",
                "## Practical Takeaways",
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
                "| Experiments | blocked | PDF text evidence map, image manifest |",
                "| Limitations | ready | PDF text evidence map |",
                "| Practical Takeaways | blocked | generated method, experiment, limitation, and Deep Q&A evidence notes |",
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
                "Introduction This paper starts from a limitation in current workflows.",
                "```",
                "",
                "### Page 2",
                "",
                "```text",
                "A limitation is that the current method still needs manual review for ambiguous evidence.",
                "```",
                "",
                "### Page 3",
                "",
                "```text",
                "Future work should evaluate the approach on more domains and larger datasets.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    updated = run_deep_note_writing(_job())

    content = readme_path.read_text(encoding="utf-8")
    assert "## Experiments\n\n- Not generated yet." in content
    assert "## Limitations" in content
    assert "- Primary limitation evidence pages: 1, 2." in content
    assert "- Page 2 limitation evidence: A limitation is that the current method still needs manual review for ambiguous evidence." in content
    assert "- Manual review: confirm these excerpts actually describe limitations, risks, or future work." in content
    assert "## Practical Takeaways\n\n- Not generated yet." in content

    step = updated.steps[-1]
    assert step.id == "note.write_deep_note_mvp"
    assert step.state == "completed"
    assert step.inputs == ["notes/deep-note-plan.md", "notes/evidence-map.md", "notes/README.md"]


def test_deep_note_writer_does_not_treat_substring_matches_as_limitation_evidence(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    notes_dir = tmp_path / "paper-vault" / "sample-paper" / "notes"
    notes_dir.mkdir(parents=True)

    readme_path = notes_dir / "README.md"
    readme_path.write_text("# Sample Paper\n\n## Limitations\n\n- Not generated yet.\n", encoding="utf-8")
    (notes_dir / "deep-note-plan.md").write_text(
        "\n".join(
            [
                "# Deep Note Plan",
                "",
                "| Section | Status | Evidence |",
                "| --- | --- | --- |",
                "| Limitations | ready | PDF text evidence map |",
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
                "The model has unlimited access to synthetic examples in this toy setup.",
                "```",
                "",
                "### Page 2",
                "",
                "```text",
                "Future work should test whether the method fails under noisy inputs.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    run_deep_note_writing(_job())

    content = readme_path.read_text(encoding="utf-8")
    assert "- Primary limitation evidence pages: 2." in content
    assert "unlimited access" not in content
    assert "- Page 2 limitation evidence: Future work should test whether the method fails under noisy inputs." in content


def test_deep_note_writer_updates_ready_deep_qa_from_generated_evidence_notes(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    notes_dir = paper_dir / "notes"
    images_dir = paper_dir / "images"
    notes_dir.mkdir(parents=True)
    images_dir.mkdir(parents=True)

    readme_path = notes_dir / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Sample Paper",
                "",
                "## Core Method",
                "",
                "- Not generated yet.",
                "",
                "## Experiments",
                "",
                "- Not generated yet.",
                "",
                "## Deep Q&A",
                "",
                "- Not generated yet.",
                "",
                "## Limitations",
                "",
                "- Not generated yet.",
                "",
                "## Practical Takeaways",
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
                "| Core Method | ready | PDF text evidence map, image manifest |",
                "| Experiments | ready | PDF text evidence map, image manifest |",
                "| Limitations | ready | PDF text evidence map |",
                "| Deep Q&A | ready | generated method, experiment, and limitation evidence notes |",
                "| Practical Takeaways | blocked | generated method, experiment, limitation, and Deep Q&A evidence notes |",
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
                "Model Architecture The method stacks attention layers in an encoder-decoder model.",
                "```",
                "",
                "### Page 2",
                "",
                "```text",
                "Table 2 reports BLEU results on translation benchmarks.",
                "```",
                "",
                "### Page 3",
                "",
                "```text",
                "Future work should test whether the method fails under noisy inputs.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (images_dir / "manifest.md").write_text(
        "\n".join(
            [
                "# Extracted Figures",
                "",
                "| Index | File | Page | Size | Source |",
                "| --- | --- | --- | --- | --- |",
                "| 1 | `fig001_page1_img1.png` | 1 | 640x480 | 42 |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    updated = run_deep_note_writing(_job())

    content = readme_path.read_text(encoding="utf-8")
    assert "## Deep Q&A" in content
    assert (
        "- Method question (source: Core Method, page 1): Which method detail in this evidence still needs "
        "manual explanation before finalizing the note?"
    ) in content
    assert (
        "- Experiment question (source: Experiments, page 2): Which result, baseline, or training setting in "
        "this evidence needs verification?"
    ) in content
    assert (
        "- Limitation question (source: Limitations, page 3): What limitation, risk, or future-work item should "
        "be checked before using this paper as project evidence?"
    ) in content
    assert "- Manual review: answer these questions only after checking the cited source pages." in content
    assert "## Practical Takeaways\n\n- Not generated yet." in content

    step = updated.steps[-1]
    assert step.id == "note.write_deep_note_mvp"
    assert step.state == "completed"


def test_deep_note_writer_updates_ready_practical_takeaways_from_generated_sections(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    paper_dir = tmp_path / "paper-vault" / "sample-paper"
    notes_dir = paper_dir / "notes"
    images_dir = paper_dir / "images"
    notes_dir.mkdir(parents=True)
    images_dir.mkdir(parents=True)

    readme_path = notes_dir / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Sample Paper",
                "",
                "## Core Method",
                "",
                "- Not generated yet.",
                "",
                "## Experiments",
                "",
                "- Not generated yet.",
                "",
                "## Deep Q&A",
                "",
                "- Not generated yet.",
                "",
                "## Limitations",
                "",
                "- Not generated yet.",
                "",
                "## Practical Takeaways",
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
                "| Core Method | ready | PDF text evidence map, image manifest |",
                "| Experiments | ready | PDF text evidence map, image manifest |",
                "| Limitations | ready | PDF text evidence map |",
                "| Deep Q&A | ready | generated method, experiment, and limitation evidence notes |",
                "| Practical Takeaways | ready | generated method, experiment, limitation, and Deep Q&A evidence notes |",
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
                "Model Architecture The method stacks attention layers in an encoder-decoder model.",
                "```",
                "",
                "### Page 2",
                "",
                "```text",
                "Table 2 reports BLEU results on translation benchmarks.",
                "```",
                "",
                "### Page 3",
                "",
                "```text",
                "Future work should test whether the method fails under noisy inputs.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (images_dir / "manifest.md").write_text(
        "\n".join(
            [
                "# Extracted Figures",
                "",
                "| Index | File | Page | Size | Source |",
                "| --- | --- | --- | --- | --- |",
                "| 1 | `fig001_page1_img1.png` | 1 | 640x480 | 42 |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    updated = run_deep_note_writing(_job())

    content = readme_path.read_text(encoding="utf-8")
    assert "## Practical Takeaways" in content
    assert (
        "- Method takeaway (source: Core Method, page 1): Use this evidence as the starting point for "
        "explaining the paper's core mechanism."
    ) in content
    assert (
        "- Experiment takeaway (source: Experiments, page 2): Verify what was measured before drawing "
        "practical conclusions from the result evidence."
    ) in content
    assert (
        "- Limitation takeaway (source: Limitations, page 3): Treat this evidence as a constraint or risk "
        "to check before applying the method."
    ) in content
    assert (
        "- Learning follow-up (source: Deep Q&A): Answer the generated questions before turning these notes "
        "into project or interview claims."
    ) in content
    assert "- Manual review: these takeaways are evidence prompts, not project recommendations." in content
    assert "Minimal Demo" not in content
    assert "Suitability" not in content

    step = updated.steps[-1]
    assert step.id == "note.write_deep_note_mvp"
    assert step.state == "completed"


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
