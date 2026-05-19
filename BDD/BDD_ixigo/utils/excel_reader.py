"""Read Excel data files for data-driven tests."""
import os

try:
    import openpyxl
except ImportError:
    openpyxl = None


def read_excel(filename: str, sheet: str = "Sheet1") -> list[dict]:
    """Read an xlsx file and return a list of dicts (header row → keys)."""
    if openpyxl is None:
        raise ImportError("openpyxl is required: pip install openpyxl")

    filepath = os.path.join(os.path.dirname(__file__), "..", "data", filename)
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb[sheet]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if len(rows) < 2:
        return []

    headers = [str(h).strip() for h in rows[0]]
    return [dict(zip(headers, row)) for row in rows[1:]]
