"""Deterministic financial statement label mapping."""

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
    normalized = re.sub(r"['\u2019]", "", normalized)
    normalized = _PUNCTUATION_PATTERN.sub(" ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def map_statement_rows(df: pd.DataFrame, statement_type: str) -> tuple[pd.DataFrame, list[dict]]:
    """Map cleaned statement rows to canonical metadata without changing values."""
    if statement_type != "balance_sheet":
        raise ValueError("Only balance_sheet mapping is implemented in this step.")
    if len(df.columns) == 0:
        raise ValueError("Mapping requires a DataFrame with at least one label column.")

    mapped_df = df.copy(deep=True)
    label_column = mapped_df.columns[0]

    audit_records = []
    metadata_by_column = {column: [] for column in MAPPING_METADATA_COLUMNS}

    for row_position, original_label in enumerate(mapped_df[label_column].tolist()):
        metadata = _metadata_for_label(
            original_label=original_label,
            normalized_label=normalize_mapping_label(original_label),
            statement_type=statement_type,
            row_position=row_position,
        )
        audit_records.append(metadata.copy())
        for column in MAPPING_METADATA_COLUMNS:
            metadata_by_column[column].append(metadata[column])

    for column, values in metadata_by_column.items():
        mapped_df[column] = pd.Series(values, index=mapped_df.index, dtype=object)

    return mapped_df, audit_records


def _metadata_for_label(
    *,
    original_label: Any,
    normalized_label: str,
    statement_type: str,
    row_position: int,
) -> dict:
    rule = _SPECIAL_ASSET_RULES.get(normalized_label)
    if rule is None:
        rule = _SPECIAL_EQUITY_RULES.get(normalized_label)
    if rule is None:
        rule = _SPECIAL_LIABILITY_RULES.get(normalized_label)
    if rule is None:
        rule = _AUTO_MAP_ASSET_RULES.get(normalized_label)
    if rule is None:
        rule = _AUTO_MAP_EQUITY_RULES.get(normalized_label)
    if rule is None:
        rule = _AUTO_MAP_LIABILITY_RULES.get(normalized_label)

    if rule is None:
        rule = {
            "mapping_status": "unmapped",
            "canonical_label": None,
            "display_label": None,
            "matched_alias": None,
            "matched_rule_kind": None,
            "concept_category": None,
            "concept_family": None,
            "rollup_role": "none",
            "review_reason": None,
            "includes_restricted_cash": False,
        }

    return {
        "original_label": original_label,
        "normalized_label": normalized_label,
        "statement_type": statement_type,
        "row_position": row_position,
        **rule,
    }


def _asset_rule(
    *,
    mapping_status: str,
    canonical_label: str | None,
    display_label: str | None,
    matched_alias: str,
    matched_rule_kind: str,
    concept_category: str,
    concept_family: str,
    rollup_role: str,
    review_reason: str | None = None,
    includes_restricted_cash: bool = False,
) -> dict:
    return {
        "mapping_status": mapping_status,
        "canonical_label": canonical_label,
        "display_label": display_label,
        "matched_alias": matched_alias,
        "matched_rule_kind": matched_rule_kind,
        "concept_category": concept_category,
        "concept_family": concept_family,
        "rollup_role": rollup_role,
        "review_reason": review_reason,
        "includes_restricted_cash": includes_restricted_cash,
    }


def _auto_rule(
    *,
    alias: str,
    canonical_label: str,
    display_label: str,
    concept_family: str,
    rollup_role: str,
    concept_category: str = "reported_concept",
) -> dict:
    return _asset_rule(
        mapping_status="auto_mapped",
        canonical_label=canonical_label,
        display_label=display_label,
        matched_alias=alias,
        matched_rule_kind="auto_alias",
        concept_category=concept_category,
        concept_family=concept_family,
        rollup_role=rollup_role,
    )


def _title_display_label(alias: str) -> str:
    special_words = {"aoci": "AOCI"}
    return " ".join(special_words.get(word, word.title()) for word in alias.split())


_AUTO_MAP_ASSET_RULES = {
    alias: _auto_rule(
        alias=alias,
        canonical_label="cash_and_equivalents",
        display_label="Cash and Cash Equivalents",
        concept_family="liquidity",
        rollup_role="narrow",
    )
    for alias in (
        "cash and cash equivalents",
    )
}

_AUTO_MAP_ASSET_RULES.update(
    {
        alias: _auto_rule(
            alias=alias,
            canonical_label="accounts_receivable",
            display_label="Accounts Receivable",
            concept_family="receivables",
            rollup_role="component",
        )
        for alias in (
            "accounts receivable",
            "accounts receivable net",
            "trade receivables",
            "trade receivables net",
        )
    }
)

_AUTO_MAP_ASSET_RULES["trade and other receivables"] = _asset_rule(
    mapping_status="review_only",
    canonical_label="receivables_total",
    display_label="Trade and Other Receivables",
    matched_alias="trade and other receivables",
    matched_rule_kind="special_review",
    concept_category="composite_label",
    concept_family="receivables",
    rollup_role="composite",
    review_reason="includes_other_receivables",
)

_AUTO_MAP_ASSET_RULES.update(
    {
        alias: _auto_rule(
            alias=alias,
            canonical_label="inventory",
            display_label="Inventory",
            concept_family="inventory",
            rollup_role="total",
        )
        for alias in (
            "inventory",
            "inventories",
        )
    }
)

_AUTO_MAP_ASSET_RULES.update(
    {
        alias: _auto_rule(
            alias=alias,
            canonical_label="current_assets",
            display_label="Current Assets",
            concept_family="current_assets",
            rollup_role="total",
        )
        for alias in (
            "current assets",
            "total current assets",
        )
    }
)

_AUTO_MAP_ASSET_RULES.update(
    {
        alias: _auto_rule(
            alias=alias,
            canonical_label="ppe",
            display_label="PP&E",
            concept_family="long_lived_assets",
            rollup_role="narrow",
        )
        for alias in (
            "property plant and equipment",
            "property plant and equipment net",
            "property plant equipment",
            "property plant equipment net",
            "ppe",
            "pp and e",
        )
    }
)

_AUTO_MAP_ASSET_RULES["total assets"] = _auto_rule(
    alias="total assets",
    canonical_label="total_assets",
    display_label="Total Assets",
    concept_family="total_assets",
    rollup_role="total",
)

_AUTO_MAP_LIABILITY_RULES = {
    alias: _auto_rule(
        alias=alias,
        canonical_label="accounts_payable",
        display_label="Accounts Payable",
        concept_family="payables",
        rollup_role="narrow",
    )
    for alias in (
        "accounts payable",
        "trade payables",
    )
}

_AUTO_MAP_LIABILITY_RULES["trade and other payables"] = _asset_rule(
    mapping_status="review_only",
    canonical_label="payables_total",
    display_label="Trade and Other Payables",
    matched_alias="trade and other payables",
    matched_rule_kind="special_review",
    concept_category="composite_label",
    concept_family="payables",
    rollup_role="composite",
    review_reason="includes_other_payables",
)

_AUTO_MAP_LIABILITY_RULES.update(
    {
        alias: _asset_rule(
            mapping_status="deferred",
            canonical_label="accrued_expenses",
            display_label="Accrued Expenses",
            matched_alias=alias,
            matched_rule_kind="special_review",
            concept_category="deferred_canonical",
            concept_family="accruals",
            rollup_role="component",
            review_reason="accrued_expenses_not_supported_in_analysis_yet",
        )
        for alias in (
            "accrued expenses",
            "accrued liabilities",
        )
    }
)

_AUTO_MAP_LIABILITY_RULES.update(
    {
        alias: _auto_rule(
            alias=alias,
            canonical_label="current_liabilities",
            display_label="Current Liabilities",
            concept_family="current_liabilities",
            rollup_role="total",
        )
        for alias in (
            "current liabilities",
            "total current liabilities",
        )
    }
)

_AUTO_MAP_LIABILITY_RULES["total liabilities"] = _auto_rule(
    alias="total liabilities",
    canonical_label="total_liabilities",
    display_label="Total Liabilities",
    concept_family="total_liabilities",
    rollup_role="total",
)

_AUTO_MAP_EQUITY_RULES = {
    "total equity": _auto_rule(
        alias="total equity",
        canonical_label="total_equity",
        display_label="Total Equity",
        concept_family="total_equity",
        rollup_role="total",
    )
}


_SPECIAL_ASSET_RULES = {
    "cash": _asset_rule(
        mapping_status="unmapped",
        canonical_label=None,
        display_label=None,
        matched_alias="cash",
        matched_rule_kind="special_review",
        concept_category="broad_label",
        concept_family="liquidity",
        rollup_role="broad_unspecified",
        review_reason="broad_cash_label",
    ),
    "cash on hand": _asset_rule(
        mapping_status="unmapped",
        canonical_label=None,
        display_label=None,
        matched_alias="cash on hand",
        matched_rule_kind="special_review",
        concept_category="broad_label",
        concept_family="liquidity",
        rollup_role="broad_unspecified",
        review_reason="broad_vendor_label",
    ),
    "cash and short term investments": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="cash and short term investments",
        matched_rule_kind="special_review",
        concept_category="composite_label",
        concept_family="liquidity",
        rollup_role="composite",
        review_reason="includes_short_term_investments",
    ),
    "cash and marketable securities": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="cash and marketable securities",
        matched_rule_kind="special_review",
        concept_category="composite_label",
        concept_family="liquidity",
        rollup_role="composite",
        review_reason="includes_marketable_securities",
    ),
    "cash and cash equivalents and restricted cash": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="cash and cash equivalents and restricted cash",
        matched_rule_kind="special_review",
        concept_category="conditional_label",
        concept_family="liquidity",
        rollup_role="conditional",
        review_reason="restricted_cash_scope",
        includes_restricted_cash=True,
    ),
    "receivables": _asset_rule(
        mapping_status="unmapped",
        canonical_label=None,
        display_label=None,
        matched_alias="receivables",
        matched_rule_kind="special_review",
        concept_category="broad_label",
        concept_family="receivables",
        rollup_role="broad_unspecified",
        review_reason="broad_receivables_label",
    ),
    "other receivables": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="other receivables",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="receivables",
        rollup_role="component",
        review_reason="other_receivables_not_supported_yet",
    ),
    "accounts receivable net and other": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="accounts receivable net and other",
        matched_rule_kind="special_review",
        concept_category="composite_label",
        concept_family="receivables",
        rollup_role="composite",
        review_reason="includes_other_receivables",
    ),
    "raw materials": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="raw materials",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="inventory",
        rollup_role="component",
        review_reason="inventory_component_not_supported_yet",
    ),
    "finished goods": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="finished goods",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="inventory",
        rollup_role="component",
        review_reason="inventory_component_not_supported_yet",
    ),
    "work in process": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="work in process",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="inventory",
        rollup_role="component",
        review_reason="inventory_component_not_supported_yet",
    ),
    "stock": _asset_rule(
        mapping_status="unmapped",
        canonical_label=None,
        display_label=None,
        matched_alias="stock",
        matched_rule_kind="special_review",
        concept_category="broad_label",
        concept_family="inventory",
        rollup_role="broad_unspecified",
        review_reason="broad_or_regional_label",
    ),
    "fixed assets": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="fixed assets",
        matched_rule_kind="special_review",
        concept_category="conditional_label",
        concept_family="long_lived_assets",
        rollup_role="conditional",
        review_reason="may_not_equal_pp_and_e",
    ),
    "tangible assets": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="tangible assets",
        matched_rule_kind="special_review",
        concept_category="conditional_label",
        concept_family="long_lived_assets",
        rollup_role="conditional",
        review_reason="may_not_equal_pp_and_e",
    ),
    "right of use assets": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="right of use assets",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="long_lived_assets",
        rollup_role="component",
        review_reason="separate_asset_class",
    ),
    "construction in progress": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="construction in progress",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="long_lived_assets",
        rollup_role="component",
        review_reason="pp_and_e_component_not_supported_yet",
    ),
    "intangible assets": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="intangible assets",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="long_lived_assets",
        rollup_role="component",
        review_reason="intangible_assets_not_supported_yet",
    ),
    "goodwill": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="goodwill",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="long_lived_assets",
        rollup_role="component",
        review_reason="goodwill_not_supported_yet",
    ),
    "assets": _asset_rule(
        mapping_status="unmapped",
        canonical_label=None,
        display_label=None,
        matched_alias="assets",
        matched_rule_kind="special_review",
        concept_category="broad_label",
        concept_family="other_assets",
        rollup_role="broad_unspecified",
        review_reason="broad_assets_label",
    ),
    "other current assets": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="other current assets",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="current_assets",
        rollup_role="component",
        review_reason="other_current_assets_not_supported_yet",
    ),
    "other non current assets": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="other non current assets",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="other_assets",
        rollup_role="component",
        review_reason="other_non_current_assets_not_supported_yet",
    ),
}

