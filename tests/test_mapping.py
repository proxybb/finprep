"""Manufacturing IFRS Income Statement and Balance Sheet mapping tests."""
import pandas as pd
import pytest

from cleaning.mapping import MAPPING_METADATA_COLUMNS, map_statement_rows


def _map_is(labels, values=None):
    if values is None:
        values = [100] * len(labels)
    df = pd.DataFrame({"line_item": labels, "2022": values})
    return map_statement_rows(df, "income_statement")


def _map_bs(labels, values=None):
    if values is None:
        values = [100] * len(labels)
    df = pd.DataFrame({"line_item": labels, "2022": values})
    return map_statement_rows(df, "balance_sheet")


# === Group 1 — Basic auto-map exact matches ===

@pytest.mark.parametrize("alias,expected_canonical", [
    ("turnover", "revenue"),
    ("cost of sales", "cogs"),
    ("gross profit", "gross_profit"),
    ("operating profit", "operating_profit"),
    ("net income", "net_income"),
    ("ebitda", "ebitda"),
])
def test_g1_basic_auto_map_exact_matches(alias, expected_canonical):
    mapped_df, _ = _map_is([alias])
    assert mapped_df.loc[0, "mapping_status"] == "auto_mapped"
    assert mapped_df.loc[0, "canonical_label"] == expected_canonical


# === Group 2 — template_operator values ===

def test_g2_template_operator_revenue_is_null():
    mapped_df, _ = _map_is(["revenue"])
    assert pd.isna(mapped_df.loc[0, "template_operator"])


def test_g2_template_operator_cogs_is_minus():
    mapped_df, _ = _map_is(["cost of sales"])
    assert mapped_df.loc[0, "template_operator"] == "-"


def test_g2_template_operator_gross_profit_is_equals():
    mapped_df, _ = _map_is(["gross profit"])
    assert mapped_df.loc[0, "template_operator"] == "="


def test_g2_template_operator_selling_expenses_is_minus():
    mapped_df, _ = _map_is(["selling expenses"])
    assert mapped_df.loc[0, "template_operator"] == "-"


def test_g2_template_operator_finance_income_is_plus():
    mapped_df, _ = _map_is(["finance income"])
    assert mapped_df.loc[0, "template_operator"] == "+"


def test_g2_template_operator_finance_costs_is_minus():
    mapped_df, _ = _map_is(["finance costs"])
    assert mapped_df.loc[0, "template_operator"] == "-"


def test_g2_template_operator_net_income_is_equals():
    mapped_df, _ = _map_is(["net income"])
    assert mapped_df.loc[0, "template_operator"] == "="


# === Group 3 — row_type values ===

@pytest.mark.parametrize("alias,expected_row_type", [
    ("revenue", "fixed"),
    ("cost of sales", "fixed"),
    ("selling expenses", "dynamic"),
    ("administrative expenses", "dynamic"),
    ("ebitda", "supplementary"),
])
def test_g3_row_type_values(alias, expected_row_type):
    mapped_df, _ = _map_is([alias])
    assert mapped_df.loc[0, "row_type"] == expected_row_type


# === Group 4 — Review-only rules ===

def test_g4_gross_margin_is_review_only_with_ratio_reason():
    mapped_df, _ = _map_is(["gross margin"])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert mapped_df.loc[0, "review_reason"] == "ratio_or_monetary_ambiguous"


def test_g4_profit_is_unmapped_not_review_only():
    mapped_df, _ = _map_is(["profit"])
    assert mapped_df.loc[0, "mapping_status"] == "unmapped"


def test_g4_adjusted_ebitda_is_review_only_with_adjusted_metric_reason():
    mapped_df, _ = _map_is(["adjusted ebitda"])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert mapped_df.loc[0, "review_reason"] == "adjusted_metric"


def test_g4_depreciation_and_amortization_is_review_only_with_placement_ambiguous():
    mapped_df, _ = _map_is(["depreciation and amortization"])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert mapped_df.loc[0, "review_reason"] == "placement_ambiguous"


def test_g4_profit_before_tax_is_review_only_with_non_standard_subtotal():
    mapped_df, _ = _map_is(["profit before tax"])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert mapped_df.loc[0, "review_reason"] == "non_standard_subtotal"


