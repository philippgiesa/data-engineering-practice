import logging
import requests
import pandas

from bs4 import BeautifulSoup
from requests.compat import urljoin
from pathlib import Path

logger = logging.getLogger(__name__)


def soup_get_csv_links(url):
    """Get all links to .csv files from url."""
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        csv_links = []
        for a in soup.select('a[href$=".csv"]'):
            href = a.get("href")
            full_url = urljoin(url, href)
            csv_links.append(full_url)

        logger.info(f"Found {len(csv_links)} links: {csv_links}")

        csv_download_path = Path("downloads/")
        csv_download_path.mkdir(parents=True, exist_ok=True)

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
            
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)



def main():
    logging.basicConfig(level=logging.INFO)
    url = "https://datacatalog.worldbank.org/search/dataset/0038130/gdp-ranking"
    logger.info("test")
    soup_get_csv_links(url=url)

if __name__ == "__main__":
    main()
