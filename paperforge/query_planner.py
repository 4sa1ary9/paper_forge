from __future__ import annotations

import json
import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from paperforge.arxiv_client import parse_arxiv_id
from paperforge.llm_client import query_planner_client_from_env


U_NET_TITLE = "U-Net: Convolutional Networks for Biomedical Image Segmentation"


@dataclass(frozen=True)
class QueryPlan:
    original_input: str
    canonical_title: str
    search_query: str
    author_hint: str | None = None
    year_hint: int | None = None
    rationale: str = ""
    confidence: str = "low"
    used_llm: bool = False
    fallback: bool = False
    fallback_reason: str | None = None


class QueryPlannerClient(Protocol):
    def plan_query(self, raw_input: str) -> str:
        """Return a JSON query plan for a raw paper input."""


def plan_paper_query(raw_input: str, client: QueryPlannerClient | None = None) -> QueryPlan:
    cleaned_input = _clean_text(raw_input)
    if not cleaned_input:
        return _raw_fallback(cleaned_input, "Empty input; using raw input fallback.")

    protected_plan = _protected_input_plan(cleaned_input)
    if protected_plan:
        return protected_plan

    alias_plan = _alias_plan(cleaned_input)
    if alias_plan:
        return alias_plan

    if client is None:
        client = query_planner_client_from_env()

    if client is None:
        return _raw_fallback(cleaned_input, "No query planner client configured; using raw input fallback.")

    try:
        return _plan_from_client(cleaned_input, client)
    except Exception as error:
        return _raw_fallback(cleaned_input, f"LLM query plan failed; using raw input fallback. Error: {error}")


def write_query_plan_markdown(plan: QueryPlan, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_query_plan_markdown(plan), encoding="utf-8")
    return output_path


def _protected_input_plan(raw_input: str) -> QueryPlan | None:
    if parse_arxiv_id(raw_input):
        return QueryPlan(
            original_input=raw_input,
            canonical_title=raw_input,
            search_query=raw_input,
            rationale="Input is an arXiv ID or arXiv URL; it was kept unchanged.",
            confidence="high",
        )

    if _looks_like_pdf_url(raw_input):
        return QueryPlan(
            original_input=raw_input,
            canonical_title=raw_input,
            search_query=raw_input,
            rationale="Input is a PDF URL; it was kept unchanged.",
            confidence="high",
        )

    return None


def _alias_plan(raw_input: str) -> QueryPlan | None:
    if _alias_key(raw_input) != "unet":
        return None

    return QueryPlan(
        original_input=raw_input,
        canonical_title=U_NET_TITLE,
        search_query=U_NET_TITLE,
        author_hint="Ronneberger",
        year_hint=2015,
        rationale="Known alias for the original U-Net paper.",
        confidence="high",
    )


def _plan_from_client(raw_input: str, client: QueryPlannerClient) -> QueryPlan:
    response = client.plan_query(raw_input)
    if not response or not response.strip():
        raise ValueError("empty response")

    data = json.loads(response)
    if not isinstance(data, dict):
        raise ValueError("response JSON must be an object")

    canonical_title = _clean_text(str(data.get("canonical_title") or ""))
    search_query = _clean_text(str(data.get("search_query") or canonical_title))
    if not canonical_title and not search_query:
        raise ValueError("response JSON must include canonical_title or search_query")
    canonical_title = canonical_title or search_query
    search_query = search_query or canonical_title

    return QueryPlan(
        original_input=raw_input,
        canonical_title=canonical_title,
        search_query=search_query,
        author_hint=_optional_text(data.get("author_hint")),
        year_hint=_optional_int(data.get("year_hint")),
        rationale=_clean_text(str(data.get("rationale") or "LLM query plan.")),
        confidence=_confidence(data.get("confidence")),
        used_llm=True,
    )


def _raw_fallback(raw_input: str, reason: str) -> QueryPlan:
    return QueryPlan(
        original_input=raw_input,
        canonical_title=raw_input,
        search_query=raw_input,
        rationale=reason,
        confidence="low",
        fallback=True,
        fallback_reason=reason,
    )


def _query_plan_markdown(plan: QueryPlan) -> str:
    fallback = "yes" if plan.fallback else "no"
    used_llm = "yes" if plan.used_llm else "no"
    lines = [
        "# Query Plan",
        "",
        "## Planned Paper Identity",
        "",
        f"- Original input: `{plan.original_input}`",
        f"- Canonical title: {plan.canonical_title or 'not resolved'}",
        f"- Search query: {plan.search_query or 'not resolved'}",
        f"- Author hint: {plan.author_hint or 'none'}",
        f"- Year hint: {plan.year_hint if plan.year_hint is not None else 'none'}",
        f"- Confidence: {plan.confidence}",
        f"- Used LLM: {used_llm}",
        f"- Fallback: {fallback}",
        f"- Fallback reason: {plan.fallback_reason or 'none'}",
        "",
        "## Rationale",
        "",
        plan.rationale or "No rationale provided.",
        "",
    ]
    return "\n".join(lines)


def _looks_like_pdf_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    return parsed.path.lower().endswith(".pdf")


def _alias_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = _clean_text(str(value))
    return text or None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _confidence(value: object) -> str:
    text = _clean_text(str(value or "")).lower()
    return text if text in {"low", "medium", "high"} else "low"


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
