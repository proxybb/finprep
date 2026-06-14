import pandas as pd
import pytest

from cleaning.mapping import MAPPING_METADATA_COLUMNS
# TODO: map_statement_rows is defined in old_engine_files/generic_mapping.py and has not yet
# been ported to the refactored cleaning.mapping package. Update this import when the
# balance-sheet mapping module is added under cleaning/mapping/.


def _map_labels(labels):
    df = pd.DataFrame({"line_item": labels, "2022": [100] * len(labels)})
    mapped_df, audit_records = map_statement_rows(df, "balance_sheet")
    return mapped_df, audit_records


def _map_labels_is(labels):
    df = pd.DataFrame({"line_item": labels, "2022": [100] * len(labels)})
    mapped_df, audit_records = map_statement_rows(df, "income_statement")
    return mapped_df, audit_records


def test_auto_maps_core_balance_sheet_asset_labels():
    mapped_df, _ = _map_labels(
        [
            "cash and cash equivalents",
            "trade receivables",
            "inventories",
            "total current assets",
            "property plant and equipment net",
            "total assets",
        ]
    )

    assert mapped_df["mapping_status"].tolist() == ["auto_mapped"] * 6
    assert mapped_df["canonical_label"].tolist() == [
        "cash_and_equivalents",
        "accounts_receivable",
        "inventory",
        "current_assets",
        "ppe",
        "total_assets",
    ]
    assert mapped_df["display_label"].tolist() == [
        "Cash and Cash Equivalents",
        "Accounts Receivable",
        "Inventory",
        "Current Assets",
        "PP&E",
        "Total Assets",
    ]


def test_preserves_numeric_values_and_signs():
    df = pd.DataFrame(
        {
            "line_item": ["cash and cash equivalents", "trade receivables"],
            "2022": [1200, -50],
            "2023": [1400, -75],
        }
    )

    mapped_df, _ = map_statement_rows(df, "balance_sheet")

    assert mapped_df["2022"].tolist() == [1200, -50]
    assert mapped_df["2023"].tolist() == [1400, -75]


def test_does_not_mutate_input_dataframe():
    df = pd.DataFrame(
        {
            "line_item": ["cash and cash equivalents", "total assets"],
            "2022": [100, 200],
        }
    )
    original = df.copy(deep=True)

    map_statement_rows(df, "balance_sheet")

    pd.testing.assert_frame_equal(df, original)


def test_does_not_drop_rows():
    df = pd.DataFrame(
        {
            "line_item": ["cash and cash equivalents", "not a mapped label", "total assets"],
            "2022": [100, 150, 200],
        }
    )

    mapped_df, _ = map_statement_rows(df, "balance_sheet")

    assert len(mapped_df.index) == len(df.index)
    assert mapped_df["line_item"].tolist() == df["line_item"].tolist()


def test_special_labels_are_not_forced_into_narrow_canonicals():
    mapped_df, _ = _map_labels(
        [
            "cash on hand",
            "cash and short term investments",
            "receivables",
            "trade and other receivables",
            "fixed assets",
            "right of use assets",
        ]
    )

    assert mapped_df.loc[0, "mapping_status"] == "unmapped"
    assert pd.isna(mapped_df.loc[0, "canonical_label"])

    assert mapped_df.loc[1, "mapping_status"] == "review_only"
    assert mapped_df.loc[1, "concept_category"] == "composite_label"
    assert mapped_df.loc[1, "concept_family"] == "liquidity"

    assert mapped_df.loc[2, "mapping_status"] == "unmapped"
    assert pd.isna(mapped_df.loc[2, "canonical_label"])

    assert mapped_df.loc[3, "mapping_status"] == "review_only"
    assert mapped_df.loc[3, "canonical_label"] == "receivables_total"
    assert mapped_df.loc[3, "concept_category"] == "composite_label"

    assert mapped_df.loc[4, "mapping_status"] == "review_only"
    assert mapped_df.loc[4, "concept_category"] == "conditional_label"
    assert mapped_df.loc[4, "canonical_label"] != "ppe"

    assert mapped_df.loc[5, "mapping_status"] == "deferred"
    assert mapped_df.loc[5, "canonical_label"] != "ppe"


