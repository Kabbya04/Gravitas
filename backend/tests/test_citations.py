import json

from app.llm.citations import collect_citation_labels, draft_json_to_markdown, validate_citations_in_draft


def test_collect_citation_labels():
    assert collect_citation_labels("See [E1] and [E2].") == {"E1", "E2"}


def test_validate_citations_ok():
    draft = {
        "title": "T",
        "sections": [{"heading": "H", "bullets": ["Fact one [E1].", "Fact two [E2] and more."]}],
    }
    issues = validate_citations_in_draft(draft, {"E1", "E2"})
    assert issues == []


def test_validate_citations_unknown_tag():
    draft = {"title": "T", "sections": [{"heading": "H", "bullets": ["Bad [E99]."]}]}
    issues = validate_citations_in_draft(draft, {"E1"})
    assert any("E99" in i for i in issues)


def test_draft_json_to_markdown_roundtrip_shape():
    d = {"title": "Case", "sections": [{"heading": "Facts", "bullets": ["A [E1]"]}]}
    md = draft_json_to_markdown(d)
    assert "Case" in md and "[E1]" in md


def test_json_roundtrip_in_blob():
    draft = {"title": "T", "sections": []}
    blob = json.dumps(draft)
    assert collect_citation_labels(blob) == set()
