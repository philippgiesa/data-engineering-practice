import logging
import requests
import pandas as pd
import re

from datetime import datetime
from bs4 import BeautifulSoup, NavigableString
from requests.compat import urljoin
from pathlib import Path

logger = logging.getLogger(__name__)


def soup_get_csv_links(url, target_date):
    """Get all links to .csv files from url and last updated on specific date."""

    date_re = re.compile(
            r'('
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'      # 05/06/2026, 5-6-26
            r'|'
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}'       # 2026-05-06
            r'|'
            r'[A-Za-z]+\s+\d{1,2},\s+\d{4}'       # May 6, 2026
            r')',
            re.I
        )
    date_patterns = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        
        csv_links = []
        
        for a in soup.select('a[href$=".csv"]'):
            parent = a.parent

            context_parts = []
            if parent:
                context_parts.append(parent.get_text(" ", strip=True))

            prev_sib = a.previous_sibling
            if isinstance(prev_sib, NavigableString):
                context_parts.append(str(prev_sib).strip())
            elif prev_sib:
                context_parts.append(prev_sib.get_text(" ", strip=True))

            next_sib = a.next_sibling
            if isinstance(next_sib, NavigableString):
                context_parts.append(str(next_sib).strip())
            elif next_sib:
                context_parts.append(next_sib.get_text(" ", strip=True))

            context = " ".join(part for part in context_parts if part).lower()

            m = date_re.search(context)

            if not m:
                continue

            date_text = m.group(1)

            parsed_date = None
            for fmt in date_patterns:
                try:
                    parsed_date = datetime.strptime(date_text, fmt).date()
                    break
                except ValueError:
                    pass
            if parsed_date == target_date:
                csv_links.append(urljoin(url, a["href"]))

        logger.info(f"Found {len(csv_links)} links: {csv_links} with last update on {target_date}")

        csv_download_path = Path("downloads/")
        csv_download_path.mkdir(parents=True, exist_ok=True)

        csv_paths = []
        for link in csv_links:
            filename = link.split("/")[-1]
            resp_csv = requests.get(link, stream=True)
            resp_csv.raise_for_status()
            csv_download_path_full = csv_download_path / filename
            logger.info(csv_download_path_full)
            with open(csv_download_path_full, 'wb') as file:
                for chunk in resp_csv.iter_content(chunk_size=128):
                    file.write(chunk)
            logger.info(f"Downloaded file {filename}")
            csv_paths.append(csv_download_path_full)
        
        return csv_paths

            
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)



def read_clean_csv(csv_paths):
    
    list_of_result_dfs = []
    for csv in csv_paths:
        df = pd.read_csv(csv)
        logger.info(df.head())

        squashed_header = []
        for col in range(df.shape[1]):
            first_4_vals = df.iloc[:4, col].dropna().tolist()  # Get first 4 values in this column
            squashed_header.append('_'.join(str(v) for v in first_4_vals))
        data_rows = df.iloc[4:]

        # Create DataFrame with squashed column names
        clean_df = pd.DataFrame(data_rows.values, columns=squashed_header)
        result_df = clean_df.iloc[:, [1, 3, 4]]
        list_of_result_dfs.append(result_df)
    return list_of_result_dfs


def main():
    logging.basicConfig(level=logging.INFO)
    url = "https://datacatalog.worldbank.org/search/dataset/0038130/gdp-ranking"
    target_date = datetime.strptime("2025-12-15", "%Y-%m-%d").date()
    
    csv_paths = soup_get_csv_links(url=url, target_date=target_date)

    list_of_result_dfs = read_clean_csv(csv_paths=csv_paths)
    df = list_of_result_dfs[0]
    logger.info(df[df.Economy == "China"])

if __name__ == "__main__":
    main()