def test_restricted_cash_flag_is_review_only():
    mapped_df, _ = _map_labels(["cash and cash equivalents and restricted cash"])

    assert mapped_df.loc[0, "includes_restricted_cash"] is True
    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert mapped_df.loc[0, "canonical_label"] != "cash_and_equivalents"
    assert mapped_df.loc[0, "review_reason"] == "restricted_cash_scope"


def test_no_fuzzy_matching():
    mapped_df, _ = _map_labels(["trad receivable", "cash equivalent", "totl assets"])

    assert mapped_df["mapping_status"].tolist() == ["unmapped", "unmapped", "unmapped"]
    assert mapped_df["canonical_label"].isna().all()


@pytest.mark.parametrize("statement_type", ["cash_flow_statement"])
def test_invalid_or_unsupported_statement_type_raises_value_error(statement_type):
    df = pd.DataFrame({"line_item": ["total assets"], "2022": [100]})

    with pytest.raises(
        ValueError,
        match="Only balance_sheet and income_statement mapping is implemented",
    ):
        map_statement_rows(df, statement_type)


def test_every_row_gets_complete_metadata_columns_and_audit_fields():
    df = pd.DataFrame({"line_item": ["total assets", "unknown label"], "2022": [100, 50]})

    mapped_df, audit_records = map_statement_rows(df, "balance_sheet")

    for column in MAPPING_METADATA_COLUMNS:
        assert column in mapped_df.columns
    assert len(audit_records) == len(df.index)
    for record in audit_records:
        assert set(MAPPING_METADATA_COLUMNS).issubset(record.keys())


def test_duplicate_canonical_mappings_are_preserved():
    df = pd.DataFrame(
        {
            "line_item": ["accounts receivable", "trade receivables"],
            "2022": [100, 110],
        }
    )

    mapped_df, _ = map_statement_rows(df, "balance_sheet")

    assert len(mapped_df.index) == 2
    assert mapped_df["line_item"].tolist() == ["accounts receivable", "trade receivables"]
    assert mapped_df["canonical_label"].tolist() == [
        "accounts_receivable",
        "accounts_receivable",
    ]


def test_auto_maps_core_balance_sheet_liability_labels():
    mapped_df, _ = _map_labels(
        [
            "accounts payable",
            "trade payables",
            "current liabilities",
            "total current liabilities",
            "total liabilities",
        ]
    )

    assert mapped_df["mapping_status"].tolist() == ["auto_mapped"] * 5
    assert mapped_df["canonical_label"].tolist() == [
        "accounts_payable",
        "accounts_payable",
        "current_liabilities",
        "current_liabilities",
        "total_liabilities",
    ]
    assert mapped_df["display_label"].tolist() == [
        "Accounts Payable",
        "Accounts Payable",
        "Current Liabilities",
        "Current Liabilities",
        "Total Liabilities",
    ]


def test_broader_and_composite_payables_are_review_only():
    mapped_df, _ = _map_labels(
        [
            "trade and other payables",
            "accounts payable and accrued expenses",
        ]
    )

    assert mapped_df.loc[0, "mapping_status"] == "review_only"
    assert mapped_df.loc[0, "canonical_label"] == "payables_total"
    assert mapped_df.loc[0, "concept_category"] == "composite_label"
    assert mapped_df.loc[0, "review_reason"] == "includes_other_payables"

    assert mapped_df.loc[1, "mapping_status"] == "review_only"
    assert pd.isna(mapped_df.loc[1, "canonical_label"])
    assert mapped_df.loc[1, "canonical_label"] != "accounts_payable"
    assert mapped_df.loc[1, "concept_category"] == "composite_label"
    assert mapped_df.loc[1, "review_reason"] == "combines_payables_and_accruals"


def test_accruals_are_deferred_with_canonical_metadata():
    mapped_df, _ = _map_labels(["accrued expenses", "accrued liabilities"])

    assert mapped_df["mapping_status"].tolist() == ["deferred", "deferred"]
    assert mapped_df["canonical_label"].tolist() == ["accrued_expenses", "accrued_expenses"]
    assert mapped_df["concept_family"].tolist() == ["accruals", "accruals"]
    assert mapped_df["review_reason"].tolist() == [
        "accrued_expenses_not_supported_in_analysis_yet",
        "accrued_expenses_not_supported_in_analysis_yet",
    ]