# === Group 5 — No adjusted-to-plain mapping ===

def test_g5_adjusted_ebitda_does_not_map_to_ebitda():
    mapped_df, _ = _map_is(["adjusted ebitda"])
    assert mapped_df.loc[0, "canonical_label"] != "ebitda"
    assert pd.isna(mapped_df.loc[0, "canonical_label"])


def test_g5_underlying_ebitda_does_not_map_to_ebitda():
    mapped_df, _ = _map_is(["underlying ebitda"])
    assert mapped_df.loc[0, "canonical_label"] != "ebitda"
    assert pd.isna(mapped_df.loc[0, "canonical_label"])


# === Group 6 — Canonical preference for operating_profit ===

@pytest.mark.parametrize("alias", [
    "operating profit",
    "operating income",
    "income from operations",
    "profit from operations",
    "ebit",
])
def test_g6_operating_profit_aliases_all_map_to_operating_profit(alias):
    mapped_df, _ = _map_is([alias])
    assert mapped_df.loc[0, "mapping_status"] == "auto_mapped"
    assert mapped_df.loc[0, "canonical_label"] == "operating_profit"


# === Group 7 — Statement type isolation ===

def test_g7_unsupported_statement_type_raises_value_error():
    df = pd.DataFrame({"line_item": ["revenue"], "2022": [100]})
    with pytest.raises(ValueError):
        map_statement_rows(df, "cash_flow_statement")


def test_g7_banking_industry_raises_value_error():
    df = pd.DataFrame({"line_item": ["revenue"], "2022": [100]})
    with pytest.raises(ValueError, match="banking"):
        map_statement_rows(df, "income_statement", industry="banking")


# === Group 8 — Preservation ===

def test_g8_unmapped_rows_remain_in_output_with_preserved_order():
    labels = ["revenue", "something completely unknown", "net income"]
    mapped_df, _ = _map_is(labels)
    assert len(mapped_df) == 3
    assert mapped_df["line_item"].tolist() == labels
    assert mapped_df.loc[0, "canonical_label"] == "revenue"
    assert mapped_df.loc[1, "mapping_status"] == "unmapped"
    assert mapped_df.loc[2, "canonical_label"] == "net_income"


def test_g8_period_column_values_unchanged():
    df = pd.DataFrame(
        {"line_item": ["revenue", "net income"], "2022": [1000, 200], "2023": [1100, 220]}
    )
    mapped_df, _ = map_statement_rows(df, "income_statement")
    assert mapped_df["2022"].tolist() == [1000, 200]
    assert mapped_df["2023"].tolist() == [1100, 220]


def test_g8_input_dataframe_not_mutated():
    df = pd.DataFrame({"line_item": ["revenue", "net income"], "2022": [100, 200]})
    original = df.copy(deep=True)
    map_statement_rows(df, "income_statement")
    pd.testing.assert_frame_equal(df, original)


# === Group 9 — Metadata completeness ===

def test_g9_every_output_row_has_all_metadata_columns():
    df = pd.DataFrame({"line_item": ["revenue", "unknown label"], "2022": [100, 50]})
    mapped_df, _ = map_statement_rows(df, "income_statement")
    for col in MAPPING_METADATA_COLUMNS:
        assert col in mapped_df.columns, f"Missing column: {col}"


def test_g9_every_audit_record_has_all_metadata_column_keys():
    df = pd.DataFrame({"line_item": ["revenue", "unknown label"], "2022": [100, 50]})
    _, audit_records = map_statement_rows(df, "income_statement")
    assert len(audit_records) == 2
    for record in audit_records:
        for col in MAPPING_METADATA_COLUMNS:
            assert col in record, f"Audit record missing key: {col}"


def test_g9_no_deferred_mapping_status_in_is_output():
    labels = [
        "revenue", "cost of sales", "gross profit", "selling expenses",
        "administrative expenses", "operating profit", "net income",
        "ebitda", "depreciation and amortization", "gross margin",
        "adjusted ebitda", "profit before tax", "marketing and administration expenses",
        "an entirely unknown label",
    ]
    mapped_df, audit_records = _map_is(labels)
    assert "deferred" not in mapped_df["mapping_status"].tolist()
    for record in audit_records:
        assert record["mapping_status"] != "deferred"


