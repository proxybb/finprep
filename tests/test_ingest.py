from io import BytesIO, StringIO

import pandas as pd
import pytest

from cleaning.ingest import (
    EmptyUploadedFileError,
    UnreadableUploadedFileError,
    UnsupportedFileTypeError,
    get_file_extension,
    is_supported_file,
    read_uploaded_file,
)


def test_csv_file_can_be_read_into_dataframe():
    file = StringIO("Line Item,2023\nSales,1200\nOperating Income,500\n")

    df = read_uploaded_file(file, filename="income_statement.csv")

    assert list(df.columns) == ["Line Item", "2023"]
    assert df.to_dict("records") == [
        {"Line Item": "Sales", "2023": "1200"},
        {"Line Item": "Operating Income", "2023": "500"},
    ]


def test_xlsx_file_can_be_read_into_dataframe():
    source_df = pd.DataFrame(
        {"Line Item": ["Sales", "Operating Income"], "2023": [1200, 500]}
    )
    file = BytesIO()
    with pd.ExcelWriter(file, engine="openpyxl") as writer:
        source_df.to_excel(writer, index=False)

    df = read_uploaded_file(file, filename="income_statement.xlsx")

    assert list(df.columns) == ["Line Item", "2023"]
    assert df.to_dict("records") == [
        {"Line Item": "Sales", "2023": 1200},
        {"Line Item": "Operating Income", "2023": 500},
    ]


def test_unsupported_file_type_is_rejected():
    with pytest.raises(UnsupportedFileTypeError, match="CSV or Excel"):
        read_uploaded_file(StringIO("Line Item,2023\nSales,1200\n"), filename="data.txt")


def test_extension_detection_is_case_insensitive():
    assert get_file_extension("UPLOAD.CSV") == ".csv"
    assert get_file_extension("Upload.XLSX") == ".xlsx"
    assert get_file_extension("statement.XLS") == ".xls"
    assert is_supported_file("UPLOAD.CSV") is True
    assert is_supported_file("notes.pdf") is False


def test_empty_input_gives_clean_error():
    with pytest.raises(EmptyUploadedFileError, match="empty"):
        read_uploaded_file(StringIO(""), filename="empty.csv")


def test_unreadable_input_gives_clean_error():
    with pytest.raises(UnreadableUploadedFileError, match="could not be read"):
        read_uploaded_file(BytesIO(b"not an excel workbook"), filename="broken.xlsx")


def test_ingestion_does_not_mechanically_clean_or_map_data():
    file = StringIO(' Line Item , 2023 \n Sales ," $1,200 "\nNA, - \n')

    df = read_uploaded_file(file, filename="raw.csv")

    assert list(df.columns) == [" Line Item ", " 2023 "]
    assert df.iloc[0][" Line Item "] == " Sales "
    assert df.iloc[0][" 2023 "] == " $1,200 "
    assert df.iloc[1][" Line Item "] == "NA"
    assert df.iloc[1][" 2023 "] == " - "
    assert "revenue" not in df.to_string().lower()
