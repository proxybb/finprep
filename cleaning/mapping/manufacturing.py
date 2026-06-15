"""Manufacturing IFRS financial statement mapping."""
from __future__ import annotations

import pandas as pd

from cleaning.mapping.base import MAPPING_METADATA_COLUMNS, normalize_mapping_label

_UNMAPPED_RULE: dict = {
    "mapping_status": "unmapped",
    "canonical_label": None,
    "display_label": None,
    "matched_alias": None,
    "matched_rule_kind": "unmapped",
    "concept_category": None,
    "concept_family": None,
    "rollup_role": None,
    "review_reason": None,
    "includes_restricted_cash": False,
    "template_operator": None,
    "row_type": None,
}

_IS_LABEL_RULES: dict[str, dict] = {}


def _add_auto_rules(
    aliases: tuple[str, ...],
    *,
    canonical_label: str,
    display_label: str,
    concept_category: str,
    concept_family: str,
    rollup_role: str,
    template_operator: str | None,
    row_type: str,
) -> None:
    for alias in aliases:
        _IS_LABEL_RULES[alias] = {
            "mapping_status": "auto_mapped",
            "canonical_label": canonical_label,
            "display_label": display_label,
            "matched_alias": alias,
            "matched_rule_kind": "auto_map",
            "concept_category": concept_category,
            "concept_family": concept_family,
            "rollup_role": rollup_role,
            "review_reason": None,
            "includes_restricted_cash": False,
            "template_operator": template_operator,
            "row_type": row_type,
        }


def _add_review_rules(
    aliases: tuple[str, ...],
    *,
    review_reason: str,
    concept_category: str | None = None,
    concept_family: str | None = None,
    rollup_role: str | None = None,
) -> None:
    for alias in aliases:
        _IS_LABEL_RULES[alias] = {
            "mapping_status": "review_only",
            "canonical_label": None,
            "display_label": None,
            "matched_alias": alias,
            "matched_rule_kind": "review_only",
            "concept_category": concept_category,
            "concept_family": concept_family,
            "rollup_role": rollup_role,
            "review_reason": review_reason,
            "includes_restricted_cash": False,
            "template_operator": None,
            "row_type": None,
        }


# === AUTO-MAP RULES ===

_add_auto_rules(
    ("revenue", "total revenue", "group revenue", "sales", "net sales", "turnover", "net revenue"),
    canonical_label="revenue",
    display_label="Revenue",
    concept_category="reported_concept",
    concept_family="revenue",
    rollup_role="component",
    template_operator=None,
    row_type="fixed",
)

_add_auto_rules(
    ("cost of sales", "cost of goods sold", "cost of revenue"),
    canonical_label="cogs",
    display_label="Cost of Sales",
    concept_category="reported_concept",
    concept_family="cost_of_sales",
    rollup_role="component",
    template_operator="-",
    row_type="fixed",
)

_add_auto_rules(
    ("gross profit",),
    canonical_label="gross_profit",
    display_label="Gross Profit",
    concept_category="reported_concept",
    concept_family="gross_profit",
    rollup_role="subtotal",
    template_operator="=",
    row_type="fixed",
)

_add_auto_rules(
    (
        "selling expenses",
        "distribution expenses",
        "selling and distribution expenses",
        "selling and marketing expenses",
    ),
    canonical_label="selling_expenses",
    display_label="Selling Expenses",
    concept_category="reported_concept",
    concept_family="operating_expenses",
    rollup_role="component",
    template_operator="-",
    row_type="dynamic",
)

_add_auto_rules(
    (
        "administrative expenses",
        "general and administrative expenses",
        "selling general and administrative expenses",
        "selling and general administrative expenses",
    ),
    canonical_label="administrative_expenses",
    display_label="Administrative Expenses",
    concept_category="reported_concept",
    concept_family="operating_expenses",
    rollup_role="component",
    template_operator="-",
    row_type="dynamic",
)

_add_auto_rules(
    (
        "research and development expenses",
        "research and development costs",
        "r and d expenses",
        "rd expenses",
    ),
    canonical_label="rd_expenses",
    display_label="Research and Development Expenses",
    concept_category="reported_concept",
    concept_family="operating_expenses",
    rollup_role="component",
    template_operator="-",
    row_type="dynamic",
)

_add_auto_rules(
    ("other operating expenses", "other expenses"),
    canonical_label="other_operating_expenses",
    display_label="Other Operating Expenses",
    concept_category="reported_concept",
    concept_family="operating_expenses",
    rollup_role="component",
    template_operator="-",
    row_type="dynamic",
)

_add_auto_rules(
    ("other operating income", "other income"),
    canonical_label="other_operating_income",
    display_label="Other Operating Income",
    concept_category="reported_concept",
    concept_family="operating_income",
    rollup_role="component",
    template_operator="+",
    row_type="dynamic",
)

_add_auto_rules(
    (
        "operating profit",
        "operating income",
        "income from operations",
        "profit from operations",
        "operating result",
        "ebit",
    ),
    canonical_label="operating_profit",
    display_label="Operating Profit",
    concept_category="reported_concept",
    concept_family="operating_profit",
    rollup_role="subtotal",
    template_operator="=",
    row_type="fixed",
)

