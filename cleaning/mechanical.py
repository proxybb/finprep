"""Conservative mechanical cleaning for uploaded tabular data."""

from __future__ import annotations

import re
from numbers import Number
from typing import Any

import pandas as pd

from configs.currencies import SUPPORTED_CURRENCY_CODES
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

HEADER_SEPARATOR_PATTERN = re.compile(r"[_\-/.,\r\n]+")
HEADER_APOSTROPHE_PATTERN = re.compile(r"['\u2019]")
HEADER_UNIT_SUFFIX_PATTERNS = (
    r"\s*\(\s*(?:\$?\s*(?:mm|m)|usd|us dollars|millions|thousands)\s*\)\s*$",
    r"\s*\$mm\s*$",
    r"\s*\$m\s*$",
    r"\s*\$\s*$",
    r"\s*us dollars\s*$",
    r"\s*usd\s*$",
    r"\s*(?:in\s+)?millions\s*$",
    r"\s*(?:in\s+)?thousands\s*$",
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


def drop_exact_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop fully identical duplicate rows after prior mechanical normalization."""
    return df.drop_duplicates(keep="first").copy()


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

    supported_codes = "|".join(re.escape(code) for code in SUPPORTED_CURRENCY_CODES)
    text = re.sub(rf"^(?:{supported_codes})\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(rf"\s+(?:{supported_codes})$", "", text, flags=re.IGNORECASE)
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
    normalized = HEADER_APOSTROPHE_PATTERN.sub("", normalized)
    normalized = HEADER_SEPARATOR_PATTERN.sub(" ", normalized)
    normalized = normalize_string_value(normalized)

    changed = True
    while changed:
        changed = False
        for pattern in HEADER_UNIT_SUFFIX_PATTERNS:
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

    as_of_year_match = re.fullmatch(r"as of\s+(\d{4})", text, flags=re.IGNORECASE)
    if as_of_year_match:
        return as_of_year_match.group(1)

    month_pattern = "|".join(MONTH_NAMES)
    as_of_month_day_year_match = re.fullmatch(
        rf"as of\s+({month_pattern})\s+\d{{1,2}},?\s+(\d{{4}})",
        text,
        flags=re.IGNORECASE,
    )
    if as_of_month_day_year_match:
        return as_of_month_day_year_match.group(2)

    fiscal_year_match = re.fullmatch(r"FY\s*(\d{4})A?", text, flags=re.IGNORECASE)
    if fiscal_year_match:
        return fiscal_year_match.group(1)

    actual_year_match = re.fullmatch(r"(\d{4})A", text, flags=re.IGNORECASE)
    if actual_year_match:
        return actual_year_match.group(1)

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

    deduped_df = drop_exact_duplicate_rows(cleaned_df)
    audit_log.duplicate_rows_dropped_count = len(cleaned_df.index) - len(deduped_df.index)
    audit_log.rows_dropped_count += audit_log.duplicate_rows_dropped_count
    cleaned_df = deduped_df

    return {"cleaned_df": cleaned_df, "audit_log": audit_log.as_dict()}
