import json
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


def _balance_sheet_mapping_csv() -> BytesIO:
    return BytesIO(
        b"Line Item,2022,2023\n"
        b'Total Assets,"$5,000","$5,500"\n'
        b'Total Liabilities,"$3,000","$3,300"\n'
        b'Total Equity,"$2,000","$2,200"\n'
    )


def _balance_sheet_display_csv() -> BytesIO:
    return BytesIO(
        b"Line Item,2022,2023\n"
        b'Cash and Cash Equivalents,"$1,000","$1,100"\n'
        b'Property Plant and Equipment,"$2,500","$2,700"\n'
        b'Total Assets,"$5,000","$5,500"\n'
        b'Total Liabilities,"$3,000","$3,300"\n'
        b'Total Equity,"$2,000","$2,200"\n'
    )


def _balance_sheet_missing_equity_csv() -> BytesIO:
    return BytesIO(
        b"Line Item,2022,2023\n"
        b'Total Assets,"$5,000","$5,500"\n'
        b'Total Liabilities,"$3,000","$3,300"\n'
        b'Inventory,"$700","$750"\n'
    )


def _balance_sheet_failing_identity_csv() -> BytesIO:
    return BytesIO(
        b"Line Item,2023\n"
        b'Total Assets,"$1,000"\n'
        b'Total Liabilities,"$400"\n'
        b'Total Equity,"$500"\n'
    )


def _balance_sheet_missing_equity_single_period_csv() -> BytesIO:
    return BytesIO(
        b"Line Item,2023\n"
        b'Total Assets,"$1,000"\n'
        b'Total Liabilities,"$400"\n'
    )


def _balance_sheet_stockholders_equity_csv(equity_value: int = 600) -> BytesIO:
    return BytesIO(
        (
            "Line Item,2023\n"
            'Total Assets,"$1,000"\n'
            'Total Liabilities,"$400"\n'
            f'Stockholders Equity,"${equity_value}"\n'
        ).encode("utf-8")
    )


def _extract_expandable_table_card(html: str, filename: str) -> str:
    filename_index = html.index(filename)
    start = html.rfind('<article class="table-card table-card--embedded" data-expandable-card>', 0, filename_index)
    assert start != -1
    end = html.index("</article>", filename_index) + len("</article>")
    return html[start:end]


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
    assert "Clear uploaded data" in html


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
    table_card = _extract_expandable_table_card(html, "balance.csv")
    assert "canonical_label" not in table_card
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