# === Group 10 — No deferred ===

def test_g10_no_row_in_full_is_output_has_deferred_status():
    labels = [
        "revenue", "total revenue", "sales", "cost of goods sold", "gross profit",
        "selling expenses", "distribution expenses", "administrative expenses",
        "research and development expenses", "other operating expenses", "other income",
        "operating profit", "ebit", "income from operations", "finance income",
        "interest income", "finance costs", "interest expense", "income tax expense",
        "taxes", "net income", "profit for the year", "profit after tax", "ebitda",
        "earnings before interest taxes depreciation and amortization",
        "depreciation and amortization", "gross margin", "trading operating profit",
        "profit before tax", "total comprehensive income",
        "income from associates and joint ventures", "marketing and administration expenses",
        "adjusted ebitda", "underlying ebitda", "ebitdaal",
        "profit attributable to owners of the parent", "income from continuing operations",
        "other revenue", "completely unknown label",
    ]
    mapped_df, _ = _map_is(labels)
    assert "deferred" not in mapped_df["mapping_status"].tolist()


def test_g10_marketing_and_administration_expenses_is_review_only_not_deferred():
    mapped_df, _ = _map_is(["marketing and administration expenses"])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert mapped_df.loc[0, "mapping_status"] != "deferred"


# === Group 11 — BS auto-map exact matches ===

@pytest.mark.parametrize("alias,expected_canonical", [
    ("cash and cash equivalents", "cash_and_cash_equivalents"),
    ("inventories", "inventory"),
    ("trade and other receivables", "trade_and_other_receivables"),
    ("total current assets", "current_assets"),
    ("property, plant and equipment", "ppe"),
    ("other intangible assets", "intangible_assets"),
    ("total non-current assets", "non_current_assets"),
    ("total assets", "total_assets"),
])
def test_g11_bs_auto_map_exact_matches(alias, expected_canonical):
    mapped_df, _ = _map_bs([alias])
    assert mapped_df.loc[0, "mapping_status"] == "auto_mapped"
    assert mapped_df.loc[0, "canonical_label"] == expected_canonical


# === Group 12 — BS review-only canonical candidates ===

def test_g12_trade_receivables_is_review_only():
    mapped_df, _ = _map_bs(["trade receivables"])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert mapped_df.loc[0, "concept_family"] == "trade_and_other_receivables"
    assert mapped_df.loc[0, "suggested_section"] == "current_assets"
    assert mapped_df.loc[0, "review_reason"] == "narrow_receivables_label"


# === Group 13 — Goodwill ===

def test_g13_goodwill_is_review_only():
    mapped_df, _ = _map_bs(["goodwill"])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"


def test_g13_goodwill_does_not_map_to_intangible_assets():
    mapped_df, _ = _map_bs(["goodwill"])
    assert mapped_df.loc[0, "canonical_label"] != "intangible_assets"
    assert pd.isna(mapped_df.loc[0, "canonical_label"])


def test_g13_goodwill_suggested_section_is_non_current_assets():
    mapped_df, _ = _map_bs(["goodwill"])
    assert mapped_df.loc[0, "suggested_section"] == "non_current_assets"


def test_g13_goodwill_review_reason():
    mapped_df, _ = _map_bs(["goodwill"])
    assert mapped_df.loc[0, "review_reason"] == "separate_intangible_component"


# === Group 14 — Ambiguous financial assets ===

def test_g14_financial_assets_is_review_only():
    mapped_df, _ = _map_bs(["financial assets"])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"


def test_g14_financial_assets_suggested_section_is_null():
    mapped_df, _ = _map_bs(["financial assets"])
    assert pd.isna(mapped_df.loc[0, "suggested_section"])


def test_g14_financial_assets_review_reason():
    mapped_df, _ = _map_bs(["financial assets"])
    assert mapped_df.loc[0, "review_reason"] == "financial_asset_section_ambiguous"


# === Group 15 — Suggested sections ===

def test_g15_prepayments_suggested_section_is_current_assets():
    mapped_df, _ = _map_bs(["prepayments"])
    assert mapped_df.loc[0, "suggested_section"] == "current_assets"


