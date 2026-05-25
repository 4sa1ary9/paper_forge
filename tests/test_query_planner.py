import json

import pytest

from paperforge.intake_agent import run_paper_intake
from paperforge.models import PaperMetadata
from paperforge.query_planner import QueryPlan, plan_paper_query, write_query_plan_markdown


U_NET_TITLE = "U-Net: Convolutional Networks for Biomedical Image Segmentation"


@pytest.mark.parametrize("raw_input", ["unet", "u-net", "u net"])
def test_unet_alias_resolves_to_original_paper(raw_input):
    plan = plan_paper_query(raw_input)

    assert plan.original_input == raw_input
    assert plan.canonical_title == U_NET_TITLE
    assert plan.search_query == U_NET_TITLE
    assert plan.author_hint == "Ronneberger"
    assert plan.year_hint == 2015
    assert plan.used_llm is False
    assert plan.fallback is False


@pytest.mark.parametrize(
    "raw_input",
    [
        "1706.03762",
        "https://arxiv.org/abs/1706.03762",
        "https://arxiv.org/pdf/1706.03762.pdf",
        "https://example.test/papers/sample.pdf",
    ],
)
def test_ids_and_urls_are_not_sent_to_llm_or_rewritten(raw_input):
    class ExplodingClient:
        def plan_query(self, _raw_input):
            raise AssertionError("URL and arXiv ID inputs should bypass the LLM")

    plan = plan_paper_query(raw_input, client=ExplodingClient())

    assert plan.original_input == raw_input
    assert plan.canonical_title == raw_input
    assert plan.search_query == raw_input
    assert plan.used_llm is False
    assert plan.fallback is False


def test_fake_llm_json_plan_is_used():
    class FakeClient:
        def plan_query(self, raw_input):
            assert raw_input == "attention paper"
            return json.dumps(
                {
                    "canonical_title": "Attention Is All You Need",
                    "search_query": "Attention Is All You Need",
                    "author_hint": "Vaswani",
                    "year_hint": 2017,
                    "rationale": "The user likely refers to the Transformer paper.",
                    "confidence": "high",
                }
            )

    plan = plan_paper_query("attention paper", client=FakeClient())

    assert plan.canonical_title == "Attention Is All You Need"
    assert plan.search_query == "Attention Is All You Need"
    assert plan.author_hint == "Vaswani"
    assert plan.year_hint == 2017
    assert plan.rationale == "The user likely refers to the Transformer paper."
    assert plan.confidence == "high"
    assert plan.used_llm is True
    assert plan.fallback is False


def test_bad_llm_json_falls_back_to_raw_input():
    class BadClient:
        def plan_query(self, _raw_input):
            return "{not valid json"

    plan = plan_paper_query("rare paper nickname", client=BadClient())

    assert plan.canonical_title == "rare paper nickname"
    assert plan.search_query == "rare paper nickname"
    assert plan.used_llm is False
    assert plan.fallback is True
    assert "fallback" in plan.rationale.lower()


def test_configured_default_llm_client_is_used_when_no_client_is_passed(monkeypatch):
    class FakeDefaultClient:
        def plan_query(self, raw_input):
            assert raw_input == "transformer paper"
            return json.dumps(
                {
                    "canonical_title": "Attention Is All You Need",
                    "search_query": "Attention Is All You Need",
                    "confidence": "high",
                }
            )

    monkeypatch.setattr("paperforge.query_planner.query_planner_client_from_env", lambda: FakeDefaultClient())

    plan = plan_paper_query("transformer paper")

    assert plan.canonical_title == "Attention Is All You Need"
    assert plan.search_query == "Attention Is All You Need"
    assert plan.used_llm is True
    assert plan.fallback is False


def test_query_plan_markdown_records_plan_fields(tmp_path):
    plan = QueryPlan(
        original_input="unet",
        canonical_title=U_NET_TITLE,
        search_query=U_NET_TITLE,
        author_hint="Ronneberger",
        year_hint=2015,
        rationale="Known alias for the original U-Net paper.",
        confidence="high",
        used_llm=False,
        fallback=False,
        fallback_reason=None,
    )
    output_path = tmp_path / "query-plan.md"

    written = write_query_plan_markdown(plan, output_path)

    assert written == output_path
    content = output_path.read_text(encoding="utf-8")
    assert "# Query Plan" in content
    assert "- Original input: `unet`" in content
    assert f"- Canonical title: {U_NET_TITLE}" in content
    assert f"- Search query: {U_NET_TITLE}" in content
    assert "- Author hint: Ronneberger" in content
    assert "- Year hint: 2015" in content
    assert "- Fallback: no" in content
    assert "Known alias for the original U-Net paper." in content


def test_intake_uses_query_plan_before_arxiv_resolution(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERFORGE_DATA_DIR", str(tmp_path))
    observed_queries = []

    def fake_resolve_paper_metadata(query):
        observed_queries.append(query)
        return PaperMetadata(
            slug="u-net-convolutional-networks-for-biomedical-image-segmentation",
            title=U_NET_TITLE,
            authors=["Olaf Ronneberger", "Philipp Fischer", "Thomas Brox"],
            year=2015,
            venue="arXiv",
            abstract="U-Net paper metadata.",
            canonical_url="https://arxiv.org/abs/1505.04597",
            pdf_url="https://arxiv.org/pdf/1505.04597",
            source_url="https://arxiv.org/e-print/1505.04597",
            github_candidates=[],
            created_at="2026-05-24T00:00:00+00:00",
            status="intake_completed",
        )

    monkeypatch.setattr("paperforge.intake_agent.resolve_paper_metadata", fake_resolve_paper_metadata)

    job = run_paper_intake("unet")

    assert observed_queries == [U_NET_TITLE]
    assert [step.id for step in job.steps[:2]] == ["query.plan_paper_identity", "intake.resolve_identity"]
    query_plan_path = (
        tmp_path
        / "paper-vault"
        / "u-net-convolutional-networks-for-biomedical-image-segmentation"
        / "notes"
        / "query-plan.md"
    )
    assert query_plan_path.exists()
    assert U_NET_TITLE in query_plan_path.read_text(encoding="utf-8")
    assert any(artifact.label == "Query plan" and artifact.path.endswith("notes/query-plan.md") for artifact in job.artifacts)
