"""Shared mapping helpers for all statement types."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


MAPPING_METADATA_COLUMNS = [
    "original_label",
    "normalized_label",
    "statement_type",
    "row_position",
    "mapping_status",
    "canonical_label",
    "display_label",
    "matched_alias",
    "matched_rule_kind",
    "concept_category",
    "concept_family",
    "rollup_role",
    "review_reason",
    "includes_restricted_cash",
    "expected_sign",
]

_PUNCTUATION_PATTERN = re.compile(r"[^\w\s]")


def normalize_mapping_label(label: Any) -> str:
    """Normalize a source statement label for exact deterministic matching."""
    if label is None:
        return ""

    try:
        if pd.isna(label):
            return ""
    except TypeError:
        pass

    normalized = str(label).lower().strip()
    normalized = normalized.replace("&", "and")
    normalized = re.sub(r"[‘’]", "", normalized)
    normalized = _PUNCTUATION_PATTERN.sub(" ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()
