# End to End Azure Cricket Project

A complete, working data engineering pipeline built on Azure: cricket match
data flows from a free, unlimited data source through batch and simulated
streaming ingestion, gets transformed and modeled in Databricks, is
validated by an automated data quality gate, and lands in a published
analytics dashboard — all orchestrated end to end with Kestra.

**Live dashboard:** https://adb-7405607340327595.15.azuredatabricks.net/dashboardsv3/01f18f02ee2215a0bbefecbf1fc1289b/published?o=7405607340327595

## Architecture

![Architecture diagram](docs/architecture.png)

Text version of the same flow:

```
Cricsheet (batch)  ──┐
                      ├─→ dltHub ──→ ADLS raw ──┐
Cricsheet (simulated  │                          │
  streaming)  ────────┘→ Event Hubs ──→ ADLS raw/streaming ──┐
                                                                │
                                                                ▼
                                                    Spark (Databricks)
                                                                │
                                                                ▼
                                                        ADLS silver
                                                                │
                                                                ▼
                                            Gold tables (Unity Catalog)
                                          batsman / bowler / team / over
                                                                │
                                          ┌─────────────────────┴───────────────┐
                                          ▼                                     ▼
                                Bruin (quality gate)              Databricks Dashboard
```

Orchestrated end to end by **Kestra**, running in **Docker**. Infrastructure
is provisioned with **Terraform**.

## Why Cricsheet instead of RapidAPI

RapidAPI's free tier caps requests, which breaks a pipeline that needs to
run repeatedly during development, demos, and scheduled orchestration.
Cricsheet (cricsheet.org) is a free, unlimited, no-signup source of
ball-by-ball cricket match data. Batch ingestion reads it directly. For
streaming, there is no free, unlimited *live* cricket feed available
anywhere — so the streaming leg **replays historical Cricsheet data
ball-by-ball into Event Hubs with a delay**, exercising the exact same
streaming path a real live feed would use. This is disclosed here
transparently: the streaming source is simulated, not a live match feed.

## What's actually built (vs. the original diagram)

| Component | Status | Notes |
|---|---|---|
| Terraform infra | ✅ | Resource group, ADLS Gen2 (raw/silver/gold), Event Hubs, Databricks workspace (Premium SKU — Standard is now deprecated by Azure) |
| Batch ingestion | ✅ | `dlt_batch_ingestion.py` — a proper dltHub pipeline, filesystem destination into `raw/dlt_batch_ingestion` |
| Streaming ingestion | ✅ | `stream_simulator.py` replays Cricsheet matches into Event Hubs; `consume_to_adls.py` lands each event in `raw/streaming/` |
| Spark transformation | ✅ | Explodes nested innings/overs/deliveries JSON into flat Delta tables in `silver/` |
| Gold layer | ✅ | 4 tables (`batsman_summary`, `bowler_summary`, `team_summary`, `over_summary`), registered in Unity Catalog |
| Dashboard | ✅ | Databricks SQL Dashboard "IPL Cricket Analytics", published |
| Data quality (Bruin) | ✅ | 4 quality-check assets against the Gold tables, 32/32 checks passing |
| Orchestration (Kestra) | ✅ | Runs in Docker; automates the batch ingestion + Bruin quality gate on a daily schedule |

## Project structure

```
end-to-end-azure-cricket-project/
├── terraform/              # Infra as code: ADLS, Event Hubs, Databricks workspace
├── scripts/
│   ├── download_cricsheet.py     # (legacy) direct download helper
│   ├── dlt_batch_ingestion.py    # dltHub pipeline: Cricsheet -> ADLS raw
│   ├── stream_simulator.py       # replays a match into Event Hubs
│   └── consume_to_adls.py        # Event Hubs -> ADLS raw/streaming
├── bruin_project/
│   ├── .bruin.yml           # connection config (NEVER commit real credentials)
│   ├── pipeline.yml
│   └── assets/              # 4 SQL quality-check assets, one per Gold table
├── kestra/flows/            # orchestration flow definition
└── docker/docker-compose.yml
```

## Data quality: what Bruin actually caught

Two of the first quality-check runs failed — not because of bugs, but
because the checks were initially too strict:

- `total_runs` was checked as strictly positive, but a batter can be given
  out for a duck (0 runs) — a completely valid outcome. Relaxed to
  non-negative.
- The bowling economy sanity check flagged bowlers with a tiny sample size
  (e.g. 1 ball bowled for a six = economy of 36), which is statistical
  noise, not bad data. The check now only applies to bowlers with 30+
  balls bowled.

This is a genuine example of iterating on data quality rules against real
data, not just writing checks that happen to pass.

## Running it yourself

See inline comments in each script for exact commands. In short:

1. `terraform apply` in `terraform/` to provision Azure infra
2. `python scripts/dlt_batch_ingestion.py --source ./data/raw` for batch
3. `python scripts/stream_simulator.py` + `python scripts/consume_to_adls.py`
   for the simulated streaming leg
4. Run the Spark transformation + Gold table notebooks in Databricks
5. `bruin run ./bruin_project` for quality checks
6. The Kestra flow in `kestra/flows/` automates steps 2 and 5 on a schedule