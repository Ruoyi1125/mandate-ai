"""Input parsing helpers for source records."""

from __future__ import annotations

import csv
from io import StringIO

from mandate.schemas import SourceRecord

REQUIRED_CSV_COLUMNS = {"source_id", "text"}
OPTIONAL_CSV_COLUMNS = {"participant_id", "consent_id"}


def source_records_from_lines(raw_text: str) -> list[SourceRecord]:
    """Create source records from one opinion per line."""

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    return [
        SourceRecord(
            source_id=f"source_{index + 1}",
            participant_id=None,
            text=line,
            metadata={"input_method": "line_text"},
            consent_id=None,
        )
        for index, line in enumerate(lines)
    ]


def source_records_from_csv(csv_text: str) -> list[SourceRecord]:
    """Create source records from CSV text with validated columns."""

    reader = csv.DictReader(StringIO(csv_text))
    columns = set(reader.fieldnames or [])
    missing = REQUIRED_CSV_COLUMNS - columns
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"CSV is missing required columns: {missing_list}")

    allowed = REQUIRED_CSV_COLUMNS | OPTIONAL_CSV_COLUMNS
    metadata_columns = [column for column in columns if column not in allowed]
    records: list[SourceRecord] = []
    for row in reader:
        metadata = {
            column: row[column]
            for column in metadata_columns
            if row.get(column) not in {None, ""}
        }
        records.append(
            SourceRecord(
                source_id=str(row["source_id"]).strip(),
                participant_id=_optional(row.get("participant_id")),
                text=str(row["text"]).strip(),
                metadata=metadata,
                consent_id=_optional(row.get("consent_id")),
            )
        )
    return records


def _optional(value: object) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None
