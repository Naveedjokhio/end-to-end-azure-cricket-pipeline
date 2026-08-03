/* @bruin
name: default.team_summary_quality
type: databricks.sql
description: Data quality gate for the team_summary Gold table.
materialization:
  type: view

columns:
  - name: batting_team
    type: string
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

custom_checks:
  - name: row count is greater than zero
    query: SELECT count(*) > 0 FROM default.team_summary_quality
    value: 1
@bruin */

SELECT * FROM databricks_e2e_cricket.default.team_summary