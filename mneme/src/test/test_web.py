from types import SimpleNamespace

from src.adapters.web import extract_crawl_result_text, normalize_content_text


def test_normalize_content_text_strips_html_and_compacts_whitespace() -> None:
    raw = "<main><h1>Title</h1><script>ignored()</script><p>Hello   world</p></main>"

    normalized = normalize_content_text(raw)

    assert normalized == "Title Hello world"


def test_extract_crawl_result_text_prefers_markdown() -> None:
    result = SimpleNamespace(
        markdown=SimpleNamespace(fit_markdown="## Fit heading\n\nUseful content", raw_markdown="# Raw"),
        cleaned_html="<p>Fallback</p>",
        html="<p>Raw</p>",
        extracted_content=None,
    )

    extracted = extract_crawl_result_text(result)

    assert extracted == "Fit heading Useful content"


def test_extract_crawl_result_text_falls_back_to_html_fields() -> None:
    result = SimpleNamespace(
        markdown=None,
        cleaned_html="<article><h1>Title</h1><p>Body copy</p></article>",
        html="<p>Ignored because cleaned_html exists</p>",
        extracted_content=None,
    )

    extracted = extract_crawl_result_text(result)

    assert extracted == "Title Body copy"
