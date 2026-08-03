"""
Batch ingestion source: Cricsheet.
Downloads a free, unlimited ball-by-ball match dataset (no API key, no rate
limit) and lands the raw JSON files locally so dltHub can pick them up and
write them to ADLS Raw.

Usage:
    python download_cricsheet.py --competition ipl --out ./data/raw
"""

import argparse
import io
import zipfile
from pathlib import Path

import requests

# Cricsheet zip files are named "<competition>_json.zip"
# See https://cricsheet.org/downloads/ for the full list of competition codes
# (ipl, odis, tests, t20s, bbl, psl, all, etc.)
CRICSHEET_BASE_URL = "https://cricsheet.org/downloads"


def download_competition(competition: str, out_dir: Path) -> list[Path]:
    url = f"{CRICSHEET_BASE_URL}/{competition}_json.zip"
    print(f"Downloading {url} ...")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    out_dir.mkdir(parents=True, exist_ok=True)

    extracted_files = []
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        zf.extractall(out_dir)
        extracted_files = [out_dir / name for name in zf.namelist() if name.endswith(".json")]

    print(f"Extracted {len(extracted_files)} match files to {out_dir}")
    return extracted_files


def main():
    parser = argparse.ArgumentParser(description="Download Cricsheet match data")
    parser.add_argument(
        "--competition",
        default="ipl",
        help="Competition code from https://cricsheet.org/downloads/ (default: ipl)",
    )
    parser.add_argument(
        "--out",
        default="./data/raw",
        help="Local directory to extract JSON match files into",
    )
    args = parser.parse_args()

    download_competition(args.competition, Path(args.out))


if __name__ == "__main__":
    main()
