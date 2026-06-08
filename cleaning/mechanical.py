"""Conservative mechanical cleaning for uploaded tabular data."""

from __future__ import annotations

import re
from numbers import Number
from typing import Any

import pandas as pd

from cleaning.audit import MechanicalAuditLog


MISSING_STRINGS = {
    "",
    "-",
    "—",
    "–",
    "N/A",
    "NA",
    "na",
    "n/a",
    "None",
    "none",
    "NULL",
    "null",
}

MONTH_NAMES = (
    "jan",
    "january",
    "feb",
    "february",
    "mar",
    "march",
    "apr",
    "april",
    "may",
    "jun",
    "june",
    "jul",
    "july",
    "aug",
    "august",
    "sep",
    "sept",
    "september",
    "oct",
    "october",
    "nov",
    "november",
    "dec",
    "december",
)


def normalize_string_value(value: Any) -> Any:
    """Strip strings and collapse repeated whitespace."""
    if not isinstance(value, str):
        return value
    return re.sub(r"\s+", " ", value.strip())


def normalize_missing_value(value: Any) -> Any:
    """Convert obvious blank-like values to None."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass

    if isinstance(value, str):
        normalized = normalize_string_value(value)
        if normalized in MISSING_STRINGS:
            return None

    return value


def _is_blank_like(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except TypeError:
        pass
    return normalize_missing_value(value) is None


def drop_blank_rows_and_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows and columns where every value is null or blank-like."""
    blank_mask = df.apply(lambda column: column.map(_is_blank_like))
    non_blank_rows = ~blank_mask.all(axis=1)
    non_blank_columns = ~blank_mask.all(axis=0)
    return df.loc[non_blank_rows, non_blank_columns].copy()


def clean_numeric_value(value: Any) -> Any:
    """Convert obvious numeric-looking strings into numbers."""
    if isinstance(value, Number) and not isinstance(value, bool):
        return value
    if not isinstance(value, str):
        return value

    text = normalize_string_value(value)
    if not text:
        return value

    is_parenthetical_negative = text.startswith("(") and text.endswith(")")
    if is_parenthetical_negative:
        text = text[1:-1].strip()

    text = re.sub(r"^[A-Z]{3}\s+", "", text)
    text = re.sub(r"\s+[A-Z]{3}$", "", text)
    text = text.replace("$", "").replace("€", "").replace("£", "")
    text = text.replace(",", "").strip()

    if not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", text):
        return value

    number = float(text) if "." in text else int(text)
    if is_parenthetical_negative:
        number = -abs(number)
    return number


def normalize_header_text(label: Any) -> Any:
    """Mechanically normalize a column/header label without mapping meaning."""
    if not isinstance(label, str):
        return label

    normalized = normalize_string_value(label).lower()
    normalized = normalized.replace("&", "and")
    normalized = normalize_string_value(normalized)

    suffix_patterns = (
        r"\s*\(\s*\$?\s*(?:m|mm|usd)?\s*\)\s*$",
        r"\s*\$m\s*$",
        r"\s*\$\s*$",
        r"\s*usd\s*$",
        r"\s*in millions\s*$",
        r"\s*in thousands\s*$",
    )
    changed = True
    while changed:
        changed = False
        for pattern in suffix_patterns:
            next_value = re.sub(pattern, "", normalized, flags=re.IGNORECASE).strip()
            if next_value != normalized:
                normalized = next_value
                changed = True

    return normalize_string_value(normalized)


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Apply mechanical normalization to DataFrame column names."""
    cleaned = df.copy()
    cleaned.columns = [normalize_header_text(column) for column in cleaned.columns]
    return cleaned


def normalize_period_label(value: Any) -> Any:
    """Normalize only obvious period labels."""
    if not isinstance(value, str):
        return value

    text = normalize_string_value(value)

    quarter_match = re.fullmatch(r"Q([1-4])\s+(\d{4})", text, flags=re.IGNORECASE)
    if quarter_match:
        return f"Q{quarter_match.group(1)} {quarter_match.group(2)}"

    fiscal_year_match = re.fullmatch(r"FY\s*(\d{4})", text, flags=re.IGNORECASE)
    if fiscal_year_match:
        return fiscal_year_match.group(1)

    month_pattern = "|".join(MONTH_NAMES)
    month_year_match = re.fullmatch(
        rf"({month_pattern})[-\s]+(\d{{4}})", text, flags=re.IGNORECASE
    )
    if month_year_match:
        return month_year_match.group(2)

    return value


def _normalize_cell_value(value: Any, audit_log: MechanicalAuditLog) -> Any:
    value = normalize_string_value(value)
    missing_value = normalize_missing_value(value)
    if missing_value is None:
        if value is not None:
            audit_log.missing_values_normalized_count += 1
        return None

    numeric_value = clean_numeric_value(missing_value)
    if numeric_value != missing_value:
        audit_log.numeric_values_converted_count += 1
        return numeric_value

    period_value = normalize_period_label(missing_value)
    if period_value != missing_value:
        audit_log.period_labels_normalized_count += 1
    return period_value


def run_mechanical_cleaning(df: pd.DataFrame) -> dict[str, Any]:
    """Run Stage 1 mechanical cleaning and return cleaned data plus audit log."""
    audit_log = MechanicalAuditLog()

    cleaned_df = drop_blank_rows_and_columns(df)
    audit_log.rows_dropped_count = len(df.index) - len(cleaned_df.index)
    audit_log.columns_dropped_count = len(df.columns) - len(cleaned_df.columns)

    original_headers = list(cleaned_df.columns)
    cleaned_df = normalize_headers(cleaned_df)
    audit_log.headers_normalized = [
        {"original": original, "normalized": normalized}
        for original, normalized in zip(original_headers, cleaned_df.columns)
        if original != normalized
    ]

    cleaned_df = cleaned_df.apply(
        lambda column: column.map(lambda value: _normalize_cell_value(value, audit_log))
    )

    return {"cleaned_df": cleaned_df, "audit_log": audit_log.as_dict()}
