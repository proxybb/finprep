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

_BS_UNMAPPED_RULE: dict = {
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
    "suggested_section": None,
}

_IS_LABEL_RULES: dict[str, dict] = {}
_BS_LABEL_RULES: dict[str, dict] = {}


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


def _add_bs_auto_rules(
    aliases: tuple[str, ...],
    *,
    canonical_label: str,
    display_label: str,
    concept_category: str,
    concept_family: str,
    rollup_role: str,
    suggested_section: str | None,
) -> None:
    for alias in aliases:
        _BS_LABEL_RULES[alias] = {
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
            "suggested_section": suggested_section,
        }


def _add_bs_review_rules(
    aliases: tuple[str, ...],
    *,
    review_reason: str,
    concept_category: str | None = None,
    concept_family: str | None = None,
    rollup_role: str | None = None,
    suggested_section: str | None = None,
) -> None:
    for alias in aliases:
        _BS_LABEL_RULES[alias] = {
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
            "suggested_section": suggested_section,
        }


# === IS AUTO-MAP RULES ===

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

# === IS REVIEW-ONLY RULES ===
# "depreciation & amortization" and "depreciation & amortisation" normalize to
# "depreciation and amortization" and "depreciation and amortisation" respectively.

_add_review_rules(
    ("depreciation and amortization", "depreciation and amortisation"),
    concept_category="reported_concept",
    concept_family="da",
    rollup_role="supplementary",
    review_reason="placement_ambiguous",
)

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

# === BS AUTO-MAP RULES ===
# Aliases are stored in normalized form (post-normalize_mapping_label).

_add_bs_auto_rules(
    ("cash and cash equivalents",),
    canonical_label="cash_and_cash_equivalents",
    display_label="Cash and Cash Equivalents",
    concept_category="reported_concept",
    concept_family="current_assets",
    rollup_role="component",
    suggested_section="current_assets",
)

_add_bs_auto_rules(
    ("inventories", "inventory"),
    canonical_label="inventory",
    display_label="Inventories",
    concept_category="reported_concept",
    concept_family="current_assets",
    rollup_role="component",
    suggested_section="current_assets",
)

_add_bs_auto_rules(
    ("trade and other receivables",),
    canonical_label="trade_and_other_receivables",
    display_label="Trade and Other Receivables",
    concept_category="reported_concept",
    concept_family="current_assets",
    rollup_role="component",
    suggested_section="current_assets",
)

_add_bs_auto_rules(
    ("total current assets", "current assets"),
    canonical_label="current_assets",
    display_label="Total Current Assets",
    concept_category="reported_concept",
    concept_family="current_assets",
    rollup_role="subtotal",
    suggested_section="current_assets",
)

# "Property, plant and equipment" normalizes to "property plant and equipment"
# (comma → space, then deduplicate spaces).
_add_bs_auto_rules(
    ("property plant and equipment",),
    canonical_label="ppe",
    display_label="Property, Plant and Equipment",
    concept_category="reported_concept",
    concept_family="non_current_assets",
    rollup_role="component",
    suggested_section="non_current_assets",
)

_add_bs_auto_rules(
    ("intangible assets", "other intangible assets"),
    canonical_label="intangible_assets",
    display_label="Intangible Assets",
    concept_category="reported_concept",
    concept_family="non_current_assets",
    rollup_role="component",
    suggested_section="non_current_assets",
)

# "total non-current assets" and "non-current assets" normalize to
# "total non current assets" and "non current assets" (hyphen → space).
_add_bs_auto_rules(
    ("total non current assets", "non current assets"),
    canonical_label="non_current_assets",
    display_label="Total Non-current Assets",
    concept_category="reported_concept",
    concept_family="non_current_assets",
    rollup_role="subtotal",
    suggested_section="non_current_assets",
)

_add_bs_auto_rules(
    ("total assets",),
    canonical_label="total_assets",
    display_label="Total Assets",
    concept_category="reported_concept",
    concept_family="assets",
    rollup_role="total",
    suggested_section="assets",
)

# === BS REVIEW-ONLY RULES ===

# Canonical-candidate review-only rows
_add_bs_review_rules(
    ("trade receivables",),
    review_reason="narrow_receivables_label",
    concept_category="reported_concept",
    concept_family="trade_and_other_receivables",
    rollup_role="component",
    suggested_section="current_assets",
)

_add_bs_review_rules(
    ("other receivables",),
    review_reason="narrow_receivables_label",
    concept_category="reported_concept",
    concept_family="trade_and_other_receivables",
    rollup_role="component",
    suggested_section="current_assets",
)

# Dynamic-section review-only rows
_add_bs_review_rules(
    ("goodwill",),
    review_reason="separate_intangible_component",
    concept_category="reported_concept",
    concept_family="non_current_assets",
    rollup_role="component",
    suggested_section="non_current_assets",
)

_add_bs_review_rules(
    ("prepayments",),
    review_reason="prepayment_asset",
    concept_category="reported_concept",
    concept_family="current_assets",
    rollup_role="component",
    suggested_section="current_assets",
)

