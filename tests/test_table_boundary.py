import pandas as pd

from cleaning.table_boundary import normalize_table_boundary


def test_leading_company_metadata_is_removed_without_capture():
    df = pd.DataFrame(
        {
            "line_item": ["Company: DemoComp", "revenue", "operating income"],
            "2021": [None, 1200, 500],
            "2022": [None, 1400, 650],
        }
    )

    result = normalize_table_boundary(df)

    assert result.status == "bounded"
    assert result.metadata == {}
    assert result.dataframe.to_dict("records") == [
        {"line_item": "revenue", "2021": 1200, "2022": 1400},
        {"line_item": "operating income", "2021": 500, "2022": 650},
    ]


def test_leading_title_metadata_is_removed():
    df = pd.DataFrame(
        {
            "line_item": ["Title: Balance Sheet", "cash", "total assets"],
            "2021": [None, 100, 500],
            "2022": [None, 120, 550],
        }
    )

    result = normalize_table_boundary(df)

    assert result.status == "bounded"
    assert result.metadata == {}
    assert result.dataframe.to_dict("records") == [
        {"line_item": "cash", "2021": 100, "2022": 120},
        {"line_item": "total assets", "2021": 500, "2022": 550},
    ]


def test_leading_statement_currency_and_units_metadata_are_removed():
    df = pd.DataFrame(
        {
            "line_item": [
                "Statement: Income Statement",
                "Currency: USD",
                "Units: USD millions",
                "revenue",
                "operating income",
            ],
            "2021": [None, None, None, 1200, 500],
            "2022": [None, None, None, 1400, 650],
        }
    )

    result = normalize_table_boundary(df)

    assert result.status == "bounded"
    assert result.metadata == {}
    assert result.dataframe.to_dict("records") == [
        {"line_item": "revenue", "2021": 1200, "2022": 1400},
        {"line_item": "operating income", "2021": 500, "2022": 650},
    ]


def test_leading_metadata_with_junk_cells_is_removed():
    df = pd.DataFrame(
        [
            [
                "Company: DemoCo",
                None,
                None,
                "extra header row that should eventually be ignored",
            ],
            ["year", "sales", "operating income", None],
            ["2021", 1200, 500, None],
            ["2022", 1400, 650, None],
        ],
        columns=[0, 1, 2, 3],
    )

    result = normalize_table_boundary(df)

    assert result.status == "bounded"
    assert result.metadata == {}
    assert list(result.dataframe.columns) == ["year", "sales", "operating income"]
    output_text = result.dataframe.to_string()
    assert "DemoCo" not in output_text
    assert "extra header row that should eventually be ignored" not in output_text


def test_metadata_like_row_in_middle_is_preserved():
    df = pd.DataFrame(
        {
            "line_item": [
                "Company: DemoComp",
                "revenue",
                "Company: Segment A",
                "operating income",
            ],
            "2021": [None, 1200, 300, 500],
            "2022": [None, 1400, 350, 650],
        }
    )

    result = normalize_table_boundary(df)

    assert result.metadata == {}
    assert result.dataframe.to_dict("records") == [
        {"line_item": "revenue", "2021": 1200, "2022": 1400},
        {"line_item": "Company: Segment A", "2021": 300, "2022": 350},
        {"line_item": "operating income", "2021": 500, "2022": 650},
    ]


def test_header_row_is_promoted_when_metadata_was_parsed_as_headers():
    df = pd.DataFrame(
        [
            ["Title: Balance Sheet", "", "", ""],
            ["Year", "Sales", "Operating Income", ""],
            ["2021", 1200, 500, ""],
            ["2022", 1400, 650, ""],
        ],
        columns=["Company: DemoComp", "Unnamed: 1", "Unnamed: 2", "Unnamed: 3"],
    )

    result = normalize_table_boundary(df)

    assert result.status == "bounded"
    assert result.action == "header_row_promoted"
    assert result.metadata == {}
    assert list(result.dataframe.columns) == ["year", "sales", "operating income"]
    assert result.dataframe.to_dict("records") == [
        {"year": "2021", "sales": 1200, "operating income": 500},
        {"year": "2022", "sales": 1400, "operating income": 650},
    ]


def test_uncertain_table_boundary_stays_unchanged_conservatively():
    df = pd.DataFrame(
        {
            "metric": ["revenue", "cogs"],
            "current": [100, 40],
            "prior": [120, 50],
        }
    )

    result = normalize_table_boundary(df)

    assert result.status == "unchanged"
    assert result.action == "no_change"
    assert result.metadata == {}
    assert result.dataframe.equals(df)


def test_annotation_columns_are_removed_from_cleaned_working_table():
    df = pd.DataFrame(
        [
            ["sales", 1200, 1250, "review", "ignore", "used as label"],
            ["operating income", 500, 550, "check", "ignore", "used as label"],
        ],
        columns=["line_item", "2021", "2021", "notes", "extra blank col", "description"],
    )

    result = normalize_table_boundary(df)

    assert result.status == "bounded"
    assert result.action == "annotation_columns_removed"
    assert list(result.dataframe.columns) == [
        "line_item",
        "2021",
        "2021",
        "description",
    ]
    assert "notes" not in result.dataframe.columns
    assert "extra blank col" not in result.dataframe.columns
