"""Mechanical period-label normalization helpers."""

from __future__ import annotations

import re
from typing import Any


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


def _normalize_period_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def normalize_period_label(value: Any) -> Any:
    """Normalize only obvious period labels."""
    if not isinstance(value, str):
        return value

    text = _normalize_period_text(value)

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