_add_auto_rules(
    ("financial income", "interest income", "finance income", "finance revenue"),
    canonical_label="finance_income",
    display_label="Finance Income",
    concept_category="reported_concept",
    concept_family="finance",
    rollup_role="component",
    template_operator="+",
    row_type="fixed",
)

_add_auto_rules(
    (
        "financial expense",
        "financial expenses",
        "interest expense",
        "interest expenses",
        "finance costs",
        "finance charges",
    ),
    canonical_label="finance_costs",
    display_label="Finance Costs",
    concept_category="reported_concept",
    concept_family="finance",
    rollup_role="component",
    template_operator="-",
    row_type="fixed",
)

_add_auto_rules(
    (
        "income taxes",
        "income tax expense",
        "income tax expenses",
        "taxes",
        "tax expense",
        "taxation",
    ),
    canonical_label="income_tax_expense",
    display_label="Income Tax Expense",
    concept_category="reported_concept",
    concept_family="tax",
    rollup_role="component",
    template_operator="-",
    row_type="fixed",
)

_add_auto_rules(
    (
        "net income",
        "profit for the year",
        "profit for the period",
        "net earnings",
        "net profit",
        "profit after tax",
        "income after taxes",
    ),
    canonical_label="net_income",
    display_label="Net Income",
    concept_category="reported_concept",
    concept_family="net_income",
    rollup_role="subtotal",
    template_operator="=",
    row_type="fixed",
)

_add_auto_rules(
    ("ebitda", "earnings before interest taxes depreciation and amortization"),
    canonical_label="ebitda",
    display_label="EBITDA",
    concept_category="management_defined_metric",
    concept_family="ebitda",
    rollup_role="supplementary",
    template_operator=None,
    row_type="supplementary",
)

# === D&A — review_only despite having aliases ===
# "depreciation & amortization" and "depreciation & amortisation" normalize to
# "depreciation and amortization" and "depreciation and amortisation" respectively.

_add_review_rules(
    ("depreciation and amortization", "depreciation and amortisation"),
    concept_category="reported_concept",
    concept_family="da",
    rollup_role="supplementary",
    review_reason="placement_ambiguous",
)

# === REVIEW-ONLY RULES ===
# "gross margin %" normalizes to "gross margin" due to punctuation stripping,
# so only one entry is stored; the ratio_or_monetary_ambiguous reason covers both inputs.

_add_review_rules(
    ("gross margin",),
    review_reason="ratio_or_monetary_ambiguous",
)

_add_review_rules(
    ("trading operating profit",),
    review_reason="management_subtotal",
)

_add_review_rules(
    ("profit before financial result and income taxes",),
    review_reason="non_standard_subtotal",
)

_add_review_rules(
    ("profit before tax",),
    review_reason="non_standard_subtotal",
)

_add_review_rules(
    ("total comprehensive income",),
    review_reason="broader_than_net_income",
)

_add_review_rules(
    ("income from associates and joint ventures", "income from discontinued operations"),
    review_reason="non_operating_item",
)

_add_review_rules(
    ("marketing and administration expenses",),
    review_reason="composite_expense",
)

_add_review_rules(
    ("adjusted ebitda", "underlying ebitda", "ebitdaal"),
    concept_category="management_defined_metric",
    review_reason="adjusted_metric",
)

_add_review_rules(
    (
        "profit attributable to owners of the parent",
        "of which attributable to shareholders of the parent",
    ),
    review_reason="attribution_line",
)

_add_review_rules(
    ("income from continuing operations",),
    review_reason="non_standard_subtotal",
)

_add_review_rules(
    ("other revenue",),
    review_reason="narrow_revenue_subtype",
)

_EXTRA_COLUMNS = ["template_operator", "row_type"]
_ALL_COLUMNS = MAPPING_METADATA_COLUMNS + _EXTRA_COLUMNS


def map_statement_rows(
    df: pd.DataFrame,
    statement_type: str,
    industry: str = "manufacturing",
) -> tuple[pd.DataFrame, list[dict]]:
    """Map manufacturing IFRS income statement rows to canonical metadata."""
    if industry != "manufacturing":
        raise ValueError(f"industry '{industry}' is not supported.")
    if statement_type != "income_statement":
        raise ValueError(
            f"statement_type '{statement_type}' is not yet supported in manufacturing mapper."
        )

    mapped_df = df.copy(deep=True)
    label_column = mapped_df.columns[0]

    audit_records: list[dict] = []
    col_data: dict[str, list] = {col: [] for col in _ALL_COLUMNS}

    for row_position, original_label in enumerate(mapped_df[label_column].tolist()):
        normalized = normalize_mapping_label(original_label)
        rule = _IS_LABEL_RULES.get(normalized, _UNMAPPED_RULE)

        record: dict = {
            "original_label": original_label,
            "normalized_label": normalized,
            "statement_type": statement_type,
            "row_position": row_position,
            **rule,
        }
        audit_records.append({k: record[k] for k in MAPPING_METADATA_COLUMNS})
        for col in _ALL_COLUMNS:
            col_data[col].append(record[col])

    for col, values in col_data.items():
        mapped_df[col] = pd.Series(values, index=mapped_df.index, dtype=object)

    return mapped_df, audit_records
