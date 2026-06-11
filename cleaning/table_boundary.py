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
    status: str
    action: str
    message: str


TABLE_HEADER_FIRST_LABELS = {"year", "period", "date", "line item", "line_item"}
ANNOTATION_COLUMN_LABELS = {
    "notes",
    "note",
    "comments",
    "comment",
    "remarks",
    "remark",
    "extra blank col",
}


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


def _is_metadata_text(value: Any) -> bool:
    text = _text_value(value)
    if not text:
        return False

    return bool(
        re.fullmatch(
            r"(company|statement|title|currency|units)\s*:\s*.+",
            text,
            flags=re.IGNORECASE,
        )
        or re.match(r"prepared by\b", text, flags=re.IGNORECASE)
    )


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
        if _is_non_year_text_label(value) and not _is_metadata_text(value)
    )
    return historical_year_count >= 2 or text_label_count >= 1


def _row_is_leading_metadata(values: list[Any]) -> bool:
    if not values:
        return False

    return _is_metadata_text(values[0])


def _drop_annotation_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    keep_columns = [
        _text_value(column).lower() not in ANNOTATION_COLUMN_LABELS
        for column in df.columns
    ]
    if all(keep_columns):
        return df.copy(), False

    kept_positions = [
        position for position, keep_column in enumerate(keep_columns) if keep_column
    ]
    return df.iloc[:, kept_positions].copy(), True


def _drop_blank_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    keep_columns = []
    for column_position, column in enumerate(df.columns):
        column_is_blank = _is_blank(column)
        values_are_blank = all(_is_blank(value) for value in df.iloc[:, column_position])
        keep_columns.append(not (column_is_blank and values_are_blank))

    if all(keep_columns):
        return df.copy(), False

    kept_positions = [
        position for position, keep_column in enumerate(keep_columns) if keep_column
    ]
    return df.iloc[:, kept_positions].copy(), True


def _drop_non_table_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    without_annotations, annotations_removed = _drop_annotation_columns(df)
    without_blanks, blanks_removed = _drop_blank_columns(without_annotations)
    return without_blanks, annotations_removed or blanks_removed


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
    working, annotation_columns_removed = _drop_non_table_columns(df)
    action = "no_change"
    if annotation_columns_removed:
        action = "annotation_columns_removed"

    if len(working.columns) > 0 and _is_metadata_text(working.columns[0]):
        working.columns = list(range(len(working.columns)))
        action = "metadata_header_reset"

    leading_rows_to_drop = 0
    for row_position, (_, row) in enumerate(working.iterrows()):
        values = list(row)
        if _row_is_leading_metadata(values):
            leading_rows_to_drop = row_position + 1
            action = "metadata_rows_removed"
            continue

        if _row_looks_like_table_header(values):
            bounded = _promote_row_to_header(working, row_position)
            bounded, _ = _drop_non_table_columns(bounded)
            return TableBoundaryResult(
                dataframe=bounded,
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
        status=status,
        action=action,
        message=message,
    )
