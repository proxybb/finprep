"""Conservative table-boundary cleanup for mechanically cleaned data."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pandas as pd

from cleaning.mechanical import normalize_header_text


@dataclass(frozen=True)
class TableBoundaryResult:
    """Result of leading metadata cleanup and header-row promotion."""

    dataframe: pd.DataFrame
    metadata: dict[str, str]
    status: str
    action: str
    message: str


TABLE_HEADER_FIRST_LABELS = {"year", "period", "date", "line item", "line_item"}


def _text_value(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value).strip()


def _is_blank(value: Any) -> bool:
    return _text_value(value) == ""


def _is_historical_year_label(value: Any) -> bool:
    text = _text_value(value)
    if not re.fullmatch(r"\d{4}", text):
        return False

    year = int(text)
    return 1900 <= year <= 2099


def _is_non_year_text_label(value: Any) -> bool:
    text = _text_value(value)
    return bool(text) and not _is_historical_year_label(text)


def _metadata_from_text(value: Any) -> tuple[str, str] | None:
    text = _text_value(value)
    if not text:
        return None

    metadata_match = re.fullmatch(
        r"(company|statement|title|currency|units)\s*:\s*(.+)",
        text,
        flags=re.IGNORECASE,
    )
    if metadata_match:
        return metadata_match.group(1).lower(), metadata_match.group(2).strip()

    if re.match(r"prepared by\b", text, flags=re.IGNORECASE):
        return "prepared_by", text

    return None


def extract_leading_metadata(df: pd.DataFrame) -> dict[str, str]:
    """Extract simple leading metadata without changing the DataFrame."""
    metadata: dict[str, str] = {}

    if len(df.columns) > 0:
        header_metadata = _metadata_from_text(df.columns[0])
        if header_metadata:
            key, value = header_metadata
            metadata[key] = value

    for _, row in df.iterrows():
        values = list(row)
        if not values:
            continue

        first_value = values[0]
        row_metadata = _metadata_from_text(first_value)
        rest_is_blank = all(_is_blank(value) for value in values[1:])
        if row_metadata and rest_is_blank:
            key, value = row_metadata
            metadata[key] = value
            continue

        break

    return metadata


def _count_historical_years(values: list[Any]) -> int:
    return sum(1 for value in values if _is_historical_year_label(value))


def _row_looks_like_table_header(values: list[Any]) -> bool:
    if len(values) < 2:
        return False

    first_label = _text_value(values[0]).lower().replace("_", " ")
    if first_label not in TABLE_HEADER_FIRST_LABELS:
        return False

    remaining_values = values[1:]
    historical_year_count = _count_historical_years(remaining_values)
    text_label_count = sum(
        1
        for value in remaining_values
        if _is_non_year_text_label(value) and not _metadata_from_text(value)
    )
    return historical_year_count >= 2 or text_label_count >= 1


def _row_is_leading_metadata(values: list[Any]) -> bool:
    if not values:
        return False

    row_metadata = _metadata_from_text(values[0])
    if not row_metadata:
        return False

    return all(_is_blank(value) for value in values[1:])


def _promote_row_to_header(df: pd.DataFrame, row_position: int) -> pd.DataFrame:
    new_headers = [
        normalize_header_text(_text_value(value))
        for value in list(df.iloc[row_position])
    ]
    promoted = df.iloc[row_position + 1 :].copy()
    promoted.columns = new_headers
    return promoted.reset_index(drop=True)


def normalize_table_boundary(df: pd.DataFrame) -> TableBoundaryResult:
    """Remove leading metadata and promote a clear table header when present."""
    metadata = extract_leading_metadata(df)
    working = df.copy()
    action = "no_change"

    if len(working.columns) > 0 and _metadata_from_text(working.columns[0]):
        working.columns = list(range(len(working.columns)))
        action = "metadata_header_reset"

    leading_rows_to_drop = 0
    for row_position, (_, row) in enumerate(working.iterrows()):
        values = list(row)
        if _row_is_leading_metadata(values):
            row_metadata = _metadata_from_text(values[0])
            if row_metadata:
                key, value = row_metadata
                metadata[key] = value
            leading_rows_to_drop = row_position + 1
            action = "metadata_rows_removed"
            continue

        if _row_looks_like_table_header(values):
            bounded = _promote_row_to_header(working, row_position)
            return TableBoundaryResult(
                dataframe=bounded,
                metadata=metadata,
                status="bounded",
                action="header_row_promoted",
                message="Table boundary normalized.",
            )

        break

    if leading_rows_to_drop:
        working = working.iloc[leading_rows_to_drop:].copy().reset_index(drop=True)

    status = "bounded" if action != "no_change" else "unchanged"
    message = (
        "Table boundary normalized."
        if action != "no_change"
        else "No table-boundary cleanup applied."
    )
    return TableBoundaryResult(
        dataframe=working,
        metadata=metadata,
        status=status,
        action=action,
        message=message,
    )
