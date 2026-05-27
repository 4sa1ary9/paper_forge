import json

from paperforge.batch_runner import run_batch_intake
from paperforge.models import PaperMetadata, ResearchJob


def test_batch_intake_creates_jobs_for_multiple_lines_and_skips_empty(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    calls = []

    def fake_intake(input_text, *, use_query_planner=True):
        calls.append((input_text, use_query_planner))
        return _job(input_text, slug=input_text.replace(" ", "-"), job_id=f"job-{len(calls)}")

    result = run_batch_intake(
        "paper one\n\n  paper two  \n",
        intake_runner=fake_intake,
        use_query_planner=False,
    )

    assert [call[0] for call in calls] == ["paper one", "paper two"]
    assert all(call[1] is False for call in calls)
    assert result.status == "completed"
    assert result.total_inputs == 2
    assert [item.job_id for item in result.items] == ["job-1", "job-2"]
    assert (tmp_path / "batches" / f"{result.batch_id}.json").exists()

    saved = json.loads(result.json_path.read_text(encoding="utf-8"))
    assert saved["batch_id"] == result.batch_id
    assert saved["status"] == "completed"
    assert [item["input"] for item in saved["items"]] == ["paper one", "paper two"]


def test_batch_intake_single_failure_does_not_block_following_jobs(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    calls = []

    def fake_intake(input_text, *, use_query_planner=True):
        calls.append(input_text)
        if input_text == "bad paper":
            raise RuntimeError("resolver unavailable")
        return _job(input_text, slug=f"slug-{len(calls)}", job_id=f"job-{len(calls)}")

    result = run_batch_intake("good paper\nbad paper\nlater paper", intake_runner=fake_intake)

    assert calls == ["good paper", "bad paper", "later paper"]
    assert result.status == "partial"
    assert [item.status for item in result.items] == ["completed", "failed", "completed"]
    assert result.items[1].job_id is None
    assert result.items[1].slug is None
    assert result.items[1].error == "resolver unavailable"
    assert result.items[2].job_id == "job-3"


def test_batch_intake_summary_files_record_each_paper(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))

    def fake_intake(input_text, *, use_query_planner=True):
        return _job(input_text, slug="stable-slug", job_id="job-stable", status="partial")

    result = run_batch_intake("sample paper", intake_runner=fake_intake)

    assert result.status == "partial"
    assert result.summary_path.exists()
    summary = result.summary_path.read_text(encoding="utf-8")
    assert "# Batch Intake Summary" in summary
    assert "| sample paper | job-stable | stable-slug | partial | - |" in summary
    assert "Sequential intake only; no parallel execution and no literature review summary." in summary

    saved = json.loads(result.json_path.read_text(encoding="utf-8"))
    assert saved["items"] == [
        {
            "input": "sample paper",
            "job_id": "job-stable",
            "slug": "stable-slug",
            "status": "partial",
            "error": None,
        }
    ]


def test_batch_intake_empty_input_returns_needs_user_input(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))

    result = run_batch_intake("\n  \n", intake_runner=lambda *_args, **_kwargs: None)

    assert result.status == "needs_user_input"
    assert result.total_inputs == 0
    assert result.items == []
    assert result.json_path.exists()
    assert result.summary_path.exists()


def _job(input_text: str, *, slug: str, job_id: str, status: str = "completed") -> ResearchJob:
    metadata = PaperMetadata(
        slug=slug,
        title=input_text.title(),
        authors=["Ada Lovelace"],
        year=2026,
        venue="arXiv",
        abstract="A sample paper.",
        canonical_url="https://example.test/abs/sample",
        pdf_url="https://example.test/paper.pdf",
        source_url=None,
        github_candidates=[],
        created_at="2026-05-25T00:00:00+00:00",
        status="intake_completed" if status == "completed" else "intake_partial",
    )
    return ResearchJob(
        id=job_id,
        input_text=input_text,
        status=status,
        paper_slug=slug,
        created_at="2026-05-25T00:00:00+00:00",
        updated_at="2026-05-25T00:00:00+00:00",
        metadata=metadata,
        steps=[],
        artifacts=[],
    )
