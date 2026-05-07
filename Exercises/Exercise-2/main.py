import logging
import requests
import pandas as pd
import re

from datetime import datetime
from bs4 import BeautifulSoup, NavigableString
from requests.compat import urljoin
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Constants moved to module level for clarity and performance
DATE_RE = re.compile(
    r'('
    r'\d{4}[/-]\d{1,2}[/-]\d{1,2}\s+\d{1,2}:\d{2}' # 2024-01-19 10:27
    r'|'
    r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'               # 05/06/2026, 5-6-26
    r'|'
    r'\d{4}[/-]\d{1,2}[/-]\d{1,2}'       # 2026-05-06
    r'|'
    r'[A-Za-z]+\s+\d{1,2},\s+\d{4}'       # May 6, 2026
    r')',
    re.I
)

DATE_PATTERNS = [
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%B %d, %Y",
    "%b %d, %Y",
]

def extract_date(text: str) -> Optional[datetime]:
    """Helper to find and parse a date from a string."""
    m = DATE_RE.search(text)
    if not m:
        return None
    
    date_text = m.group(1)
    for fmt in DATE_PATTERNS:
        try:
            return datetime.strptime(date_text, fmt)
        except ValueError:
            continue
    return None

def find_csv_links(session: requests.Session, url: str, target_date: datetime) -> List[str]:
    """Scrapes the URL for CSV links matching a specific last-modified date."""
    try:
        resp = session.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        csv_links = []
        for a in soup.select('a[href$=".csv"]'):
            context_parts = []
            if a.parent:
                context_parts.append(a.parent.get_text(" ", strip=True))
            
            for sib in [a.previous_sibling, a.next_sibling]:
                if isinstance(sib, NavigableString):
                    context_parts.append(str(sib).strip())
                elif sib:
                    context_parts.append(sib.get_text(" ", strip=True))

            context = " ".join(part for part in context_parts if part).lower()
            parsed_date = extract_date(context)
            
            if parsed_date == target_date:
                csv_links.append(urljoin(url, a["href"]))
        
        return csv_links
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return []

def download_files(session: requests.Session, urls: List[str], download_dir: str) -> List[Path]:
    """Downloads a list of URLs to the specified directory."""
    download_path = Path(download_dir)
    download_path.mkdir(parents=True, exist_ok=True)
    
    local_paths = []
    for link in urls:
        filename = link.split("/")[-1]
        target_file = download_path / filename
        try:
            resp_csv = session.get(link, stream=True)
            resp_csv.raise_for_status()
            
            with open(target_file, 'wb') as f:
                for chunk in resp_csv.iter_content(chunk_size=128):
                    f.write(chunk)
            
            logger.info(f"Downloaded: {target_file}")
            local_paths.append(target_file)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {link}: {e}")
            
    return local_paths

def soup_get_csv_links(url: str, target_date: datetime, download_dir: str = "downloads/") -> List[Path]:
    """
    Orchestrator function find csv links and then download csv files.
    """
    with requests.Session() as session:
        links = find_csv_links(session, url, target_date)
        if not links:
            logger.warning(f"No CSV links found for date {target_date}")
            return []
        return download_files(session, links, download_dir)


def read_clean_csv(csv_paths: List[Path]) -> List[pd.DataFrame]:
    """Reads the csv files and applies some very use-case specific cleaning."""
    list_of_result_dfs = []
    for csv in csv_paths:
        df = pd.read_csv(csv)
        
        # Extract headers from first 4 rows and squash them
        headers = df.iloc[:4]
        squashed_columns = [
            "_".join(headers.iloc[:, i].dropna().astype(str)) 
            for i in range(df.shape[1])
        ]
        
        clean_df = df.iloc[4:].copy()
        clean_df.columns = squashed_columns
        list_of_result_dfs.append(clean_df.iloc[:, [1, 3, 4]])
    return list_of_result_dfs


def main():
    logging.basicConfig(level=logging.INFO)
    url = "https://datacatalog.worldbank.org/search/dataset/0038130/gdp-ranking"
    target_date = datetime.strptime("2025-12-15", "%Y-%m-%d")
    
    csv_paths = soup_get_csv_links(url=url, target_date=target_date)

    list_of_result_dfs = read_clean_csv(csv_paths=csv_paths)
    df = list_of_result_dfs[0]
    logger.info(df[df.Economy == "China"])

if __name__ == "__main__":
    main()