def test_debt_labels_are_deferred_not_mapped_to_liability_totals():
    mapped_df, _ = _map_labels(
        [
            "short term debt",
            "current portion of long term debt",
            "long term debt",
            "total debt",
            "borrowings",
        ]
    )

    assert mapped_df["mapping_status"].tolist() == ["deferred"] * 5
    assert mapped_df["concept_family"].tolist() == ["debt_and_borrowings"] * 5
    assert not (mapped_df["canonical_label"] == "total_liabilities").any()
    assert mapped_df["review_reason"].tolist() == [
        "debt_not_supported_yet",
        "debt_not_supported_yet",
        "debt_not_supported_yet",
        "debt_not_supported_yet",
        "borrowings_not_supported_yet",
    ]


def test_lease_provision_tax_and_deferred_revenue_labels_are_deferred():
    mapped_df, _ = _map_labels(
        [
            "lease liabilities",
            "provisions",
            "deferred tax liabilities",
            "deferred revenue",
            "contract liabilities",
        ]
    )

    assert mapped_df["mapping_status"].tolist() == ["deferred"] * 5
    assert mapped_df["concept_family"].tolist() == [
        "lease_liabilities",
        "provisions",
        "tax_liabilities",
        "deferred_revenue",
        "deferred_revenue",
    ]
    assert mapped_df["review_reason"].tolist() == [
        "lease_liabilities_not_supported_yet",
        "provisions_not_supported_yet",
        "deferred_tax_liabilities_not_supported_yet",
        "deferred_revenue_not_supported_yet",
        "contract_liabilities_not_supported_yet",
    ]


def test_equation_totals_are_not_mapped_to_total_liabilities():
    mapped_df, _ = _map_labels(
        [
            "total liabilities and equity",
            "total liabilities and shareholders equity",
        ]
    )

    assert mapped_df["mapping_status"].tolist() == ["review_only", "review_only"]
    assert mapped_df["concept_category"].tolist() == ["composite_label", "composite_label"]
    assert mapped_df["concept_family"].tolist() == [
        "total_equity_and_liabilities",
        "total_equity_and_liabilities",
    ]
    assert not (mapped_df["canonical_label"] == "total_liabilities").any()
    assert mapped_df["review_reason"].tolist() == [
        "accounting_equation_total_not_equity_only",
        "accounting_equation_total_not_equity_only",
    ]


def test_liability_mapping_preserves_numeric_values_and_signs():
    df = pd.DataFrame(
        {
            "line_item": ["accounts payable", "total liabilities"],
            "2022": [-300, 500],
            "2023": [-325, 550],
        }
    )

    mapped_df, _ = map_statement_rows(df, "balance_sheet")

    assert mapped_df["2022"].tolist() == [-300, 500]
    assert mapped_df["2023"].tolist() == [-325, 550]


def test_liability_mapping_does_not_mutate_input_dataframe():
    df = pd.DataFrame(
        {
            "line_item": ["accounts payable", "total liabilities"],
            "2022": [100, 200],
        }
    )
    original = df.copy(deep=True)

    map_statement_rows(df, "balance_sheet")

    pd.testing.assert_frame_equal(df, original)


def test_liability_mapping_does_not_drop_rows():
    df = pd.DataFrame(
        {
            "line_item": ["accounts payable", "unknown liability", "total liabilities"],
            "2022": [100, 150, 200],
        }
    )

    mapped_df, _ = map_statement_rows(df, "balance_sheet")

    assert len(mapped_df.index) == len(df.index)
    assert mapped_df["line_item"].tolist() == df["line_item"].tolist()


def test_liability_mapping_does_not_fuzzy_match():
    mapped_df, _ = _map_labels(["acounts payable", "totl liabilities", "curent liabilities"])

    assert mapped_df["mapping_status"].tolist() == ["unmapped", "unmapped", "unmapped"]
    assert mapped_df["canonical_label"].isna().all()