def test_g15_deferred_tax_assets_suggested_section_is_non_current_assets():
    mapped_df, _ = _map_bs(["deferred tax assets"])
    assert mapped_df.loc[0, "suggested_section"] == "non_current_assets"


def test_g15_other_current_financial_assets_suggested_section_is_current_assets():
    mapped_df, _ = _map_bs(["other current financial assets"])
    assert mapped_df.loc[0, "suggested_section"] == "current_assets"


# === Group 16 — Duplicate label preservation ===

def test_g16_duplicate_labels_both_rows_present():
    labels = ["financial assets", "financial assets"]
    mapped_df, _ = _map_bs(labels)
    assert len(mapped_df) == 2


def test_g16_duplicate_labels_row_order_preserved():
    labels = ["financial assets", "financial assets"]
    mapped_df, _ = _map_bs(labels)
    assert mapped_df["line_item"].tolist() == labels


def test_g16_duplicate_labels_values_unchanged():
    labels = ["financial assets", "financial assets"]
    values = [100, 200]
    mapped_df, _ = _map_bs(labels, values)
    assert mapped_df["2022"].tolist() == values


def test_g16_duplicate_labels_both_mapped_same_way():
    labels = ["financial assets", "financial assets"]
    mapped_df, _ = _map_bs(labels)
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert mapped_df.loc[1, "mapping_status"] == "review_only"


# === Group 17 — BS unmapped ===

def test_g17_unknown_bs_label_becomes_unmapped():
    mapped_df, _ = _map_bs(["some completely unknown asset label"])
    assert mapped_df.loc[0, "mapping_status"] == "unmapped"


def test_g17_unknown_bs_label_suggested_section_is_null():
    mapped_df, _ = _map_bs(["some completely unknown asset label"])
    assert pd.isna(mapped_df.loc[0, "suggested_section"])


# === Group 18 — BS metadata completeness ===

def test_g18_bs_output_has_all_base_metadata_columns():
    df = pd.DataFrame({"line_item": ["cash and cash equivalents", "unknown"], "2022": [100, 50]})
    mapped_df, _ = map_statement_rows(df, "balance_sheet")
    for col in MAPPING_METADATA_COLUMNS:
        assert col in mapped_df.columns, f"Missing column: {col}"


def test_g18_bs_output_has_suggested_section_column():
    df = pd.DataFrame({"line_item": ["cash and cash equivalents", "unknown"], "2022": [100, 50]})
    mapped_df, _ = map_statement_rows(df, "balance_sheet")
    assert "suggested_section" in mapped_df.columns


def test_g18_bs_audit_records_have_base_metadata_keys():
    df = pd.DataFrame({"line_item": ["cash and cash equivalents", "unknown"], "2022": [100, 50]})
    _, audit_records = map_statement_rows(df, "balance_sheet")
    assert len(audit_records) == 2
    for record in audit_records:
        for col in MAPPING_METADATA_COLUMNS:
            assert col in record, f"Audit record missing key: {col}"


def test_g18_is_tests_still_pass_after_bs_implementation():
    mapped_df, _ = _map_is(["revenue", "cost of sales", "net income"])
    assert mapped_df.loc[0, "canonical_label"] == "revenue"
    assert mapped_df.loc[1, "canonical_label"] == "cogs"
    assert mapped_df.loc[2, "canonical_label"] == "net_income"


# === Group 19 — Statement type behavior ===

def test_g19_balance_sheet_does_not_raise_value_error():
    df = pd.DataFrame({"line_item": ["cash and cash equivalents"], "2022": [100]})
    result = map_statement_rows(df, "balance_sheet")
    assert result is not None


def test_g19_unsupported_statement_type_raises_value_error():
    df = pd.DataFrame({"line_item": ["revenue"], "2022": [100]})
    with pytest.raises(ValueError):
        map_statement_rows(df, "cash_flow_statement")


# === Group 20 — BS Liabilities auto-map exact matches ===

