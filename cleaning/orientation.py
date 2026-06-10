"""Conservative table orientation detection for bounded statement data."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class OrientationResult:
    """Result of the orientation normalization stage."""

    dataframe: pd.DataFrame
    status: str
    action: str
    confidence: float
    message: str


def _is_historical_year_label(value: Any) -> bool:
    """Return True for simple historical year labels used for orientation."""
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except TypeError:
        pass

    if isinstance(value, float) and value.is_integer():
        value = int(value)

    text = str(value).strip()
    if not re.fullmatch(r"\d{4}", text):
        return False

    year = int(text)
    return 1900 <= year <= 2099


def _is_non_year_text_label(value: Any) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except TypeError:
        pass

    text = str(value).strip()
    return bool(text) and not _is_historical_year_label(text)


def _count_historical_years(values: list[Any]) -> int:
    return sum(1 for value in values if _is_historical_year_label(value))


def _first_column_mostly_labels(df: pd.DataFrame) -> bool:
    if df.empty or len(df.columns) == 0:
        return False

    first_column_values = list(df.iloc[:, 0])
    non_empty_values = [
        value
        for value in first_column_values
        if _is_non_year_text_label(value) or _is_historical_year_label(value)
    ]
    if not non_empty_values:
        return False

    text_label_count = sum(
        1 for value in non_empty_values if _is_non_year_text_label(value)
    )
    return text_label_count / len(non_empty_values) >= 0.5


def _headers_look_like_statement_items(headers: list[Any]) -> bool:
    if not headers:
        return False

    text_label_count = sum(1 for header in headers if _is_non_year_text_label(header))
    return text_label_count / len(headers) >= 0.5


def _canonical_period_label(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def _transpose_sideways_table(df: pd.DataFrame) -> pd.DataFrame | None:
    if df.empty or len(df.columns) < 2 or len(df.index) < 1:
        return None

    first_column = df.columns[0]
    period_values = list(df.iloc[:, 0])
    value_columns = list(df.columns[1:])
    if not value_columns or _count_historical_years(period_values) < 2:
        return None

    indexed = df.copy()
    indexed = indexed.set_index(first_column, drop=True)
    transposed = indexed.T.reset_index()
    if transposed.empty or len(transposed.columns) < 2:
        return None

    transposed = transposed.rename(columns={"index": "line_item"})
    transposed.columns = [
        "line_item" if index == 0 else _canonical_period_label(column)
        for index, column in enumerate(transposed.columns)
    ]
    return transposed


def normalize_orientation(df: pd.DataFrame) -> OrientationResult:
    """Normalize statement periods into columns when orientation is clear."""
    if df.empty or len(df.columns) == 0:
        return OrientationResult(
            dataframe=df.copy(),
            status="uncertain",
            action="no_change",
            confidence=0.0,
            message="Orientation uncertain; table left unchanged.",
        )

    headers = list(df.columns)
    first_column_values = list(df.iloc[:, 0])
    header_year_count = _count_historical_years(headers)
    first_column_year_count = _count_historical_years(first_column_values)

    if header_year_count >= 2 and _first_column_mostly_labels(df):
        return OrientationResult(
            dataframe=df.copy(),
            status="already_standard",
            action="no_change",
            confidence=0.9,
            message="Orientation already standard.",
        )

    if (
        first_column_year_count >= 2
        and _headers_look_like_statement_items(headers[1:])
    ):
        transposed = _transpose_sideways_table(df)
        if transposed is not None:
            return OrientationResult(
                dataframe=transposed,
                status="transposed",
                action="transpose",
                confidence=0.85,
                message="Orientation normalized.",
            )

    return OrientationResult(
        dataframe=df.copy(),
        status="uncertain",
        action="no_change",
        confidence=0.2,
        message="Orientation uncertain; table left unchanged.",
    )
