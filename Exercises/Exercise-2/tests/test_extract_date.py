import pytest
from datetime import datetime
from main import extract_date

@pytest.mark.parametrize("text, expected", [
    ("Updated: 2024-01-19 10:27", datetime(2024, 1, 19, 10, 27)),
    ("Date is 2026-05-06", datetime(2026, 5, 6)),
    ("Wrong format 2026/05/06", None),
    ("No date here", None),
])
def test_extract_date_variations(text, expected):
    assert extract_date(text) == expected