_add_bs_review_rules(
    ("contract assets",),
    review_reason="contract_balance",
    concept_category="reported_concept",
    concept_family="current_assets",
    rollup_role="component",
    suggested_section="current_assets",
)

_add_bs_review_rules(
    ("current income tax assets",),
    review_reason="tax_asset",
    concept_category="reported_concept",
    concept_family="current_assets",
    rollup_role="component",
    suggested_section="current_assets",
)

_add_bs_review_rules(
    ("deferred tax assets",),
    review_reason="tax_asset",
    concept_category="reported_concept",
    concept_family="non_current_assets",
    rollup_role="component",
    suggested_section="non_current_assets",
)

_add_bs_review_rules(
    ("other current assets",),
    review_reason="broad_other_asset",
    concept_category="reported_concept",
    concept_family="current_assets",
    rollup_role="component",
    suggested_section="current_assets",
)

# "short-term investments" normalizes to "short term investments" (hyphen → space).
_add_bs_review_rules(
    ("short term investments",),
    review_reason="investment_asset",
    concept_category="reported_concept",
    concept_family="current_assets",
    rollup_role="component",
    suggested_section="current_assets",
)

_add_bs_review_rules(
    ("assets held for sale",),
    review_reason="disposal_group_or_non_core_asset",
    concept_category="reported_concept",
    concept_family="current_assets",
    rollup_role="component",
    suggested_section="current_assets",
)

_add_bs_review_rules(
    ("investment property",),
    review_reason="separate_non_current_asset",
    concept_category="reported_concept",
    concept_family="non_current_assets",
    rollup_role="component",
    suggested_section="non_current_assets",
)

_add_bs_review_rules(
    ("investments in associates and joint ventures",),
    review_reason="investment_or_associate_item",
    concept_category="reported_concept",
    concept_family="non_current_assets",
    rollup_role="component",
    suggested_section="non_current_assets",
)

_add_bs_review_rules(
    ("investments accounted for using the equity method",),
    review_reason="investment_or_associate_item",
    concept_category="reported_concept",
    concept_family="non_current_assets",
    rollup_role="component",
    suggested_section="non_current_assets",
)

_add_bs_review_rules(
    ("financial assets",),
    review_reason="financial_asset_section_ambiguous",
    concept_category="reported_concept",
    concept_family="assets",
    rollup_role="component",
    suggested_section=None,
)

_add_bs_review_rules(
    ("other financial assets",),
    review_reason="financial_asset_section_ambiguous",
    concept_category="reported_concept",
    concept_family="assets",
    rollup_role="component",
    suggested_section=None,
)

_add_bs_review_rules(
    ("other current financial assets",),
    review_reason="financial_asset",
    concept_category="reported_concept",
    concept_family="current_assets",
    rollup_role="component",
    suggested_section="current_assets",
)

# === BS LIABILITIES AUTO-MAP RULES ===

_add_bs_auto_rules(
    ("trade and other payables",),
    canonical_label="trade_and_other_payables",
    display_label="Trade and Other Payables",
    concept_category="reported_concept",
    concept_family="current_liabilities",
    rollup_role="component",
    suggested_section="current_liabilities",
)

_add_bs_auto_rules(
    ("total current liabilities", "current liabilities"),
    canonical_label="current_liabilities",
    display_label="Total Current Liabilities",
    concept_category="reported_concept",
    concept_family="current_liabilities",
    rollup_role="subtotal",
    suggested_section="current_liabilities",
)

# "total non-current liabilities" and "non-current liabilities" normalize to
# "total non current liabilities" and "non current liabilities" (hyphen → space).
_add_bs_auto_rules(
    ("total non current liabilities", "non current liabilities"),
    canonical_label="non_current_liabilities",
    display_label="Total Non-current Liabilities",
    concept_category="reported_concept",
    concept_family="non_current_liabilities",
    rollup_role="subtotal",
    suggested_section="non_current_liabilities",
)

_add_bs_auto_rules(
    ("total liabilities",),
    canonical_label="total_liabilities",
    display_label="Total Liabilities",
    concept_category="reported_concept",
    concept_family="liabilities",
    rollup_role="total",
    suggested_section="liabilities",
)

# === BS LIABILITIES REVIEW-ONLY RULES ===

# Canonical-candidate review-only row
_add_bs_review_rules(
    ("trade payables",),
    review_reason="narrow_payables_label",
    concept_category="reported_concept",
    concept_family="trade_and_other_payables",
    rollup_role="component",
    suggested_section="current_liabilities",
)

# Current liability dynamic candidates
# "short-term debt and current maturities of long-term debt" normalizes to
# "short term debt and current maturities of long term debt" (hyphen → space).
_add_bs_review_rules(
    (
        "contract liabilities",
        "current provisions",
        "current income tax liabilities",
        "other current liabilities",
        "other current financial liabilities",
        "short term debt and current maturities of long term debt",
        "short term debt",
        "current portion of long term debt",
        "accruals",
        "accrued expenses",
    ),
    review_reason="liability_component",
    concept_category="reported_concept",
    concept_family="current_liabilities",
    rollup_role="component",
    suggested_section="current_liabilities",
)

