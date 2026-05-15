from unittest.mock import MagicMock, patch

from app.ingestion.ocr_refine import pages_need_ocr_refine, refine_ocr_pages


def test_pages_need_ocr_refine_only_when_ocr_with_text():
    assert not pages_need_ocr_refine([{"source": "native", "text": "hello"}])
    assert not pages_need_ocr_refine([{"source": "ocr", "text": ""}])
    assert pages_need_ocr_refine([{"source": "ocr", "text": "scan text", "page": 1}])


def test_refine_skips_when_disabled():
    pages = [{"page": 1, "text": "raw", "source": "ocr", "ocr_confidence": 80.0}]
    out = refine_ocr_pages(pages, {"ocr_refine": {"enabled": False}})
    assert out == pages


def test_refine_passthrough_native_pages():
    pages = [{"page": 1, "text": "native text", "source": "native"}]
    out = refine_ocr_pages(pages, {"ocr_refine": {"enabled": True}})
    assert out == pages


@patch("app.ingestion.ocr_refine.get_groq_runtime")
@patch("app.ingestion.ocr_refine.get_ocr_refine_prompts")
def test_refine_ocr_page_calls_groq(mock_prompts, mock_runtime):
    mock_prompts.return_value = MagicMock(system="sys", user="page {{ page_number }}\n{{ ocr_text }}")
    client = MagicMock()
    choice = MagicMock()
    choice.message.content = "Cleaned witness statement."
    client.chat.completions.create.return_value = MagicMock(choices=[choice])
    mock_runtime.return_value = MagicMock(
        client=client,
        model="test-model",
        temperature=0.1,
        max_tokens=1024,
    )

    pages = [{"page": 2, "text": "Wltness staternent", "source": "ocr", "ocr_confidence": 72.0}]
    out = refine_ocr_pages(pages, {"ocr_refine": {"enabled": True}})

    assert len(out) == 1
    assert out[0]["text"] == "Cleaned witness statement."
    assert out[0]["source"] == "ocr_refined"
    assert out[0]["ocr_confidence"] == 72.0
    assert out[0]["page"] == 2
    client.chat.completions.create.assert_called_once()