@pytest.mark.parametrize("alias,expected_canonical", [
    ("trade and other payables", "trade_and_other_payables"),
    ("total current liabilities", "current_liabilities"),
    ("current liabilities", "current_liabilities"),
    ("total non-current liabilities", "non_current_liabilities"),
    ("non-current liabilities", "non_current_liabilities"),
    ("total liabilities", "total_liabilities"),
])
def test_g20_liabilities_auto_map_exact_matches(alias, expected_canonical):
    mapped_df, _ = _map_bs([alias])
    assert mapped_df.loc[0, "mapping_status"] == "auto_mapped"
    assert mapped_df.loc[0, "canonical_label"] == expected_canonical


# === Group 21 — Trade payables canonical candidate ===

def test_g21_trade_payables_is_review_only():
    mapped_df, _ = _map_bs(["trade payables"])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"


def test_g21_trade_payables_canonical_label_is_null():
    mapped_df, _ = _map_bs(["trade payables"])
    assert pd.isna(mapped_df.loc[0, "canonical_label"])


def test_g21_trade_payables_concept_family():
    mapped_df, _ = _map_bs(["trade payables"])
    assert mapped_df.loc[0, "concept_family"] == "trade_and_other_payables"


def test_g21_trade_payables_suggested_section():
    mapped_df, _ = _map_bs(["trade payables"])
    assert mapped_df.loc[0, "suggested_section"] == "current_liabilities"


def test_g21_trade_payables_review_reason():
    mapped_df, _ = _map_bs(["trade payables"])
    assert mapped_df.loc[0, "review_reason"] == "narrow_payables_label"


# === Group 22 — Current liability dynamic candidates ===

@pytest.mark.parametrize("alias", [
    "contract liabilities",
    "current provisions",
    "current income tax liabilities",
    "short-term debt and current maturities of long-term debt",
    "accruals",
])
def test_g22_current_liability_candidates_are_review_only(alias):
    mapped_df, _ = _map_bs([alias])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert mapped_df.loc[0, "concept_family"] == "current_liabilities"
    assert mapped_df.loc[0, "suggested_section"] == "current_liabilities"
    assert mapped_df.loc[0, "review_reason"] == "liability_component"


# === Group 23 — Non-current liability dynamic candidates ===

@pytest.mark.parametrize("alias", [
    "long-term debt",
    "deferred tax liabilities",
    "other non-current liabilities",
])
def test_g23_non_current_liability_candidates_are_review_only(alias):
    mapped_df, _ = _map_bs([alias])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert mapped_df.loc[0, "concept_family"] == "non_current_liabilities"
    assert mapped_df.loc[0, "suggested_section"] == "non_current_liabilities"
    assert mapped_df.loc[0, "review_reason"] == "liability_component"


# === Group 24 — Ambiguous liability dynamic candidates ===

@pytest.mark.parametrize("alias", [
    "financial debt",
    "provisions",
])
def test_g24_ambiguous_liabilities_are_review_only_with_null_section(alias):
    mapped_df, _ = _map_bs([alias])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert mapped_df.loc[0, "concept_family"] == "liabilities"
    assert pd.isna(mapped_df.loc[0, "suggested_section"])
    assert mapped_df.loc[0, "review_reason"] == "liability_section_ambiguous"


# === Group 25 — BS Equity auto-map exact matches ===

@pytest.mark.parametrize("alias,expected_canonical", [
    ("total equity attributable to shareholders of the parent", "equity_attributable_to_owners"),
    ("equity attributable to owners of the parent", "equity_attributable_to_owners"),
    ("non-controlling interests", "non_controlling_interests"),
    ("noncontrolling interests", "non_controlling_interests"),
    ("total equity", "total_equity"),
])
def test_g25_equity_auto_map_exact_matches(alias, expected_canonical):
    mapped_df, _ = _map_bs([alias])
    assert mapped_df.loc[0, "mapping_status"] == "auto_mapped"
    assert mapped_df.loc[0, "canonical_label"] == expected_canonical


# === Group 26 — Equity review-only ===

def test_g26_siemens_equity_is_review_only():
    mapped_df, _ = _map_bs(["total equity attributable to shareholders of siemens ag"])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"


def test_g26_siemens_equity_concept_family():
    mapped_df, _ = _map_bs(["total equity attributable to shareholders of siemens ag"])
    assert mapped_df.loc[0, "concept_family"] == "equity_attributable_to_owners"


