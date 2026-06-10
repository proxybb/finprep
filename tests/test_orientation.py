import pandas as pd

from cleaning.orientation import normalize_orientation


def test_already_standard_table_stays_unchanged():
    df = pd.DataFrame(
        {
            "line_item": ["revenue", "cogs"],
            "2021": [100, 40],
            "2022": [120, 50],
        }
    )

    result = normalize_orientation(df)

    assert result.status == "already_standard"
    assert result.action == "no_change"
    assert result.dataframe.equals(df)


def test_sideways_table_gets_transposed_to_analyst_orientation():
    df = pd.DataFrame(
        {
            "year": ["2021", "2022"],
            "revenue": [100, 120],
            "cogs": [40, 50],
        }
    )

    result = normalize_orientation(df)

    assert result.status == "transposed"
    assert result.action == "transpose"
    assert list(result.dataframe.columns) == ["line_item", "2021", "2022"]
    assert result.dataframe.to_dict("records") == [
        {"line_item": "revenue", "2021": 100, "2022": 120},
        {"line_item": "cogs", "2021": 40, "2022": 50},
    ]


def test_uncertain_table_stays_unchanged():
    df = pd.DataFrame(
        {
            "metric": ["revenue", "cogs"],
            "current": [100, 40],
            "prior": [120, 50],
        }
    )

    result = normalize_orientation(df)

    assert result.status == "uncertain"
    assert result.action == "no_change"
    assert result.dataframe.equals(df)


def test_forecast_and_estimate_periods_do_not_drive_orientation():
    df = pd.DataFrame(
        {
            "period": ["2024E", "2025F"],
            "revenue": [150, 170],
            "cogs": [60, 70],
        }
    )

    result = normalize_orientation(df)

    assert result.status == "uncertain"
    assert result.action == "no_change"
    assert result.dataframe.equals(df)


def test_orientation_does_not_semantically_map_labels():
    df = pd.DataFrame(
        {
            "year": ["2021", "2022"],
            "sales": [100, 120],
            "operating income": [20, 30],
        }
    )

    result = normalize_orientation(df)

    assert result.status == "transposed"
    output_text = result.dataframe.to_string()
    assert "sales" in output_text
    assert "operating income" in output_text
    assert "revenue" not in output_text
    assert "ebit" not in output_text


def test_duplicate_period_columns_are_preserved():
    df = pd.DataFrame(
        [
            ["2021", 100, 40],
            ["2021", 110, 45],
            ["2022", 120, 50],
        ],
        columns=["year", "revenue", "cogs"],
    )

    result = normalize_orientation(df)

    assert result.status == "transposed"
    assert list(result.dataframe.columns) == ["line_item", "2021", "2021", "2022"]
    assert result.dataframe.shape == (2, 4)
