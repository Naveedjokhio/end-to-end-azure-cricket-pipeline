"""
Streaming consumer that lands events permanently in ADLS.
"""

import argparse
import json
import os
import time
import uuid

from azure.eventhub import EventHubConsumerClient
from azure.storage.blob import BlobServiceClient

RAW_CONTAINER = "raw"
STREAM_PREFIX = "streaming"


def make_on_event(blob_service_client: BlobServiceClient):
    container_client = blob_service_client.get_container_client(RAW_CONTAINER)

    def on_event(partition_context, event):
        if event is None:
            return
        line = event.body_as_str(encoding="UTF-8")
        data = json.loads(line)

        blob_name = f"{STREAM_PREFIX}/over{data.get('over')}_ball{data.get('ball')}_{uuid.uuid4().hex[:8]}.json"
        container_client.upload_blob(name=blob_name, data=line, overwrite=True)

        print(f"landed in ADLS: raw/{blob_name}")
        partition_context.update_checkpoint(event)

    return on_event


def main():
    parser = argparse.ArgumentParser(description="Consume Event Hub events and land them in ADLS raw/streaming")
    parser.add_argument("--eventhub-name", default="cricket-ball-events")
    parser.add_argument("--consumer-group", default="$Default")
    parser.add_argument("--seconds", type=int, default=30)
    args = parser.parse_args()

    eventhub_conn_str = os.environ.get("EVENTHUB_CONNECTION_STR")
    adls_conn_str = os.environ.get("ADLS_CONNECTION_STRING")
    if not eventhub_conn_str:
        raise SystemExit("Set EVENTHUB_CONNECTION_STR environment variable first.")
    if not adls_conn_str:
        raise SystemExit("Set ADLS_CONNECTION_STRING environment variable first.")

    eh_client = EventHubConsumerClient.from_connection_string(
        conn_str=eventhub_conn_str,
        consumer_group=args.consumer_group,
        eventhub_name=args.eventhub_name,
    )
    blob_service_client = BlobServiceClient.from_connection_string(adls_conn_str)

    with eh_client:
        print(f"Listening for {args.seconds}s, landing events in ADLS raw/{STREAM_PREFIX}/ ...")
        eh_client.receive(
            on_event=make_on_event(blob_service_client),
            starting_position="@latest",
        )
        time.sleep(args.seconds)

    print("Done.")


if __name__ == "__main__":
    main()