def test_clear_uploaded_data_removes_single_balance_sheet_upload():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"balance_sheet": (_balance_sheet_mapping_csv(), "balance-clear.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200
    assert "balance-clear.csv" in upload_response.get_data(as_text=True)

    with client.session_transaction() as session:
        upload_id = session.get("current_upload_id")
    upload_dir = Path("data/temp_uploads", upload_id)
    assert upload_dir.exists()
    assert (upload_dir / "metadata.json").exists()

    clear_response = client.post("/data/clear")

    assert clear_response.status_code == 302
    assert clear_response.headers["Location"].endswith("/data")
    assert not upload_dir.exists()
    with client.session_transaction() as session:
        assert session.get("current_upload_id") is None

    response = client.get("/data", follow_redirects=True)

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "balance-clear.csv" not in html
    assert "Total Assets" not in html
    assert "No upload preview available." in html


def test_clear_uploaded_data_removes_all_three_statement_previews():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={
            "income_statement": (_csv_file(b"Revenue"), "income-clear.csv"),
            "balance_sheet": (_balance_sheet_mapping_csv(), "balance-clear.csv"),
            "cash_flow_statement": (_csv_file(b"Operating Cash Flow"), "cash-clear.csv"),
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200
    html = upload_response.get_data(as_text=True)
    assert "income-clear.csv" in html
    assert "balance-clear.csv" in html
    assert "cash-clear.csv" in html

    with client.session_transaction() as session:
        upload_id = session.get("current_upload_id")
    upload_dir = Path("data/temp_uploads", upload_id)
    assert upload_dir.exists()

    clear_response = client.post("/data/clear")

    assert clear_response.status_code == 302
    assert not upload_dir.exists()

    response = client.get("/data/upload")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "income-clear.csv" not in html
    assert "balance-clear.csv" not in html
    assert "cash-clear.csv" not in html
    assert html.count("No upload preview available.") == 3


def test_cleaned_data_after_clear_shows_no_upload_state():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"balance_sheet": (_balance_sheet_mapping_csv(), "balance-cleaned-clear.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    cleaned_before_clear = client.get("/data/cleaned")
    assert cleaned_before_clear.status_code == 200
    assert "balance-cleaned-clear.csv" in cleaned_before_clear.get_data(as_text=True)
    assert "Balance Sheet identity check passed." in cleaned_before_clear.get_data(as_text=True)

    clear_response = client.post("/data/clear")
    assert clear_response.status_code == 302

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "No uploaded files are available to clean." in html
    assert "balance-cleaned-clear.csv" not in html
    assert "Balance Sheet identity check passed." not in html
    assert "total_assets" not in html


def test_clear_uploaded_data_is_safe_with_no_upload():
    client = _client()

    response = client.post("/data/clear")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/data")
    with client.session_transaction() as session:
        assert session.get("current_upload_id") is None

    upload_page = client.get("/data/upload")
    assert upload_page.status_code == 200
    assert "No upload preview available." in upload_page.get_data(as_text=True)


def test_new_upload_works_after_clear():
    client = _client()

    first_upload = client.post(
        "/data/upload",
        data={"balance_sheet": (_balance_sheet_mapping_csv(), "old-balance.csv")},
        content_type="multipart/form-data",
    )
    assert first_upload.status_code == 200
    assert "old-balance.csv" in first_upload.get_data(as_text=True)

    clear_response = client.post("/data/clear")
    assert clear_response.status_code == 302

    second_upload = client.post(
        "/data/upload",
        data={"balance_sheet": (_balance_sheet_mapping_csv(), "new-balance.csv")},
        content_type="multipart/form-data",
    )

    assert second_upload.status_code == 200
    html = second_upload.get_data(as_text=True)
    assert "new-balance.csv" in html
    assert "old-balance.csv" not in html
    assert "Total Assets" in html


def test_clear_uploaded_data_does_not_touch_old_engine_files():
    old_engine_path = Path("old_engine_files")
    before_exists = old_engine_path.exists()
    before_mtime = old_engine_path.stat().st_mtime if before_exists else None

    response = _client().post("/data/clear")

    assert response.status_code == 302
    assert old_engine_path.exists() is before_exists
    if before_exists:
        assert old_engine_path.stat().st_mtime == before_mtime


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
    assert "canonical_label" not in html
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
    assert "Revenue" in html
    assert "Operating Profit" in html
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
    assert "Revenue" in html
    assert "Operating Profit" in html
    assert "1200" in html
    assert "revenue" not in html
    assert "ebit" not in html


def test_balance_sheet_cleaned_preview_hides_mapping_metadata_and_uses_display_labels():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"balance_sheet": (_balance_sheet_display_csv(), "balance-map.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "balance-map.csv" in html
    assert "5 rows x 3 columns" in html
    for metadata_header in [
        "canonical_label",
        "mapping_status",
        "original_label",
        "normalized_label",
        "review_reason",
        "concept_category",
        "concept_family",
        "rollup_role",
        "CANONICAL_LABEL",
        "MAPPING_STATUS",
        "ORIGINAL_LABEL",
        "NORMALIZED_LABEL",
        "REVIEW_REASON",
        "CONCEPT_CATEGORY",
        "CONCEPT_FAMILY",
        "ROLLUP_ROLE",
    ]:
        assert metadata_header not in html
    assert "Total Assets" in html
    assert "Total Liabilities" in html
    assert "Total Equity" in html
    assert "Cash and Cash Equivalents" in html
    assert "PP&amp;E" in html
    assert "total_assets" not in html
    assert "total_liabilities" not in html
    assert "total_equity" not in html
    assert "cash_and_equivalents" not in html
    assert "Balance Sheet is ready for identity validation." in html
    assert "Balance Sheet identity check passed." in html
    assert "5000" in html
    assert "5500" in html
    assert "3000" in html
    assert "3300" in html
    assert "2000" in html
    assert "2200" in html
    table_card = _extract_expandable_table_card(html, "balance-map.csv")
    for metadata_header in [
        "canonical_label",
        "mapping_status",
        "original_label",
        "normalized_label",
        "review_reason",
        "concept_category",
        "concept_family",
        "rollup_role",
    ]:
        assert metadata_header not in table_card


def test_balance_sheet_validation_status_renders_outside_expandable_cleaned_table():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"balance_sheet": (_balance_sheet_mapping_csv(), "balance-status-outside.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    status_index = html.index('data-cleaned-status-panel')
    schema_index = html.index("Balance Sheet is ready for identity validation.")
    identity_index = html.index("Balance Sheet identity check passed.")
    table_card_start = html.index(
        '<article class="table-card table-card--embedded" data-expandable-card>',
        status_index,
    )
    assert status_index < schema_index < table_card_start
    assert status_index < identity_index < table_card_start

    table_card = _extract_expandable_table_card(html, "balance-status-outside.csv")
    assert 'data-expand-button aria-expanded="false">Expand</button>' in table_card
    assert '<div class="table-wrap table-wrap--compact">' in table_card
    assert "validation-panel" not in table_card
    assert "cleaning-status" not in table_card
    assert "Balance Sheet is ready for identity validation." not in table_card
    assert "Balance Sheet identity check passed." not in table_card


def test_balance_sheet_raw_preview_remains_unmapped():
    response = _client().post(
        "/data/upload",
        data={"balance_sheet": (_balance_sheet_mapping_csv(), "balance-raw.csv")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "balance-raw.csv" in html
    assert "3 rows x 3 columns" in html
    assert "Total Assets" in html
    assert "Total Liabilities" in html
    assert "Total Equity" in html
    assert "$5,000" in html
    assert "canonical_label" not in html
    assert "total_assets" not in html
    assert "total_liabilities" not in html
    assert "total_equity" not in html


def test_only_income_statement_cleaned_preview_does_not_run_mapping():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"income_statement": (_csv_file(b"Revenue"), "income-only.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "income-only.csv" in html
    assert "2 rows x 3 columns" in html
    assert "canonical_label" not in html
    assert "total_assets" not in html
    assert "total_liabilities" not in html
    assert "total_equity" not in html
    table_card = _extract_expandable_table_card(html, "income-only.csv")
    assert "Income Statement cleaned preview" in table_card
    assert '<div class="table-wrap table-wrap--compact">' in table_card
    assert "validation-panel" not in table_card


def test_only_cash_flow_cleaned_preview_does_not_run_mapping():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"cash_flow_statement": (_csv_file(b"Operating Cash Flow"), "cash-only.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "cash-only.csv" in html
    assert "2 rows x 3 columns" in html
    assert "canonical_label" not in html
    assert "total_assets" not in html
    assert "total_liabilities" not in html
    assert "total_equity" not in html
    table_card = _extract_expandable_table_card(html, "cash-only.csv")
    assert "Cash Flow Statement cleaned preview" in table_card
    assert '<div class="table-wrap table-wrap--compact">' in table_card
    assert "validation-panel" not in table_card


def test_three_statement_cleaned_preview_still_works_with_balance_sheet_mapping():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={
            "income_statement": (_csv_file(b"Revenue"), "income.csv"),
            "balance_sheet": (_balance_sheet_mapping_csv(), "balance.csv"),
            "cash_flow_statement": (_csv_file(b"Operating Cash Flow"), "cash-flow.csv"),
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "income.csv" in html
    assert "balance.csv" in html
    assert "cash-flow.csv" in html
    assert "Total Assets" in html
    assert "Total Liabilities" in html
    assert "Total Equity" in html
    assert "Income Statement cleaned preview" in _extract_expandable_table_card(html, "income.csv")
    assert "Balance Sheet cleaned preview" in _extract_expandable_table_card(html, "balance.csv")
    assert "Cash Flow Statement cleaned preview" in _extract_expandable_table_card(html, "cash-flow.csv")


def test_balance_sheet_mapping_error_shows_clean_error(monkeypatch):
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"balance_sheet": (_balance_sheet_mapping_csv(), "balance-error.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    def fail_mapping(_df, _statement_type):
        raise ValueError("Mapping failed cleanly.")

    monkeypatch.setattr("web.routes.map_statement_rows", fail_mapping)

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "balance-error.csv" in html
    assert "cleaning unavailable" in html
    assert "Mapping failed cleanly." in html


def test_balance_sheet_cleaned_preview_shows_missing_required_schema_status():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"balance_sheet": (_balance_sheet_missing_equity_csv(), "balance-missing.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "balance-missing.csv" in html
    assert "Balance Sheet is not ready for identity validation." in html
    assert "Missing required fields" in html
    assert "total_equity" in html
    assert "Required-field override" in html
    assert 'action="/data/review/override"' in html
    assert 'name="canonical_label" value="total_equity"' in html
    assert 'name="period_0" value="2022"' in html
    assert 'name="period_1" value="2023"' in html
    assert "Apply override" in html
    assert (
        "Identity check cannot run until required fields are mapped, approved, or overridden."
        in html
    )
    assert "Identity check skipped." in html
    assert "missing required fields: total_equity" in html
    assert "Total Assets" in html
    assert "Total Liabilities" in html
    assert "Inventory" in html
    assert "5500" in html
    assert "3300" in html


def test_balance_sheet_cleaned_preview_shows_passing_identity_status():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"balance_sheet": (_balance_sheet_mapping_csv(), "balance-pass.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "balance-pass.csv" in html
    assert "Balance Sheet is ready for identity validation." in html
    assert "Balance Sheet identity check passed." in html
    assert "Assets equal Liabilities + Equity for all checked periods." in html
    assert "Balance Sheet identity check failed." not in html
    table_card = _extract_expandable_table_card(html, "balance-pass.csv")
    assert "validation-panel" not in table_card
    assert "Balance Sheet identity check passed." not in table_card


def test_balance_sheet_cleaned_preview_shows_skipped_identity_status():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"balance_sheet": (_balance_sheet_missing_equity_csv(), "balance-skip.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "balance-skip.csv" in html
    assert "Identity check skipped." in html
    assert "missing required fields: total_equity" in html
    table_card = _extract_expandable_table_card(html, "balance-skip.csv")
    assert "validation-panel" not in table_card
    assert "Identity check skipped." not in table_card
    assert "missing required fields: total_equity" not in table_card


def test_submitting_balance_sheet_override_reruns_schema_and_passing_identity():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={
            "balance_sheet": (
                _balance_sheet_missing_equity_single_period_csv(),
                "override-pass.csv",
            )
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200
    assert "Apply override" in client.get("/data/cleaned").get_data(as_text=True)

    with client.session_transaction() as session:
        upload_id = session.get("current_upload_id")

    override_response = client.post(
        "/data/review/override",
        data={
            "statement_type": "balance_sheet",
            "canonical_label": "total_equity",
            "period_count": "1",
            "period_0": "2023",
            "value_0": "600",
        },
    )

    assert override_response.status_code == 302
    assert override_response.headers["Location"].endswith("/data/cleaned")
    metadata = json.loads(
        Path("data/temp_uploads", upload_id, "metadata.json").read_text(
            encoding="utf-8"
        )
    )
    assert metadata["overrides"]["balance_sheet"] == [
        {
            "canonical_label": "total_equity",
            "reason": "User-entered required-field override",
            "values": {"2023": 600},
        }
    ]

    response = client.get("/data/cleaned")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "override-pass.csv" in html
    assert "Balance Sheet is ready for identity validation." in html
    assert "Balance Sheet identity check passed." in html
    assert "Total Equity" in html
    assert "Apply override" not in html
    assert "user_override" not in html
    assert "User override: Total Equity" not in html


def test_submitting_balance_sheet_override_can_fail_identity():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={
            "balance_sheet": (
                _balance_sheet_missing_equity_single_period_csv(),
                "override-fail.csv",
            )
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    override_response = client.post(
        "/data/review/override",
        data={
            "statement_type": "balance_sheet",
            "canonical_label": "total_equity",
            "period_count": "1",
            "period_0": "2023",
            "value_0": "500",
        },
    )

    assert override_response.status_code == 302

    response = client.get("/data/cleaned")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "override-fail.csv" in html
    assert "Balance Sheet is ready for identity validation." in html
    assert "Balance Sheet identity check failed." in html
    assert "1,000" in html
    assert "400" in html
    assert "500" in html
    assert "900" in html
    assert "100" in html
    assert "Fail" in html


def test_balance_sheet_override_invalid_canonical_label_does_not_alter_results():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={
            "balance_sheet": (
                _balance_sheet_missing_equity_single_period_csv(),
                "override-invalid.csv",
            )
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    with client.session_transaction() as session:
        upload_id = session.get("current_upload_id")

    override_response = client.post(
        "/data/review/override",
        data={
            "statement_type": "balance_sheet",
            "canonical_label": "revenue",
            "period_count": "1",
            "period_0": "2023",
            "value_0": "600",
        },
    )

    assert override_response.status_code == 302
    metadata = (Path("data/temp_uploads", upload_id, "metadata.json")).read_text(
        encoding="utf-8"
    )
    assert "overrides" not in metadata

    html = client.get("/data/cleaned").get_data(as_text=True)
    assert "override-invalid.csv" in html
    assert "Balance Sheet is not ready for identity validation." in html
    assert "Identity check skipped." in html
    assert "missing required fields: total_equity" in html


def test_balance_sheet_auto_mapped_required_field_hides_override_input():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"balance_sheet": (_balance_sheet_mapping_csv(), "no-override.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "no-override.csv" in html
    assert "Balance Sheet is ready for identity validation." in html
    assert "Required-field override" not in html
    assert 'action="/data/review/override"' not in html
    assert 'name="canonical_label" value="total_equity"' not in html


def test_balance_sheet_cleaned_preview_shows_failing_identity_status():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"balance_sheet": (_balance_sheet_failing_identity_csv(), "balance-fail.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "balance-fail.csv" in html
    assert "Balance Sheet is ready for identity validation." in html
    assert "Balance Sheet identity check failed." in html
    assert "2023" in html
    assert "1,000" in html
    assert "400" in html
    assert "500" in html
    assert "900" in html
    assert "100" in html
    assert "Fail" in html
    identity_detail_index = html.index("identity-detail-table")
    table_card_start = html.index(
        '<article class="table-card table-card--embedded" data-expandable-card>',
        identity_detail_index,
    )
    assert identity_detail_index < table_card_start
    table_card = _extract_expandable_table_card(html, "balance-fail.csv")
    assert "validation-panel" not in table_card
    assert "identity-detail-table" not in table_card
    assert "Balance Sheet identity check failed." not in table_card


def test_balance_sheet_review_panel_shows_required_field_candidate():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={
            "balance_sheet": (
                _balance_sheet_stockholders_equity_csv(),
                "stockholders.csv",
            )
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "stockholders.csv" in html
    assert "Balance Sheet is not ready for identity validation." in html
    assert "Missing required fields" in html
    assert "total_equity" in html
    assert "Suggested review" in html
    assert "Stockholders Equity may be approved as Total Equity." in html
    assert "Owner-only equity may exclude non-controlling interests." in html
    assert "Approve as Total Equity" in html
    assert "Apply override" in html
    assert (
        "Identity check cannot run until required fields are mapped, approved, or overridden."
        in html
    )
    assert 'name="row_position" value="2"' in html
    review_index = html.index("review-candidate")
    table_card_start = html.index(
        '<article class="table-card table-card--embedded" data-expandable-card>',
        review_index,
    )
    assert review_index < table_card_start
    table_card = _extract_expandable_table_card(html, "stockholders.csv")
    assert "review-candidate" not in table_card
    assert "Approve as Total Equity" not in table_card


def test_approving_stockholders_equity_reruns_schema_and_identity():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={
            "balance_sheet": (
                _balance_sheet_stockholders_equity_csv(),
                "stockholders-pass.csv",
            )
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    approve_response = client.post(
        "/data/review/approve",
        data={
            "statement_type": "balance_sheet",
            "row_position": "2",
            "canonical_label": "total_equity",
        },
    )

    assert approve_response.status_code == 302
    assert approve_response.headers["Location"].endswith("/data/cleaned")

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "stockholders-pass.csv" in html
    assert "Balance Sheet is ready for identity validation." in html
    assert "Balance Sheet identity check passed." in html
    assert "Approve as Total Equity" not in html
    assert "Total Equity" in html
    assert "total_equity" not in html
    table_card = _extract_expandable_table_card(html, "stockholders-pass.csv")
    assert "validation-panel" not in table_card
    assert "Balance Sheet identity check passed." not in table_card


def test_approved_stockholders_equity_can_fail_identity():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={
            "balance_sheet": (
                _balance_sheet_stockholders_equity_csv(equity_value=500),
                "stockholders-fail.csv",
            )
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    approve_response = client.post(
        "/data/review/approve",
        data={
            "statement_type": "balance_sheet",
            "row_position": "2",
            "canonical_label": "total_equity",
        },
    )
    assert approve_response.status_code == 302

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "stockholders-fail.csv" in html
    assert "Balance Sheet is ready for identity validation." in html
    assert "Balance Sheet identity check failed." in html


def test_approval_route_is_safe_without_upload():
    response = _client().post(
        "/data/review/approve",
        data={
            "statement_type": "balance_sheet",
            "row_position": "2",
            "canonical_label": "total_equity",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/data/cleaned")


def test_approval_route_ignores_invalid_row_position():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={
            "balance_sheet": (
                _balance_sheet_stockholders_equity_csv(),
                "stockholders-invalid.csv",
            )
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    approve_response = client.post(
        "/data/review/approve",
        data={
            "statement_type": "balance_sheet",
            "row_position": "99",
            "canonical_label": "total_equity",
        },
    )
    assert approve_response.status_code == 302

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Balance Sheet is not ready for identity validation." in html
    assert "Identity check skipped." in html
    assert "missing required fields: total_equity" in html
    assert "Approve as Total Equity" in html


def test_approval_route_does_not_affect_income_or_cash_flow():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={
            "income_statement": (_csv_file(b"Revenue"), "income-review.csv"),
            "cash_flow_statement": (_csv_file(b"Operating Cash Flow"), "cash-review.csv"),
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    approve_response = client.post(
        "/data/review/approve",
        data={
            "statement_type": "balance_sheet",
            "row_position": "2",
            "canonical_label": "total_equity",
        },
    )
    assert approve_response.status_code == 302

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "income-review.csv" in html
    assert "cash-review.csv" in html
    assert "canonical_label" not in html
    assert "total_equity" not in html


def test_override_route_does_not_affect_income_or_cash_flow():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={
            "income_statement": (_csv_file(b"Revenue"), "income-override.csv"),
            "cash_flow_statement": (_csv_file(b"Operating Cash Flow"), "cash-override.csv"),
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    override_response = client.post(
        "/data/review/override",
        data={
            "statement_type": "balance_sheet",
            "canonical_label": "total_equity",
            "period_count": "1",
            "period_0": "2023",
            "value_0": "600",
        },
    )
    assert override_response.status_code == 302

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "income-override.csv" in html
    assert "cash-override.csv" in html
    assert "canonical_label" not in html
    assert "user_override" not in html
    assert "total_equity" not in html


def test_clear_uploaded_data_clears_approval_state():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={
            "balance_sheet": (
                _balance_sheet_stockholders_equity_csv(),
                "approved-before-clear.csv",
            )
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    approve_response = client.post(
        "/data/review/approve",
        data={
            "statement_type": "balance_sheet",
            "row_position": "2",
            "canonical_label": "total_equity",
        },
    )
    assert approve_response.status_code == 302
    assert "Balance Sheet identity check passed." in client.get("/data/cleaned").get_data(as_text=True)

    clear_response = client.post("/data/clear")
    assert clear_response.status_code == 302

    new_upload_response = client.post(
        "/data/upload",
        data={
            "balance_sheet": (
                _balance_sheet_stockholders_equity_csv(),
                "approved-after-clear.csv",
            )
        },
        content_type="multipart/form-data",
    )
    assert new_upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "approved-after-clear.csv" in html
    assert "Balance Sheet is not ready for identity validation." in html
    assert "Approve as Total Equity" in html


def test_clear_uploaded_data_clears_override_state():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={
            "balance_sheet": (
                _balance_sheet_missing_equity_single_period_csv(),
                "override-before-clear.csv",
            )
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    override_response = client.post(
        "/data/review/override",
        data={
            "statement_type": "balance_sheet",
            "canonical_label": "total_equity",
            "period_count": "1",
            "period_0": "2023",
            "value_0": "600",
        },
    )
    assert override_response.status_code == 302
    assert "Balance Sheet identity check passed." in client.get("/data/cleaned").get_data(as_text=True)

    clear_response = client.post("/data/clear")
    assert clear_response.status_code == 302

    new_upload_response = client.post(
        "/data/upload",
        data={
            "balance_sheet": (
                _balance_sheet_missing_equity_single_period_csv(),
                "override-after-clear.csv",
            )
        },
        content_type="multipart/form-data",
    )
    assert new_upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "override-after-clear.csv" in html
    assert "Balance Sheet is not ready for identity validation." in html
    assert "Balance Sheet identity check passed." not in html
    assert "Apply override" in html


def test_cleaned_data_with_no_current_upload_shows_empty_state():
    response = _client().get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "No uploaded files are available to clean." in html
    assert "Back to upload/raw preview" in html


# === Income Statement route wiring tests ===


def _income_statement_mapping_csv() -> BytesIO:
    return BytesIO(
        b"Line Item,2022,2023\n"
        b"Turnover,1000,1100\n"
        b"Cost of Sales,-400,-440\n"
        b"Gross Profit,600,660\n"
        b"Net Income,200,220\n"
    )


def _income_statement_negative_values_csv() -> BytesIO:
    return BytesIO(
        b"Line Item,2022,2023\n"
        b"Revenue,1000,1100\n"
        b"Cost of Sales,-400,-440\n"
        b"Net Income,200,220\n"
    )


def test_income_statement_cleaned_preview_applies_is_mapping():
    client = _client()

    upload_response = client.post(
        "/data/upload",
        data={"income_statement": (_income_statement_mapping_csv(), "income-mapped.csv")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "income-mapped.csv" in html
    assert "Cleaned Data Preview" in html
    assert "Income Statement cleaned preview" in html
    assert "4 rows x 3 columns" in html


def test_income_statement_cleaned_preview_hides_mapping_metadata_columns():
    client = _client()

    client.post(
        "/data/upload",
        data={"income_statement": (_income_statement_mapping_csv(), "income-meta.csv")},
        content_type="multipart/form-data",
    )

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    table_card = _extract_expandable_table_card(html, "income-meta.csv")
    for col in [
        "canonical_label",
        "mapping_status",
        "normalized_label",
        "original_label",
        "matched_alias",
        "matched_rule_kind",
        "concept_category",
        "concept_family",
        "rollup_role",
        "review_reason",
        "includes_restricted_cash",
        "template_operator",
        "row_type",
    ]:
        assert col not in table_card, f"Metadata column leaked into display: {col}"


def test_income_statement_cleaned_preview_shows_display_labels_not_canonical():
    client = _client()

    client.post(
        "/data/upload",
        data={"income_statement": (_income_statement_mapping_csv(), "income-labels.csv")},
        content_type="multipart/form-data",
    )

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    table_card = _extract_expandable_table_card(html, "income-labels.csv")
    assert "Revenue" in table_card
    assert "Turnover" not in table_card
    assert "revenue" not in table_card
    assert "Cost of Sales" in table_card
    assert "Gross Profit" in table_card
    assert "Net Income" in table_card


def test_income_statement_cleaned_preview_preserves_period_values_and_signs():
    client = _client()

    client.post(
        "/data/upload",
        data={
            "income_statement": (_income_statement_negative_values_csv(), "income-values.csv")
        },
        content_type="multipart/form-data",
    )

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "1000" in html
    assert "1100" in html
    assert "-400" in html
    assert "-440" in html
    assert "200" in html
    assert "220" in html


def test_balance_sheet_cleaned_preview_behavior_not_changed_by_is_wiring():
    client = _client()

    client.post(
        "/data/upload",
        data={
            "income_statement": (_income_statement_mapping_csv(), "income-both.csv"),
            "balance_sheet": (_balance_sheet_mapping_csv(), "balance-both.csv"),
        },
        content_type="multipart/form-data",
    )

    response = client.get("/data/cleaned")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "income-both.csv" in html
    assert "balance-both.csv" in html
    assert "Revenue" in html
    assert "canonical_label" not in html
