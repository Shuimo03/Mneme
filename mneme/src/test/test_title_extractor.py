from src.storage.title_extractor import extract_title


def test_extract_title_reads_first_heading() -> None:
    markdown = """
    # Meta Ray Ban Display From Zero To Polish

    Intro paragraph.
    """

    assert extract_title(markdown, "fallback-title") == "Meta Ray Ban Display From Zero To Polish"


def test_extract_title_skips_logo_heading_and_sanitizes_content() -> None:
    markdown = """
    # [Meta Engineering](https://engineering.fb.com)
    # Meta: Display / Vision?
    """

    assert extract_title(markdown, "fallback-title") == "Meta Display Vision"


def test_extract_title_falls_back_to_slug_when_heading_missing() -> None:
    markdown = "No heading here"

    assert extract_title(markdown, "meta-ray-ban") == "Meta Ray Ban"
