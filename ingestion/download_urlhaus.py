import requests
from pathlib import Path


# Configuration

URLHAUS_URL = "https://urlhaus.abuse.ch/downloads/csv_recent/"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"

OUTPUT_FILE = RAW_DIR / "urlhaus.csv"


def download_urlhaus():

    # Create data/raw directory if it doesn't exist
    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("Downloading URLHaus CSV...")

    response = requests.get(
        URLHAUS_URL,
        timeout=30
    )

    response.raise_for_status()

    # Save downloaded file
    OUTPUT_FILE.write_bytes(
        response.content
    )

    print("CSV downloaded successfully!")
    print(f"File location: {OUTPUT_FILE}")


def main():

    download_urlhaus()


if __name__ == "__main__":

    main()