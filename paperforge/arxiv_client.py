from __future__ import annotations

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from paperforge.models import PaperMetadata
from paperforge.slug import slugify_title
from paperforge.steps import now_iso


ARXIV_NS = {"atom": "http://www.w3.org/2005/Atom"}


def parse_arxiv_id(text: str) -> str | None:
    value = text.strip()
    url_match = re.search(r"arxiv\.org/(?:abs|pdf|e-print)/([^?#\s]+)", value, flags=re.I)
    candidate = url_match.group(1) if url_match else value
    candidate = re.sub(r"\.pdf$", "", candidate, flags=re.I)

    modern = re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", candidate, flags=re.I)
    if modern:
        return modern.group(0)

    legacy = re.fullmatch(r"[a-z-]+(?:\.[A-Z]{2})?/\d{7}(v\d+)?", candidate, flags=re.I)
    if legacy:
        return legacy.group(0)

    return None


def resolve_paper_metadata(input_text: str) -> PaperMetadata:
    arxiv_id = parse_arxiv_id(input_text)
    if arxiv_id:
        query = f"id_list={urllib.parse.quote(arxiv_id)}"
    else:
        query = f"search_query=ti:{urllib.parse.quote(input_text.strip())}&start=0&max_results=1"

    url = f"https://export.arxiv.org/api/query?{query}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PaperForgeAgent/0.1 contact=local-dev",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        xml_text = response.read().decode("utf-8")

    root = ET.fromstring(xml_text)
    entry = root.find("atom:entry", ARXIV_NS)
    if entry is None:
        raise ValueError("No arXiv paper matched the input")

    return _entry_to_metadata(entry)


def _entry_to_metadata(entry: ET.Element) -> PaperMetadata:
    title = _clean_text(_text(entry, "title") or "Untitled Paper")
    canonical_url = _text(entry, "id")
    arxiv_id = canonical_url.rsplit("/", 1)[-1] if canonical_url else None
    pdf_url = _find_pdf_url(entry) or (f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else None)
    source_url = f"https://arxiv.org/e-print/{arxiv_id}" if arxiv_id else None
    published = _text(entry, "published")

    return PaperMetadata(
        slug=slugify_title(title),
        title=title,
        authors=_authors(entry),
        year=_year_from_published(published),
        venue="arXiv",
        abstract=_clean_text(_text(entry, "summary") or "") or None,
        canonical_url=canonical_url,
        pdf_url=pdf_url,
        source_url=source_url,
        github_candidates=[],
        created_at=now_iso(),
        status="intake_completed",
    )


def _text(entry: ET.Element, tag: str) -> str | None:
    node = entry.find(f"atom:{tag}", ARXIV_NS)
    return node.text if node is not None else None


def _authors(entry: ET.Element) -> list[str]:
    authors: list[str] = []
    for author in entry.findall("atom:author", ARXIV_NS):
        name = author.find("atom:name", ARXIV_NS)
        if name is not None and name.text:
            authors.append(_clean_text(name.text))
    return authors


def _find_pdf_url(entry: ET.Element) -> str | None:
    for link in entry.findall("atom:link", ARXIV_NS):
        if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
            return link.attrib.get("href")
    return None


def _year_from_published(value: str | None) -> int | None:
    if not value or len(value) < 4:
        return None
    try:
        return int(value[:4])
    except ValueError:
        return None


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
