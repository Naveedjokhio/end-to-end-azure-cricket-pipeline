/* @bruin
name: default.over_summary_quality
type: databricks.sql
description: Data quality gate for the over_summary Gold table.
materialization:
  type: view

columns:
  - name: over
    type: bigint
    checks:
      - name: not_null
      - name: unique
  - name: total_runs
    type: bigint
    checks:
      - name: not_null
      - name: positive
  - name: total_balls
    type: bigint
    checks:
      - name: not_null
      - name: positive
  - name: run_rate
    type: double
    checks:
      - name: not_null

custom_checks:
  - name: exactly 20 overs present
    query: SELECT count(distinct over) FROM default.over_summary_quality
    value: 20
@bruin */

SELECT * FROM databricks_e2e_cricket.default.over_summary