from paperforge.arxiv_client import parse_arxiv_id


def test_parse_arxiv_abs_url():
    assert parse_arxiv_id("https://arxiv.org/abs/1706.03762") == "1706.03762"


def test_parse_arxiv_pdf_url():
    assert parse_arxiv_id("https://arxiv.org/pdf/1706.03762.pdf") == "1706.03762"


def test_parse_bare_arxiv_id():
    assert parse_arxiv_id("1706.03762v7") == "1706.03762v7"

