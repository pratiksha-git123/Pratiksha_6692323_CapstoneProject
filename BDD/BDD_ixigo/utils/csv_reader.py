"""Read CSV data files for data-driven tests."""
import csv
import os


def read_csv(filename: str) -> list[dict]:
    """Read a CSV file from data/ and return a list of dicts."""
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", filename)
    with open(filepath, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