_SPECIAL_EQUITY_RULES = {
    alias: _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=_title_display_label(alias),
        matched_alias=alias,
        matched_rule_kind="special_review",
        concept_category="conditional_label",
        concept_family="owner_equity",
        rollup_role="conditional",
        review_reason="owner_only_equity_may_exclude_non_controlling_interests",
    )
    for alias in (
        "shareholders equity",
        "stockholders equity",
        "total shareholders equity",
        "total stockholders equity",
        "total common shareholders equity",
        "equity attributable to owners of the parent",
        "equity attributable to owners of parent",
        "equity attributable to shareholders",
        "equity attributable to shareholders of the parent",
    )
}

_SPECIAL_EQUITY_RULES.update(
    {
        alias: _asset_rule(
            mapping_status="deferred",
            canonical_label=None,
            display_label=_title_display_label(alias),
            matched_alias=alias,
            matched_rule_kind="special_review",
            concept_category="deferred_canonical",
            concept_family="equity_components",
            rollup_role="component",
            review_reason="equity_component_not_supported_yet",
        )
        for alias in (
            "retained earnings",
            "accumulated deficit",
            "share capital",
            "common stock",
            "ordinary shares",
            "additional paid in capital",
            "additional paid-in capital",
            "share premium",
            "treasury stock",
            "treasury shares",
            "other reserves",
            "accumulated other comprehensive income",
            "accumulated other comprehensive loss",
            "aoci",
        )
    }
)

