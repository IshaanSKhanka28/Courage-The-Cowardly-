"""Parsing for the curated-document header format used under docs/<sector>/*.txt.

Header format (fields in any order, one per line, before a lone "---" separator):

    SOURCE: <publication/organization name>
    TYPE: official_advisory | municipal_report | news_secondary | government_guideline
    SECTOR: <sector>
    STATE: <Indian state/UT name> | National
    CITY: <city name> | ALL | state-wide | multiple
    URL_OR_REF: <url>
    ---
    <body text>

STATE "National" is a sentinel for documents whose content applies to every
state (e.g. a nationwide IMD terminology standard, or an NDMA guideline
issued for every state).

CITY has three non-city-name sentinels, all of which retrieval treats as
matching *any* city query within a matching state:
    - "ALL"        - paired with STATE "National": applies everywhere.
    - "state-wide"  - applies to an entire state but isn't city-specific
                      (e.g. a state agricultural university's general
                      package of practices).
    - "multiple"   - explicitly names more than one city/district rather
                      than being city-specific OR generically state-wide
                      (e.g. a regional bulletin that covers a named list of
                      several districts). Put the specific list in the body,
                      not in this field - keep CITY exactly "multiple" so it
                      matches the sentinel.
"""

from dataclasses import dataclass

NATIONAL_STATE = "National"
ALL_CITIES = "ALL"
STATEWIDE_CITY = "state-wide"
MULTIPLE_CITIES = "multiple"
CITY_WILDCARDS = frozenset({ALL_CITIES, STATEWIDE_CITY, MULTIPLE_CITIES})
UNSPECIFIED = "UNSPECIFIED"

_REQUIRED_FIELDS = ("SOURCE", "TYPE", "SECTOR", "STATE", "CITY", "URL_OR_REF")
_SEPARATOR = "---"


class DocumentFormatError(ValueError):
    pass


@dataclass
class DocumentMetadata:
    source: str
    type: str
    sector: str
    state: str
    city: str
    url_or_ref: str
    body: str
    file_path: str
    needs_review: bool


def parse_document(text: str, file_path: str = "<unknown>") -> DocumentMetadata:
    lines = text.split("\n")

    separator_index = None
    for i, line in enumerate(lines):
        if line.strip() == _SEPARATOR:
            separator_index = i
            break

    if separator_index is None:
        raise DocumentFormatError(
            f"{file_path}: missing '---' header/body separator"
        )

    header_lines = lines[:separator_index]
    body = "\n".join(lines[separator_index + 1:]).strip("\n")

    fields: dict[str, str] = {}
    for line in header_lines:
        if not line.strip():
            continue
        if ":" not in line:
            raise DocumentFormatError(f"{file_path}: malformed header line: {line!r}")
        key, _, value = line.partition(":")
        fields[key.strip().upper()] = value.strip()

    missing = [f for f in _REQUIRED_FIELDS if f not in fields]
    if missing:
        raise DocumentFormatError(
            f"{file_path}: missing required header field(s): {', '.join(missing)}"
        )

    state = fields["STATE"]
    city = fields["CITY"]
    needs_review = False

    if not state:
        state = UNSPECIFIED
        needs_review = True
    if not city:
        city = UNSPECIFIED
        needs_review = True

    return DocumentMetadata(
        source=fields["SOURCE"],
        type=fields["TYPE"],
        sector=fields["SECTOR"],
        state=state,
        city=city,
        url_or_ref=fields["URL_OR_REF"],
        body=body,
        file_path=file_path,
        needs_review=needs_review,
    )
