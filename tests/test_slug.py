from paperforge.slug import slugify_title


def test_slugify_title_creates_stable_paper_slug():
    assert slugify_title("Attention Is All You Need") == "attention-is-all-you-need"


def test_slugify_title_falls_back_for_empty_slug():
    assert slugify_title("!!!") == "untitled-paper"