_SPECIAL_EQUITY_RULES.update(
    {
        alias: _asset_rule(
            mapping_status="deferred",
            canonical_label=None,
            display_label=_title_display_label(alias),
            matched_alias=alias,
            matched_rule_kind="special_review",
            concept_category="deferred_canonical",
            concept_family="non_controlling_interest",
            rollup_role="component",
            review_reason="non_controlling_interest_not_supported_yet",
        )
        for alias in (
            "non controlling interests",
            "non-controlling interests",
            "noncontrolling interests",
            "minority interest",
            "minority interests",
        )
    }
)

_SPECIAL_EQUITY_RULES.update(
    {
        alias: _asset_rule(
            mapping_status="review_only",
            canonical_label=None,
            display_label=_title_display_label(alias),
            matched_alias=alias,
            matched_rule_kind="special_review",
            concept_category="composite_label",
            concept_family="total_equity_and_liabilities",
            rollup_role="composite",
            review_reason="accounting_equation_total_not_equity_only",
        )
        for alias in (
            "total equity and liabilities",
            "total liabilities and equity",
            "total liabilities and shareholders equity",
            "total liabilities and stockholders equity",
        )
    }
)

_SPECIAL_EQUITY_RULES["equity"] = _asset_rule(
    mapping_status="unmapped",
    canonical_label=None,
    display_label=None,
    matched_alias="equity",
    matched_rule_kind="special_review",
    concept_category="broad_label",
    concept_family="total_equity",
    rollup_role="broad_unspecified",
    review_reason="broad_equity_label",
)

