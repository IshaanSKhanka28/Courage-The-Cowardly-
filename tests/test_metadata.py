import pytest

from rag.metadata import ALL_CITIES, NATIONAL_STATE, UNSPECIFIED, DocumentFormatError, parse_document

WELL_FORMED_DOC = """SOURCE: Test Source
TYPE: official_advisory
SECTOR: traffic
STATE: Maharashtra
CITY: Mumbai
URL_OR_REF: https://example.com/doc
---
This is the body.

It has two paragraphs.
"""

NATIONAL_DOC = """SOURCE: IMD
TYPE: official_advisory
SECTOR: traffic
STATE: National
CITY: ALL
URL_OR_REF: https://example.com/national
---
Applies everywhere.
"""


class TestParseDocument:
    def test_parses_well_formed_header_and_body(self):
        doc = parse_document(WELL_FORMED_DOC, file_path="test.txt")
        assert doc.source == "Test Source"
        assert doc.type == "official_advisory"
        assert doc.sector == "traffic"
        assert doc.state == "Maharashtra"
        assert doc.city == "Mumbai"
        assert doc.url_or_ref == "https://example.com/doc"
        assert "two paragraphs" in doc.body
        assert doc.needs_review is False

    def test_national_scope_sentinel_values(self):
        doc = parse_document(NATIONAL_DOC, file_path="national.txt")
        assert doc.state == NATIONAL_STATE
        assert doc.city == ALL_CITIES
        assert doc.needs_review is False

    def test_missing_state_is_flagged_not_guessed(self):
        text = WELL_FORMED_DOC.replace("STATE: Maharashtra\n", "STATE: \n")
        doc = parse_document(text, file_path="missing_state.txt")
        assert doc.state == UNSPECIFIED
        assert doc.needs_review is True

    def test_missing_city_is_flagged_not_guessed(self):
        text = WELL_FORMED_DOC.replace("CITY: Mumbai\n", "CITY: \n")
        doc = parse_document(text, file_path="missing_city.txt")
        assert doc.city == UNSPECIFIED
        assert doc.needs_review is True

    def test_missing_separator_raises(self):
        text = WELL_FORMED_DOC.replace("---\n", "")
        with pytest.raises(DocumentFormatError):
            parse_document(text, file_path="no_separator.txt")

    def test_missing_required_field_raises(self):
        text = WELL_FORMED_DOC.replace("SOURCE: Test Source\n", "")
        with pytest.raises(DocumentFormatError):
            parse_document(text, file_path="missing_source.txt")