def test_liability_mapping_every_row_gets_complete_metadata():
    df = pd.DataFrame({"line_item": ["accounts payable", "unknown liability"], "2022": [100, 50]})

    mapped_df, audit_records = map_statement_rows(df, "balance_sheet")

    for column in MAPPING_METADATA_COLUMNS:
        assert column in mapped_df.columns
    assert len(audit_records) == len(df.index)
    for record in audit_records:
        assert set(MAPPING_METADATA_COLUMNS).issubset(record.keys())


def test_duplicate_liability_canonical_mappings_are_preserved():
    df = pd.DataFrame(
        {
            "line_item": ["accounts payable", "trade payables"],
            "2022": [100, 110],
        }
    )

    mapped_df, _ = map_statement_rows(df, "balance_sheet")

    assert len(mapped_df.index) == 2
    assert mapped_df["line_item"].tolist() == ["accounts payable", "trade payables"]
    assert mapped_df["canonical_label"].tolist() == [
        "accounts_payable",
        "accounts_payable",
    ]


def test_auto_maps_explicit_total_equity():
    mapped_df, _ = _map_labels(["total equity"])

    assert mapped_df.loc[0, "mapping_status"] == "auto_mapped"
    assert mapped_df.loc[0, "canonical_label"] == "total_equity"
    assert mapped_df.loc[0, "display_label"] == "Total Equity"
    assert mapped_df.loc[0, "concept_family"] == "total_equity"
    assert mapped_df.loc[0, "rollup_role"] == "total"


def test_owner_only_equity_labels_are_review_only_not_total_equity():
    mapped_df, _ = _map_labels(
        [
            "shareholders equity",
            "stockholders equity",
            "total shareholders equity",
            "equity attributable to owners of the parent",
        ]
    )

    assert mapped_df["mapping_status"].tolist() == ["review_only"] * 4
    assert mapped_df["canonical_label"].isna().all()
    assert mapped_df["concept_category"].tolist() == ["conditional_label"] * 4
    assert mapped_df["concept_family"].tolist() == ["owner_equity"] * 4
    assert mapped_df["review_reason"].tolist() == [
        "owner_only_equity_may_exclude_non_controlling_interests",
        "owner_only_equity_may_exclude_non_controlling_interests",
        "owner_only_equity_may_exclude_non_controlling_interests",
        "owner_only_equity_may_exclude_non_controlling_interests",
    ]


def test_equity_components_are_deferred():
    mapped_df, _ = _map_labels(
        [
            "retained earnings",
            "accumulated deficit",
            "share capital",
            "additional paid in capital",
            "treasury stock",
            "accumulated other comprehensive income",
        ]
    )

    assert mapped_df["mapping_status"].tolist() == ["deferred"] * 6
    assert mapped_df["canonical_label"].isna().all()
    assert mapped_df["concept_family"].tolist() == ["equity_components"] * 6
    assert mapped_df["review_reason"].tolist() == ["equity_component_not_supported_yet"] * 6


def test_non_controlling_interest_labels_are_deferred():
    mapped_df, _ = _map_labels(
        [
            "non controlling interests",
            "non-controlling interests",
            "minority interest",
        ]
    )

    assert mapped_df["mapping_status"].tolist() == ["deferred"] * 3
    assert mapped_df["canonical_label"].isna().all()
    assert mapped_df["concept_family"].tolist() == ["non_controlling_interest"] * 3
    assert mapped_df["review_reason"].tolist() == [
        "non_controlling_interest_not_supported_yet",
        "non_controlling_interest_not_supported_yet",
        "non_controlling_interest_not_supported_yet",
    ]


def test_equity_equation_totals_are_not_mapped_to_total_equity():
    mapped_df, _ = _map_labels(
        [
            "total equity and liabilities",
            "total liabilities and equity",
            "total liabilities and shareholders equity",
        ]
    )

    assert mapped_df["mapping_status"].tolist() == ["review_only"] * 3
    assert mapped_df["canonical_label"].isna().all()
    assert mapped_df["concept_category"].tolist() == ["composite_label"] * 3
    assert mapped_df["concept_family"].tolist() == ["total_equity_and_liabilities"] * 3
    assert mapped_df["review_reason"].tolist() == [
        "accounting_equation_total_not_equity_only",
        "accounting_equation_total_not_equity_only",
        "accounting_equation_total_not_equity_only",
    ]