_SPECIAL_EQUITY_RULES["capital and reserves"] = _asset_rule(
    mapping_status="review_only",
    canonical_label=None,
    display_label="Capital and Reserves",
    matched_alias="capital and reserves",
    matched_rule_kind="special_review",
    concept_category="conditional_label",
    concept_family="owner_equity",
    rollup_role="conditional",
    review_reason="may_not_equal_total_equity",
)

_SPECIAL_LIABILITY_RULES = {
    "accounts payable and accrued expenses": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label="Accounts Payable and Accrued Expenses",
        matched_alias="accounts payable and accrued expenses",
        matched_rule_kind="special_review",
        concept_category="composite_label",
        concept_family="payables",
        rollup_role="composite",
        review_reason="combines_payables_and_accruals",
    ),
    "liabilities": _asset_rule(
        mapping_status="unmapped",
        canonical_label=None,
        display_label=None,
        matched_alias="liabilities",
        matched_rule_kind="special_review",
        concept_category="broad_label",
        concept_family="other_liabilities",
        rollup_role="broad_unspecified",
        review_reason="broad_liabilities_label",
    ),
    "other liabilities": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="other liabilities",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="other_liabilities",
        rollup_role="component",
        review_reason="other_liabilities_not_supported_yet",
    ),
    "other current liabilities": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="other current liabilities",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="current_liabilities",
        rollup_role="component",
        review_reason="other_current_liabilities_not_supported_yet",
    ),
    "other non current liabilities": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="other non current liabilities",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="other_liabilities",
        rollup_role="component",
        review_reason="other_non_current_liabilities_not_supported_yet",
    ),
    "borrowings": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="borrowings",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="debt_and_borrowings",
        rollup_role="broad_unspecified",
        review_reason="borrowings_not_supported_yet",
    ),
    "loans and borrowings": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="loans and borrowings",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="debt_and_borrowings",
        rollup_role="broad_unspecified",
        review_reason="borrowings_not_supported_yet",
    ),
    "lease liabilities": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="lease liabilities",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="lease_liabilities",
        rollup_role="component",
        review_reason="lease_liabilities_not_supported_yet",
    ),
    "current lease liabilities": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="current lease liabilities",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="lease_liabilities",
        rollup_role="component",
        review_reason="lease_liabilities_not_supported_yet",
    ),
    "non current lease liabilities": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="non current lease liabilities",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="lease_liabilities",
        rollup_role="component",
        review_reason="lease_liabilities_not_supported_yet",
    ),
    "provisions": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="provisions",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="provisions",
        rollup_role="broad_unspecified",
        review_reason="provisions_not_supported_yet",
    ),
    "current provisions": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="current provisions",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="provisions",
        rollup_role="component",
        review_reason="provisions_not_supported_yet",
    ),
    "non current provisions": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="non current provisions",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="provisions",
        rollup_role="component",
        review_reason="provisions_not_supported_yet",
    ),
    "income taxes payable": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="income taxes payable",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="tax_liabilities",
        rollup_role="component",
        review_reason="tax_liabilities_not_supported_yet",
    ),
    "tax liabilities": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="tax liabilities",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="tax_liabilities",
        rollup_role="component",
        review_reason="tax_liabilities_not_supported_yet",
    ),
    "deferred tax liabilities": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="deferred tax liabilities",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="tax_liabilities",
        rollup_role="component",
        review_reason="deferred_tax_liabilities_not_supported_yet",
    ),
    "deferred revenue": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="deferred revenue",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="deferred_revenue",
        rollup_role="component",
        review_reason="deferred_revenue_not_supported_yet",
    ),
    "contract liabilities": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="contract liabilities",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="deferred_revenue",
        rollup_role="component",
        review_reason="contract_liabilities_not_supported_yet",
    ),
    "total liabilities and equity": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="total liabilities and equity",
        matched_rule_kind="special_review",
        concept_category="composite_label",
        concept_family="total_liabilities",
        rollup_role="composite",
        review_reason="accounting_equation_total_not_liabilities_only",
    ),
    "total liabilities and shareholders equity": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="total liabilities and shareholders equity",
        matched_rule_kind="special_review",
        concept_category="composite_label",
        concept_family="total_liabilities",
        rollup_role="composite",
        review_reason="accounting_equation_total_not_liabilities_only",
    ),
    "total liabilities and stockholders equity": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="total liabilities and stockholders equity",
        matched_rule_kind="special_review",
        concept_category="composite_label",
        concept_family="total_liabilities",
        rollup_role="composite",
        review_reason="accounting_equation_total_not_liabilities_only",
    ),
}

_SPECIAL_LIABILITY_RULES.update(
    {
        alias: _asset_rule(
            mapping_status="deferred",
            canonical_label=None,
            display_label=None,
            matched_alias=alias,
            matched_rule_kind="special_review",
            concept_category="deferred_canonical",
            concept_family="debt_and_borrowings",
            rollup_role=rollup_role,
            review_reason="debt_not_supported_yet",
        )
        for alias, rollup_role in (
            ("short term debt", "component"),
            ("current debt", "component"),
            ("current portion of long term debt", "component"),
            ("long term debt", "component"),
            ("total debt", "total"),
        )
    }
)