def test_g26_siemens_equity_suggested_section():
    mapped_df, _ = _map_bs(["total equity attributable to shareholders of siemens ag"])
    assert mapped_df.loc[0, "suggested_section"] == "equity"


def test_g26_siemens_equity_review_reason():
    mapped_df, _ = _map_bs(["total equity attributable to shareholders of siemens ag"])
    assert mapped_df.loc[0, "review_reason"] == "company_specific_owner_equity_label"


def test_g26_retained_earnings_is_review_only_equity_component():
    mapped_df, _ = _map_bs(["retained earnings"])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert mapped_df.loc[0, "concept_family"] == "equity"
    assert mapped_df.loc[0, "suggested_section"] == "equity"
    assert mapped_df.loc[0, "review_reason"] == "equity_component"


# === Group 27 — Duplicate L&E label preservation ===

def test_g27_duplicate_ambiguous_liability_labels_both_rows_present():
    labels = ["debt", "debt"]
    mapped_df, _ = _map_bs(labels)
    assert len(mapped_df) == 2


def test_g27_duplicate_ambiguous_liability_labels_row_order_preserved():
    labels = ["debt", "debt"]
    mapped_df, _ = _map_bs(labels)
    assert mapped_df["line_item"].tolist() == labels


def test_g27_duplicate_ambiguous_liability_labels_values_unchanged():
    labels = ["debt", "debt"]
    values = [500, 600]
    mapped_df, _ = _map_bs(labels, values)
    assert mapped_df["2022"].tolist() == values


def test_g27_duplicate_ambiguous_liability_labels_both_review_only():
    labels = ["debt", "debt"]
    mapped_df, _ = _map_bs(labels)
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert mapped_df.loc[1, "mapping_status"] == "review_only"


def test_g27_duplicate_ambiguous_liability_labels_suggested_section_is_null():
    labels = ["debt", "debt"]
    mapped_df, _ = _map_bs(labels)
    assert pd.isna(mapped_df.loc[0, "suggested_section"])
    assert pd.isna(mapped_df.loc[1, "suggested_section"])


# === Group 28 — BS L&E metadata completeness ===

def test_g28_le_output_has_suggested_section_column():
    labels = ["total liabilities", "total equity", "debt"]
    mapped_df, _ = _map_bs(labels)
    assert "suggested_section" in mapped_df.columns


def test_g28_bs_assets_tests_still_pass_after_le_implementation():
    labels = ["total assets", "cash and cash equivalents", "total current assets"]
    mapped_df, _ = _map_bs(labels)
    assert mapped_df.loc[0, "canonical_label"] == "total_assets"
    assert mapped_df.loc[1, "canonical_label"] == "cash_and_cash_equivalents"
    assert mapped_df.loc[2, "canonical_label"] == "current_assets"


def test_g28_is_tests_still_pass_after_le_implementation():
    labels = ["revenue", "cost of sales", "net income"]
    mapped_df, _ = _map_is(labels)
    assert mapped_df.loc[0, "canonical_label"] == "revenue"
    assert mapped_df.loc[1, "canonical_label"] == "cogs"
    assert mapped_df.loc[2, "canonical_label"] == "net_income"


# === Group 29 — Substring collision guards ===

def test_g29_current_liabilities_auto_maps_not_other_current():
    mapped_df, _ = _map_bs(["current liabilities"])
    assert mapped_df.loc[0, "mapping_status"] == "auto_mapped"
    assert mapped_df.loc[0, "canonical_label"] == "current_liabilities"


def test_g29_other_current_liabilities_is_review_only_not_auto_mapped():
    mapped_df, _ = _map_bs(["other current liabilities"])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert pd.isna(mapped_df.loc[0, "canonical_label"])


def test_g29_non_current_liabilities_auto_maps():
    mapped_df, _ = _map_bs(["non-current liabilities"])
    assert mapped_df.loc[0, "mapping_status"] == "auto_mapped"
    assert mapped_df.loc[0, "canonical_label"] == "non_current_liabilities"


def test_g29_other_non_current_liabilities_is_review_only_not_auto_mapped():
    mapped_df, _ = _map_bs(["other non-current liabilities"])
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert pd.isna(mapped_df.loc[0, "canonical_label"])
