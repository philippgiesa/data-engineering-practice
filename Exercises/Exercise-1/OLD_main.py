import requests
import logging 

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


def http_download(download_uris):
    """Download and extract zipfiles from http source using requests and zipfile packages."""
    logger.info("Start downloading and extracting Zip-Files")
    
    for uri in download_uris:
        filename_zip = uri.rsplit("/",1)[1]
        directory = Path("downloads/zip")
        full_path = directory / filename_zip

        if full_path.is_file():
            logger.info(f"File already exists. Skipping download.")
        else:
            try:
                logger.info(f"Start download for file from uri {uri}...")
                # get one file
                response = requests.get(uri, stream=True)
                response.raise_for_status()
            
                with open(full_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                logger.info(f"...successfully downloaded file from uri {uri}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error downloading file: {e}")
        
    logger.info("Finished downloading and extracting Zip-Files")


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
    p = Path("downloads/zip/")
    p.mkdir(parents=True, exist_ok=True)

    http_download(download_uris=download_uris)

    unzip(zip_directory=p,target_directory=p.parent)

    




if __name__ == "__main__":
    main()
