/* @bruin
name: default.batsman_summary_quality
type: databricks.sql
description: Data quality gate for the batsman_summary Gold table.
materialization:
  type: view

columns:
  - name: batter
    type: string
    checks:
      - name: not_null
      - name: unique
  - name: total_runs
    type: bigint
    description: total runs scored (0 is valid -- a batter can be out for a duck)
    checks:
      - name: not_null
  - name: balls_faced
    type: bigint
    checks:
      - name: not_null
      - name: positive

custom_checks:
  - name: total_runs is never negative
    query: SELECT count(*) FROM default.batsman_summary_quality WHERE total_runs < 0
    value: 0
  - name: no batter has more runs than balls faced x 6
    query: SELECT count(*) FROM default.batsman_summary_quality WHERE total_runs > balls_faced * 6
    value: 0
  - name: row count is greater than zero
    query: SELECT count(*) > 0 FROM default.batsman_summary_quality
    value: 1
@bruin */

SELECT * FROM databricks_e2e_cricket.default.batsman_summary