def test_broad_equity_label_is_unmapped():
    mapped_df, _ = _map_labels(["equity"])

    assert mapped_df.loc[0, "mapping_status"] == "unmapped"
    assert pd.isna(mapped_df.loc[0, "canonical_label"])
    assert mapped_df.loc[0, "concept_category"] == "broad_label"
    assert mapped_df.loc[0, "concept_family"] == "total_equity"


def test_equity_mapping_preserves_numeric_values_and_signs():
    df = pd.DataFrame(
        {
            "line_item": ["total equity", "retained earnings"],
            "2022": [1000, -250],
            "2023": [1200, -200],
        }
    )

    mapped_df, _ = map_statement_rows(df, "balance_sheet")

    assert mapped_df["2022"].tolist() == [1000, -250]
    assert mapped_df["2023"].tolist() == [1200, -200]


def test_equity_mapping_does_not_mutate_input_dataframe():
    df = pd.DataFrame(
        {
            "line_item": ["total equity", "retained earnings"],
            "2022": [100, 200],
        }
    )
    original = df.copy(deep=True)

    map_statement_rows(df, "balance_sheet")

    pd.testing.assert_frame_equal(df, original)


def test_equity_mapping_does_not_drop_rows():
    df = pd.DataFrame(
        {
            "line_item": ["total equity", "unknown equity label", "retained earnings"],
            "2022": [100, 150, 200],
        }
    )

    mapped_df, _ = map_statement_rows(df, "balance_sheet")

    assert len(mapped_df.index) == len(df.index)
    assert mapped_df["line_item"].tolist() == df["line_item"].tolist()


def test_equity_mapping_does_not_fuzzy_match():
    mapped_df, _ = _map_labels(["shareholdrs equity", "totl equity", "retaned earnings"])

    assert mapped_df["mapping_status"].tolist() == ["unmapped", "unmapped", "unmapped"]
    assert mapped_df["canonical_label"].isna().all()


def test_equity_mapping_every_row_gets_complete_metadata():
    df = pd.DataFrame({"line_item": ["total equity", "unknown equity label"], "2022": [100, 50]})

    mapped_df, audit_records = map_statement_rows(df, "balance_sheet")

    for column in MAPPING_METADATA_COLUMNS:
        assert column in mapped_df.columns
    assert len(audit_records) == len(df.index)
    for record in audit_records:
        assert set(MAPPING_METADATA_COLUMNS).issubset(record.keys())


def test_duplicate_total_equity_mappings_are_preserved():
    df = pd.DataFrame(
        {
            "line_item": ["total equity", "Total Equity"],
            "2022": [100, 110],
        }
    )

    mapped_df, _ = map_statement_rows(df, "balance_sheet")

    assert len(mapped_df.index) == 2
    assert mapped_df["line_item"].tolist() == ["total equity", "Total Equity"]
    assert mapped_df["canonical_label"].tolist() == [
        "total_equity",
        "total_equity",
    ]


def test_is_auto_maps_core_income_statement_labels():
    mapped_df, _ = _map_labels_is(
        [
            "revenue",
            "cost of revenue",
            "gross profit",
            "operating expenses",
            "operating income",
            "ebit",
            "ebitda",
            "net income",
        ]
    )

    assert mapped_df["mapping_status"].tolist() == ["auto_mapped"] * 8
    assert mapped_df["canonical_label"].tolist() == [
        "revenue",
        "cogs",
        "gross_profit",
        "operating_expenses",
        "operating_income",
        "operating_income",
        "ebitda",
        "net_income",
    ]
    assert mapped_df["display_label"].tolist() == [
        "Revenue",
        "Cost of Revenue",
        "Gross Profit",
        "Operating Expenses",
        "Operating Income",
        "Operating Income",
        "EBITDA",
        "Net Income",
    ]


