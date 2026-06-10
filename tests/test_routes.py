from io import BytesIO
from pathlib import Path

import pandas as pd

from web import create_app


def _client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def _xlsx_file() -> BytesIO:
    file = BytesIO()
    df = pd.DataFrame(
        {
            "Line Item": ["Cash", "Total Assets"],
            "2023": [1200, 5000],
        }
    )
    with pd.ExcelWriter(file, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    file.seek(0)
    return file


def test_existing_routes_return_200():
    client = _client()

    for path in ["/", "/data", "/data/cleaned", "/companies", "/analysis"]:
        response = client.get(path)
        assert response.status_code == 200


def test_data_renders_with_no_files():
    response = _client().get("/data")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "No upload preview available." in html
    assert "Preview uploaded data" in html


def test_uploading_csv_for_one_statement_shows_raw_preview():
    csv_file = BytesIO(
        b' Line Item , FY2023 , Empty \n Sales ,"$1,200", \nOperating Income,500, \n , - , \n'
    )
    client = _client()

    response = client.post(
        "/data",
        data={"income_statement": (csv_file, "income.csv")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "income.csv" in html
    assert "3 rows x 3 columns" in html
    assert "$1,200" in html
    assert "Operating Income" in html
    assert "operating income" not in html
    assert "ebit" not in html

    with client.session_transaction() as session:
        upload_id = session.get("current_upload_id")

    assert upload_id
    assert Path("data/temp_uploads", upload_id, "metadata.json").exists()


def test_uploading_xlsx_for_one_statement_shows_raw_preview():
    response = _client().post(
        "/data",
        data={"balance_sheet": (_xlsx_file(), "balance.xlsx")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "balance.xlsx" in html
    assert "2 rows x 2 columns" in html
    assert "Total Assets" in html


def test_unsupported_upload_type_shows_clean_error():
    response = _client().post(
        "/data",
        data={"cash_flow_statement": (BytesIO(b"not supported"), "cash.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "cash.txt" in html
    assert "Unsupported file type. Please upload a CSV or Excel file." in html


def test_clean_data_uses_temporary_upload_and_runs_mechanical_cleaning():
    csv_file = BytesIO(
        b' Sales , Operating Income , Empty \n'
        b'"$1,200","(500)", \n'
        b' , - , \n'
    )
    client = _client()

    upload_response = client.post(
        "/data",
        data={"income_statement": (csv_file, "income.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Cleaned Data Preview" in html
    assert "income.csv" in html
    assert "1 rows x 2 columns" in html
    assert "Mechanical cleaning applied." in html
    assert "Rows dropped" not in html
    assert "Columns dropped" not in html
    assert "Headers normalized" not in html
    assert "Numeric values converted" not in html
    assert "sales" in html
    assert "operating income" in html
    assert "1200" in html
    assert "-500" in html
    assert "revenue" not in html
    assert "ebit" not in html


def test_cleaned_data_with_no_current_upload_shows_empty_state():
    response = _client().get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "No uploaded files are available to clean." in html
    assert "Back to Data" in html