# Non-current liability dynamic candidates
# "long-term debt", "non-current provisions", etc. normalize to their space forms.
_add_bs_review_rules(
    (
        "long term debt",
        "deferred tax liabilities",
        "non current provisions",
        "other non current liabilities",
        "other non current financial liabilities",
    ),
    review_reason="liability_component",
    concept_category="reported_concept",
    concept_family="non_current_liabilities",
    rollup_role="component",
    suggested_section="non_current_liabilities",
)

# Ambiguous liability dynamic candidates
_add_bs_review_rules(
    (
        "financial debt",
        "provisions",
        "financial liabilities",
        "other financial liabilities",
        "borrowings",
        "debt",
    ),
    review_reason="liability_section_ambiguous",
    concept_category="reported_concept",
    concept_family="liabilities",
    rollup_role="component",
    suggested_section=None,
)

# === BS EQUITY AUTO-MAP RULES ===

_add_bs_auto_rules(
    (
        "total equity attributable to shareholders of the parent",
        "equity attributable to owners of the parent",
        "equity attributable to shareholders of the parent",
        "equity attributable to owners",
    ),
    canonical_label="equity_attributable_to_owners",
    display_label="Equity Attributable to Owners",
    concept_category="reported_concept",
    concept_family="equity",
    rollup_role="component",
    suggested_section="equity",
)

# "non-controlling interests" normalizes to "non controlling interests" (hyphen → space).
_add_bs_auto_rules(
    ("non controlling interests", "noncontrolling interests"),
    canonical_label="non_controlling_interests",
    display_label="Non-controlling Interests",
    concept_category="reported_concept",
    concept_family="equity",
    rollup_role="component",
    suggested_section="equity",
)

_add_bs_auto_rules(
    ("total equity",),
    canonical_label="total_equity",
    display_label="Total Equity",
    concept_category="reported_concept",
    concept_family="equity",
    rollup_role="total",
    suggested_section="equity",
)

# === BS EQUITY REVIEW-ONLY RULES ===

# Company-specific owner equity label (canonical candidate, exact match only)
_add_bs_review_rules(
    ("total equity attributable to shareholders of siemens ag",),
    review_reason="company_specific_owner_equity_label",
    concept_category="reported_concept",
    concept_family="equity_attributable_to_owners",
    rollup_role="component",
    suggested_section="equity",
)

# Equity component dynamic candidates
_add_bs_review_rules(
    (
        "retained earnings",
        "share capital",
        "issued capital",
        "capital reserves",
        "other reserves",
        "treasury shares",
        "accumulated other comprehensive income",
    ),
    review_reason="equity_component",
    concept_category="reported_concept",
    concept_family="equity",
    rollup_role="component",
    suggested_section="equity",
)

_IS_EXTRA_COLUMNS = ["template_operator", "row_type"]
_BS_EXTRA_COLUMNS = ["suggested_section"]


def map_statement_rows(
    df: pd.DataFrame,
    statement_type: str,
    industry: str = "manufacturing",
) -> tuple[pd.DataFrame, list[dict]]:
    """Map manufacturing IFRS statement rows to canonical metadata."""
    if industry != "manufacturing":
        raise ValueError(f"industry '{industry}' is not supported.")
    if statement_type not in ("income_statement", "balance_sheet"):
        raise ValueError(
            f"statement_type '{statement_type}' is not yet supported in manufacturing mapper."
        )

    mapped_df = df.copy(deep=True)
    label_column = mapped_df.columns[0]

    if statement_type == "income_statement":
        label_rules = _IS_LABEL_RULES
        unmapped_rule = _UNMAPPED_RULE
        extra_columns = _IS_EXTRA_COLUMNS
    else:
        label_rules = _BS_LABEL_RULES
        unmapped_rule = _BS_UNMAPPED_RULE
        extra_columns = _BS_EXTRA_COLUMNS

    all_columns = MAPPING_METADATA_COLUMNS + extra_columns
    audit_records: list[dict] = []
    col_data: dict[str, list] = {col: [] for col in all_columns}

    for row_position, original_label in enumerate(mapped_df[label_column].tolist()):
        normalized = normalize_mapping_label(original_label)
        rule = label_rules.get(normalized, unmapped_rule)

        record: dict = {
            "original_label": original_label,
            "normalized_label": normalized,
            "statement_type": statement_type,
            "row_position": row_position,
            **rule,
        }
        audit_records.append({k: record[k] for k in MAPPING_METADATA_COLUMNS})
        for col in all_columns:
            col_data[col].append(record[col])

    for col, values in col_data.items():
        mapped_df[col] = pd.Series(values, index=mapped_df.index, dtype=object)

    return mapped_df, audit_records
