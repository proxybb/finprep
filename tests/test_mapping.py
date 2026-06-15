"""Manufacturing IFRS Income Statement mapping tests."""
import pandas as pd
import pytest

from cleaning.mapping import MAPPING_METADATA_COLUMNS, map_statement_rows


def _map_is(labels, values=None):
    if values is None:
        values = [100] * len(labels)
    df = pd.DataFrame({"line_item": labels, "2022": values})
    return map_statement_rows(df, "income_statement")


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

def test_g7_balance_sheet_statement_type_raises_value_error():
    df = pd.DataFrame({"line_item": ["revenue"], "2022": [100]})
    with pytest.raises(ValueError, match="balance_sheet"):
        map_statement_rows(df, "balance_sheet")


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
