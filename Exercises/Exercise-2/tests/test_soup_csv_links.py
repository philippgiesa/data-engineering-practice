import pytest
from datetime import datetime
from main import find_csv_links
import requests
from unittest.mock import patch, MagicMock

@patch('requests.Session.get')
def test_find_csv_links_success(mock_get):
    url = "http://test.com/"
    target = datetime(2024, 1, 19, 10, 27)
    html = """
    <tr>
        <td><a href="test.csv">File</a> 2024-01-19 10:27</td>
    </tr>
    """
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp
    
    with requests.Session() as session:
        links = find_csv_links(session, url, target)
        assert len(links) == 1
        assert links[0] == "http://test.com/test.csv"
