"""
Quick consumer to make the simulated streaming data visible.

This is a throwaway/debug consumer -- it reads whatever events are currently
sitting in the Event Hub and writes each one as a line of JSON into a local
file, so you can see the streaming leg actually produced something, without
waiting on the full Databricks Structured Streaming job.

Usage:
    export EVENTHUB_CONNECTION_STR="Endpoint=sb://...;..."
    python consume_stream_preview.py --out streamed_events.jsonl --seconds 15
"""

import argparse
import json
import os
import time

from azure.eventhub import EventHubConsumerClient


def make_on_event(out_file):
    def on_event(partition_context, event):
        if event is None:
            return
        line = event.body_as_str(encoding="UTF-8")
        out_file.write(line + "\n")
        out_file.flush()
        data = json.loads(line)
        print(f"received: over {data.get('over')} - {data.get('bowler')} to {data.get('batter')}")
        partition_context.update_checkpoint(event)

    return on_event


def main():
    parser = argparse.ArgumentParser(description="Preview events currently in the Event Hub")
    parser.add_argument("--out", default="streamed_events.jsonl")
    parser.add_argument("--eventhub-name", default="cricket-ball-events")
    parser.add_argument("--consumer-group", default="$Default")
    parser.add_argument("--seconds", type=int, default=15, help="How long to listen before stopping")
    args = parser.parse_args()

    connection_str = os.environ.get("EVENTHUB_CONNECTION_STR")
    if not connection_str:
        raise SystemExit("Set EVENTHUB_CONNECTION_STR environment variable first.")

    client = EventHubConsumerClient.from_connection_string(
        conn_str=connection_str,
        consumer_group=args.consumer_group,
        eventhub_name=args.eventhub_name,
    )

    with open(args.out, "w", encoding="utf-8") as out_file:
        with client:
            print(f"Listening for {args.seconds}s, writing events to {args.out} ...")
            client.receive(
                on_event=make_on_event(out_file),
                starting_position="-1",  # read from the earliest available event
            )
            time.sleep(args.seconds)

    print(f"Done. Check {args.out} for the events received.")


if __name__ == "__main__":
    main()