"""
Streaming ingestion source: simulated live feed.

RapidAPI's free tier can't give unlimited real-time data, and there's no
free unlimited live cricket streaming API. So instead this replays historical
ball-by-ball data from Cricsheet as if it were arriving live: it reads a
match JSON file delivery-by-delivery and pushes each one to Azure Event Hubs
with a small delay in between, so the rest of the pipeline (Event Hubs ->
Spark -> Silver) can be built and tested exactly as if it were real streaming
data, without depending on any rate-limited external API.

Usage:
    export EVENTHUB_CONNECTION_STR="Endpoint=sb://...;SharedAccessKeyName=...;..."
    python stream_simulator.py --match-file ./data/raw/1234567.json --delay 2
"""

import argparse
import json
import time
from pathlib import Path

from azure.eventhub import EventData, EventHubProducerClient


def iter_deliveries(match_json: dict):
    """Yield one event dict per ball, in order, across all innings."""
    for innings in match_json.get("innings", []):
        team = innings.get("team")
        for over in innings.get("overs", []):
            over_num = over.get("over")
            for ball_index, delivery in enumerate(over.get("deliveries", []), start=1):
                yield {
                    "team": team,
                    "over": over_num,
                    "ball": ball_index,
                    "batter": delivery.get("batter"),
                    "bowler": delivery.get("bowler"),
                    "non_striker": delivery.get("non_striker"),
                    "runs_batter": delivery.get("runs", {}).get("batter"),
                    "runs_extras": delivery.get("runs", {}).get("extras"),
                    "runs_total": delivery.get("runs", {}).get("total"),
                    "wickets": delivery.get("wickets", []),
                }


def stream_match(match_file: Path, connection_str: str, eventhub_name: str, delay_seconds: float):
    match_json = json.loads(match_file.read_text())

    producer = EventHubProducerClient.from_connection_string(
        conn_str=connection_str, eventhub_name=eventhub_name
    )

    with producer:
        for i, event in enumerate(iter_deliveries(match_json), start=1):
            batch = producer.create_batch()
            batch.add(EventData(json.dumps(event)))
            producer.send_batch(batch)
            print(f"[{i}] sent ball: over {event['over']} - {event['bowler']} to {event['batter']}")
            time.sleep(delay_seconds)

    print("Match replay complete.")


def main():
    parser = argparse.ArgumentParser(description="Replay a Cricsheet match as a simulated live stream")
    parser.add_argument("--match-file", required=True, help="Path to a single Cricsheet match JSON file")
    parser.add_argument("--eventhub-name", default="cricket-ball-events")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds to wait between balls")
    args = parser.parse_args()

    import os

    connection_str = os.environ.get("EVENTHUB_CONNECTION_STR")
    if not connection_str:
        raise SystemExit("Set EVENTHUB_CONNECTION_STR environment variable first (see terraform output).")

    stream_match(Path(args.match_file), connection_str, args.eventhub_name, args.delay)


if __name__ == "__main__":
    main()
