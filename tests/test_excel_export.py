# tests/test_excel_export.py
import io
import pandas as pd
from app import generate_demo, build_excel_bytes


def test_build_excel_contains_expected_sheets():
    df = generate_demo(20)
    b = build_excel_bytes(df, top_n_ips=10)
    assert isinstance(b, (bytes, bytearray))
    xls = pd.ExcelFile(io.BytesIO(b))
    sheets = xls.sheet_names
    expected = {'Raw_Clean','Aggregated_By_SrcIP','Top_Alerts','Summary'}
    assert expected.issubset(set(sheets)), f"Missing sheets: {expected - set(sheets)}"
