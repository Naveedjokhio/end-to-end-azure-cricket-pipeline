"""
dltHub batch ingestion pipeline.

Replaces the earlier "az storage blob upload-batch" shortcut with a proper
dlt pipeline: reads local Cricsheet match JSON files as the source, and
loads them into ADLS raw (filesystem destination) as the destination. This
matches the "dltHub" box in the architecture diagram.

Setup (one-time):
    pip install "dlt[filesystem]"

Environment variables needed (same ADLS account as the rest of the project):
    export ADLS_ACCOUNT_NAME="najcricket2026adls"
    export ADLS_ACCOUNT_KEY="<storage account key>"

Usage:
    python dlt_batch_ingestion.py --source ./data/raw
"""

import argparse
import json
from pathlib import Path

import dlt


@dlt.resource(name="cricsheet_matches", write_disposition="replace")
def cricsheet_matches(source_dir: Path):
    """Yield one record per match JSON file found in source_dir."""
    for match_file in sorted(source_dir.glob("*.json")):
        match_json = json.loads(match_file.read_text())
        # tag each record with its source file id so it's traceable downstream
        match_json["_source_file"] = match_file.stem
        yield match_json


def main():
    parser = argparse.ArgumentParser(description="Load Cricsheet match files into ADLS raw via dltHub")
    parser.add_argument("--source", default="./data/raw", help="Local folder of Cricsheet match JSON files")
    parser.add_argument("--bucket-url", default=None, help="Override destination, e.g. az://raw/dlt")
    args = parser.parse_args()

    import os

    account_name = os.environ.get("ADLS_ACCOUNT_NAME")
    account_key = os.environ.get("ADLS_ACCOUNT_KEY")
    if not account_name or not account_key:
        raise SystemExit("Set ADLS_ACCOUNT_NAME and ADLS_ACCOUNT_KEY environment variables first.")

    bucket_url = args.bucket_url or "az://raw/dlt_batch_ingestion"

    pipeline = dlt.pipeline(
        pipeline_name="cricsheet_batch_ingestion",
        destination=dlt.destinations.filesystem(
            bucket_url=bucket_url,
            credentials={
                "azure_storage_account_name": account_name,
                "azure_storage_account_key": account_key,
            },
        ),
        dataset_name="cricsheet",
    )

    load_info = pipeline.run(
        cricsheet_matches(Path(args.source)),
        loader_file_format="jsonl",
    )
    print(load_info)


if __name__ == "__main__":
    main()