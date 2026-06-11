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


def _csv_file(label: bytes = b"Cash") -> BytesIO:
    return BytesIO(
        b"Line Item,2022,2023\n"
        + label
        + b',"$1,000","$1,100"\n'
        + b'Total Assets,"$5,000","$5,500"\n'
    )


def test_existing_routes_return_200():
    client = _client()

    for path in ["/", "/data/upload", "/data/cleaned", "/companies", "/analysis"]:
        response = client.get(path)
        assert response.status_code == 200


def test_data_redirects_to_upload_page():
    response = _client().get("/data")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/data/upload")


def test_data_upload_renders_with_no_files():
    response = _client().get("/data/upload")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Upload and Raw Preview" in html
    assert "No upload preview available." in html
    assert "Upload and preview" in html


def test_uploading_csv_for_one_statement_shows_raw_preview():
    csv_file = BytesIO(
        b' Line Item , FY2023 , Empty \n Sales ,"$1,200", \nOperating Income,500, \n , - , \n'
    )
    client = _client()

    response = client.post(
        "/data/upload",
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
        "/data/upload",
        data={"balance_sheet": (_xlsx_file(), "balance.xlsx")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "balance.xlsx" in html
    assert "2 rows x 2 columns" in html
    assert "Total Assets" in html


def test_uploading_only_balance_sheet_succeeds_and_missing_slots_do_not_error():
    client = _client()

    response = client.post(
        "/data/upload",
        data={"balance_sheet": (_csv_file(), "balance.csv")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "balance.csv" in html
    assert "Balance Sheet raw preview" in html
    assert "2 rows x 3 columns" in html
    assert "$1,000" in html
    assert "Unsupported file type" not in html
    assert "The uploaded file is empty." not in html
    assert "Income Statement raw preview" in html
    assert "Cash Flow Statement raw preview" in html
    assert "No upload preview available." in html


def test_uploading_only_balance_sheet_then_cleaned_preview_succeeds():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"balance_sheet": (_csv_file(), "balance.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Cleaned Data Preview" in html
    assert "balance.csv" in html
    assert "2 rows x 3 columns" in html
    assert "Mechanical cleaning applied." in html
    assert "Balance Sheet cleaned preview" in html
    assert "Income Statement cleaned preview" in html
    assert "No uploaded file for Income Statement." in html
    assert "No uploaded file for Cash Flow Statement." in html
    assert "1000" in html
    assert "$1,000" not in html


def test_uploading_only_cash_flow_statement_succeeds():
    response = _client().post(
        "/data/upload",
        data={"cash_flow_statement": (_csv_file(b"Operating Cash Flow"), "cash-flow.csv")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "cash-flow.csv" in html
    assert "Cash Flow Statement raw preview" in html
    assert "Operating Cash Flow" in html
    assert "Unsupported file type" not in html


def test_upload_with_no_files_leaves_no_upload_state():
    client = _client()

    response = client.post(
        "/data/upload",
        data={},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Upload and Raw Preview" in html
    assert "No upload preview available." in html
    assert "Unsupported file type" not in html
    with client.session_transaction() as session:
        assert session.get("current_upload_id") is None


def test_uploading_all_three_statements_still_shows_raw_previews():
    response = _client().post(
        "/data/upload",
        data={
            "income_statement": (_csv_file(b"Revenue"), "income.csv"),
            "balance_sheet": (_csv_file(b"Cash"), "balance.csv"),
            "cash_flow_statement": (_csv_file(b"Operating Cash Flow"), "cash-flow.csv"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "income.csv" in html
    assert "balance.csv" in html
    assert "cash-flow.csv" in html
    assert html.count("2 rows x 3 columns") == 3
    assert "Unsupported file type" not in html


def test_unsupported_upload_type_shows_clean_error():
    response = _client().post(
        "/data/upload",
        data={"cash_flow_statement": (BytesIO(b"not supported"), "cash.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "cash.txt" in html
    assert "Unsupported file type. Please upload a CSV or Excel file." in html


def test_one_valid_file_with_unsupported_file_errors_only_uploaded_bad_slot():
    response = _client().post(
        "/data/upload",
        data={
            "balance_sheet": (_csv_file(), "balance.csv"),
            "cash_flow_statement": (BytesIO(b"not supported"), "cash.txt"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "balance.csv" in html
    assert "cash.txt" in html
    assert "Unsupported file type. Please upload a CSV or Excel file." in html
    assert "No upload preview available." in html


def test_clean_data_uses_temporary_upload_and_runs_mechanical_cleaning():
    csv_file = BytesIO(
        b' Sales , Operating Income , Empty \n'
        b'"$1,200","(500)", \n'
        b' , - , \n'
    )
    client = _client()

    upload_response = client.post(
        "/data/upload",
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
    assert "Orientation uncertain; table left unchanged." in html
    assert "Rows dropped" not in html
    assert "Columns dropped" not in html
    assert "Headers normalized" not in html
    assert "Numeric values converted" not in html
    assert "<th></th>" in html
    assert "operating income" in html
    assert "1200" in html
    assert "-500" in html
    assert "revenue" not in html
    assert "ebit" not in html


def test_clean_data_normalizes_sideways_upload_orientation():
    csv_file = BytesIO(
        b" Year , Sales , Operating Income \n"
        b'2021,"$1,200","$500"\n'
        b'2022,"$1,400","$650"\n'
    )
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"income_statement": (csv_file, "sideways.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200
    raw_html = upload_response.get_data(as_text=True)
    assert "$1,200" in raw_html
    assert "Operating Income" in raw_html
    assert "operating income" not in raw_html

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "sideways.csv" in html
    assert "2 rows x 3 columns" in html
    assert "Mechanical cleaning applied." in html
    assert "Orientation normalized." in html
    assert "<th></th>" in html
    assert "line_item" not in html
    assert "2021" in html
    assert "2022" in html
    assert "sales" in html
    assert "operating income" in html
    assert "1200" in html
    assert "revenue" not in html
    assert "ebit" not in html


def test_clean_data_removes_leading_metadata_and_keeps_first_header_blank():
    csv_file = BytesIO(
        b"Company: DemoCo,,,,,extra header row that should eventually be ignored\n"
        b"Title: Balance Sheet,,,,,\n"
        b"Statement: Income Statement,,,,,\n"
        b"Currency: USD,,,,,\n"
        b"Units: USD millions,,,,,\n"
        b"Year,Sales,Operating Income,Notes,Extra Blank Col\n"
        b'As of 2021,"$1,200","$500","management comment","ignore me"\n'
        b'As of 2022,"$1,400",,"follow up","ignore me"\n'
    )
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"income_statement": (csv_file, "metadata-sideways.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200
    raw_html = upload_response.get_data(as_text=True)
    assert "Company: DemoCo" in raw_html
    assert "extra header row that should eventually be ignored" in raw_html
    assert "Title: Balance Sheet" in raw_html
    assert "Statement: Income Statement" in raw_html
    assert "Currency: USD" in raw_html
    assert "Units: USD millions" in raw_html
    assert "Notes" in raw_html
    assert "Extra Blank Col" in raw_html
    assert "management comment" in raw_html
    assert "As of 2021" in raw_html
    assert "Operating Income" in raw_html
    assert "$1,200" in raw_html

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "metadata-sideways.csv" in html
    assert "2 rows x 3 columns" in html
    assert "Mechanical cleaning applied." in html
    assert "Orientation normalized." in html
    assert "<th></th>" in html
    assert "DemoCo" not in html
    assert "2021" in html
    assert "2022" in html
    assert "Company: DemoCo" not in html
    assert "company: democo" not in html.lower()
    assert "extra header row that should eventually be ignored" not in html
    assert "title: balance sheet" not in html.lower()
    assert "statement: income statement" not in html.lower()
    assert "currency: usd" not in html.lower()
    assert "units: usd millions" not in html.lower()
    assert "notes" not in html.lower()
    assert "extra blank col" not in html.lower()
    assert "management comment" not in html
    assert "as of 2021" not in html.lower()
    assert "line_item" not in html
    assert "data-table__cell--missing" in html
    assert "sales" in html
    assert "operating income" in html
    assert "1200" in html
    assert "revenue" not in html
    assert "ebit" not in html


def test_cleaned_data_with_no_current_upload_shows_empty_state():
    response = _client().get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "No uploaded files are available to clean." in html
    assert "Back to upload/raw preview" in html