def test_is_expected_sign_for_auto_mapped_rows():
    mapped_df, _ = _map_labels_is(
        [
            "revenue",
            "cost of revenue",
            "cost of goods sold",
            "gross profit",
            "operating expenses",
            "total operating expenses",
            "operating income",
            "ebitda",
            "net income",
        ]
    )

    assert mapped_df.loc[0, "expected_sign"] == "as_reported"
    assert mapped_df.loc[1, "expected_sign"] == "negative"
    assert mapped_df.loc[2, "expected_sign"] == "negative"
    assert mapped_df.loc[3, "expected_sign"] == "as_reported"
    assert mapped_df.loc[4, "expected_sign"] == "negative"
    assert mapped_df.loc[5, "expected_sign"] == "negative"
    assert mapped_df.loc[6, "expected_sign"] == "as_reported"
    assert mapped_df.loc[7, "expected_sign"] == "as_reported"
    assert mapped_df.loc[8, "expected_sign"] == "as_reported"


def test_is_review_only_labels():
    mapped_df, _ = _map_labels_is(
        [
            "gross margin",
            "profit",
            "opex",
            "service revenue",
            "profit from continuing operations",
        ]
    )

    assert mapped_df["mapping_status"].tolist() == ["review_only"] * 5
    assert mapped_df.loc[0, "concept_category"] == "ratio_metric"
    assert mapped_df.loc[1, "concept_family"] == "net_income"
    assert mapped_df.loc[2, "concept_family"] == "operating_expenses"
    assert mapped_df.loc[3, "concept_family"] == "revenue"
    assert mapped_df.loc[4, "concept_family"] == "net_income"
    assert mapped_df["expected_sign"].isna().all()


def test_is_adjusted_variants_are_review_only_not_auto_mapped():
    mapped_df, _ = _map_labels_is(
        [
            "adjusted ebitda",
            "underlying ebitda",
            "adjusted operating profit",
        ]
    )

    assert mapped_df["mapping_status"].tolist() == ["review_only"] * 3
    assert mapped_df["concept_category"].tolist() == ["management_defined_metric"] * 3
    assert not (mapped_df["canonical_label"] == "ebitda").any()
    assert not (mapped_df["canonical_label"] == "operating_income").any()
    assert mapped_df["expected_sign"].isna().all()


def test_is_deferred_labels():
    mapped_df, _ = _map_labels_is(
        [
            "profit before tax",
            "total comprehensive income",
            "selling general and administrative",
            "depreciation and amortization",
            "interest expense",
            "tax expense",
        ]
    )

    assert mapped_df["mapping_status"].tolist() == ["deferred"] * 6
    assert mapped_df["expected_sign"].isna().all()


def test_is_operating_income_aliases():
    mapped_df, _ = _map_labels_is(
        [
            "operating income",
            "operating profit",
            "income from operations",
            "profit from operations",
            "operating earnings",
            "ebit",
        ]
    )

    assert mapped_df["mapping_status"].tolist() == ["auto_mapped"] * 6
    assert (mapped_df["canonical_label"] == "operating_income").all()
    assert (mapped_df["expected_sign"] == "as_reported").all()


def test_is_statement_type_isolation():
    revenue_in_bs, _ = _map_labels(["revenue"])
    total_assets_in_is, _ = _map_labels_is(["total assets"])

    assert revenue_in_bs.loc[0, "mapping_status"] == "unmapped"
    assert pd.isna(revenue_in_bs.loc[0, "canonical_label"])

    assert total_assets_in_is.loc[0, "mapping_status"] == "unmapped"
    assert pd.isna(total_assets_in_is.loc[0, "canonical_label"])


def test_is_preserves_rows_and_values():
    df = pd.DataFrame(
        {
            "line_item": ["revenue", "unknown is label", "net income"],
            "2022": [1000, 50, 200],
            "2023": [1100, 60, 220],
        }
    )

    mapped_df, _ = map_statement_rows(df, "income_statement")

    assert len(mapped_df.index) == len(df.index)
    assert mapped_df["line_item"].tolist() == df["line_item"].tolist()
    assert mapped_df["2022"].tolist() == [1000, 50, 200]
    assert mapped_df["2023"].tolist() == [1100, 60, 220]


def test_bs_expected_sign_is_null():
    mapped_df, _ = _map_labels(
        [
            "cash and cash equivalents",
            "total assets",
            "total liabilities",
            "total equity",
        ]
    )

    assert mapped_df["expected_sign"].isna().all()
