import requests
import logging 
import aiohttp
import asyncio

from zipfile import ZipFile
from io import BytesIO
from pathlib import Path

logger = logging.getLogger(__name__)

download_uris = [
    "https://divvy-tripdata.s3.amazonaws.com/Divvy_Trips_2018_Q4.zip",
    "https://divvy-tripdata.s3.amazonaws.com/Divvy_Trips_2019_Q1.zip",
    "https://divvy-tripdata.s3.amazonaws.com/Divvy_Trips_2019_Q2.zip",
    "https://divvy-tripdata.s3.amazonaws.com/Divvy_Trips_2019_Q3.zip",
    "https://divvy-tripdata.s3.amazonaws.com/Divvy_Trips_2019_Q4.zip",
    "https://divvy-tripdata.s3.amazonaws.com/Divvy_Trips_2020_Q1.zip",
    "https://divvy-tripdata.s3.amazonaws.com/Divvy_Trips_2220_Q1.zip",
]

async def download_file(session, semaphore, uri, path):
    """Uses aiohttp to asynchronously download files"""
    try:
        async with semaphore:
            async with session.get(uri) as response:
                if "content-disposition" in response.headers:
                    header = response.headers["content-disposition"]
                    filename = header.split("filename=")[1]
                else:
                    filename = uri.split("/")[-1]
                full_path = path / filename
                if full_path.is_file():
                    logger.info(f"File {filename} already exists. Skipping download.")
                else:
                    with open(full_path, 'wb') as file:
                        while True:
                            chunk = await response.content.read(8192)
                            if not chunk:
                                break
                            file.write(chunk)
                        logger.info(f"Downloaded file {filename}")
    except aiohttp.ClientResponseError as e:
        logger.error(f"HTTP Error {e.status} for {uri}: {e.message}")
    except aiohttp.ClientConnectorError as e: # Specific error for connection issues
        logger.error(f"Connection Error for {uri}: {e}")
    except aiohttp.ClientError as e:
        logger.error(f"Client Error for {uri}: {e}")
    except asyncio.TimeoutError:
        logger.error(f"Request timed out for {uri}")
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"An unexpected error occurred during download of {uri}: {e}")

async def multiple_download(uri_list, path, max_concurrent_downloads=5):
    """Uses asyncio to run download_file."""
    logger.info("Start downloading Zip-Files asynchronously")
    semaphore = asyncio.Semaphore(max_concurrent_downloads) # Create semaphore
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        tasks = [download_file(session, semaphore, uri, path) for uri in uri_list]
        await asyncio.gather(*tasks)
    logger.info("Finished downloading Zip-Files asynchronously")

def unzip(zip_directory, target_directory):
    """Unzip files in directory"""
    for zipfile in zip_directory.glob("*.zip"):
        logger.info(f"Extracting {zipfile}...")
        logger.info(f"Target: {target_directory}")
        with ZipFile(zipfile, 'r') as filezip: # Open the ZIP file in read mode
            for file in filezip.infolist():
                filename = file.filename
                if (target_directory / filename).is_file():
                    logger.info(f"File {filename} already exists at location {target_directory}. Skipping.")
                    continue
                else:
                    logger.info(f"File {file} is extracted to location {target_directory}")
                    filezip.extract(member=filename, path=target_directory)

def main():
    logging.basicConfig(level=logging.INFO)
    
    # create folder downloads if not exists
    zip_download_path = Path("downloads/zip/")
    zip_download_path.mkdir(parents=True, exist_ok=True)

    # http_download(download_uris=download_uris)

    asyncio.run(multiple_download(uri_list=download_uris, path=zip_download_path))

    unzip(zip_directory=zip_download_path,target_directory=zip_download_path.parent)

if __name__ == "__main__":
    main()
