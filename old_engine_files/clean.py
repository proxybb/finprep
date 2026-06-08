import re

import pandas as pd

from modules.mappings import (
    NUMERIC_COLUMNS,
    POSITIVE_MAGNITUDE_COLUMNS,
    REVIEW_NUMERIC_COLUMNS,
    map_column_name,
)


_UNIT_PATTERN = re.compile(
    r"\b(?:us dollars|in millions|in thousands|millions|thousands|usd)\b|\$mm|\$m|\$",
    re.IGNORECASE,
)

_UNIT_PARENS_PATTERN = re.compile(
    r"\(\s*(?:\$mm|\$m|\$|usd|us dollars|in millions|millions|in thousands|thousands)\s*\)",
    re.IGNORECASE,
)


def normalize_column_name(column_name):
    """Normalize only the mechanics of a column label, not its accounting meaning."""
    normalized = str(column_name).lower().strip()
    normalized = _UNIT_PARENS_PATTERN.sub(" ", normalized)
    normalized = normalized.replace("&", "and")
    normalized = re.sub(r"[_\-/.,\r\n]+", " ", normalized)
    normalized = re.sub(r"['\u2019]", "", normalized)
    normalized = _UNIT_PATTERN.sub(" ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized.strip()


def standardize_period_value(value):
    """Convert period labels like FY2023, 2021A, and Dec-2022 to a year string."""
    if pd.isna(value):
        return value

    stripped_value = str(value).strip()
    if looks_quarterly_period(value):
        return stripped_value

    year_match = re.search(r"(?<!\d)(\d{4})(?!\d)", stripped_value)
    if year_match:
        return year_match.group(1)

    return stripped_value


def looks_quarterly_period(value):
    """Return True when a period label appears to describe quarterly data."""
    if pd.isna(value):
        return False

    stripped_value = str(value).lower().strip()
    return bool(
        re.search(r"\bq[1-4]\b", stripped_value)
        or "quarter ended" in stripped_value
        or "three months ended" in stripped_value
        or "three-month period" in stripped_value
        or "3 months ended" in stripped_value
    )


def is_valid_period_value(value):
    """Return True only for period values that are exactly four digits."""
    stripped_value = str(value).strip()
    return bool(re.fullmatch(r"\d{4}", stripped_value))


def clean_numeric_value(value):
    """Convert obvious financial number formatting without making business judgments."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return value

    stripped_value = str(value).strip()
    if stripped_value.lower() in {"", "none", "nan", "n/a", "-"}:
        return None

    is_negative = False
    numeric_text = stripped_value
    if numeric_text.startswith("(") and numeric_text.endswith(")"):
        is_negative = True
        numeric_text = numeric_text[1:-1].strip()

    numeric_text = re.sub(r"[$£€]", "", numeric_text)
    numeric_text = numeric_text.replace(",", "").strip()

    try:
        number = float(numeric_text)
    except ValueError:
        return value

    if is_negative:
        return -number

    return number


def normalize_positive_magnitude(value):
    """Store cost/outflow fields as positive magnitudes after numeric cleaning."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return abs(value)

    return value


def clean_statement(df, statement_type):
    """Apply the first mechanical cleaning pass to a financial statement DataFrame."""
    if df is None:
        return None

    cleaned_df = df.copy()
    cleaned_df = cleaned_df.dropna(how="all")
    cleaned_df = cleaned_df.dropna(axis=1, how="all")

    # Layer 1: mechanical cleanup removes empty rows/columns and normalizes
    # labels so punctuation, spacing, casing, and unit text do not block lookup.
    normalized_columns = [
        normalize_column_name(column_name) for column_name in cleaned_df.columns
    ]

    # Layer 2: statement-specific mapping translates known financial labels.
    # Unmapped and review-only columns are kept so the user can inspect them.
    cleaned_df.columns = [
        map_column_name(column_name, statement_type) for column_name in normalized_columns
    ]

    # Layer 3: period and numeric cleanup standardizes obvious formatting.
    # Sorting and duplicate handling come later.
    if "period" in cleaned_df.columns:
        cleaned_df["period"] = cleaned_df["period"].apply(standardize_period_value)

    for column_name in cleaned_df.columns:
        if column_name in NUMERIC_COLUMNS or column_name in REVIEW_NUMERIC_COLUMNS:
            cleaned_df[column_name] = cleaned_df[column_name].apply(clean_numeric_value)

    # Layer 4: positive-magnitude sign convention stores cost/outflow fields as
    # positive values. Analysis formulas apply subtraction later.
    for column_name in cleaned_df.columns:
        if column_name in POSITIVE_MAGNITUDE_COLUMNS:
            cleaned_df[column_name] = cleaned_df[column_name].apply(
                normalize_positive_magnitude
            )

    # Layer 5: remove invalid non-data rows such as extra header/comment rows.
    # Quarterly-looking rows are kept so validation can warn that v1 supports
    # annual data only. Duplicate valid periods are intentionally left for later.
    if "period" in cleaned_df.columns:
        cleaned_df = cleaned_df[
            cleaned_df["period"].apply(
                lambda value: is_valid_period_value(value)
                or looks_quarterly_period(value)
            )
        ].reset_index(drop=True)

    # TODO: sort periods
    # TODO: handle duplicate periods
    # TODO: handle missing values
    # TODO: produce a cleaning report for unmapped columns and review-only labels

    return cleaned_df
