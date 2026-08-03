/* @bruin
name: default.bowler_summary_quality
type: databricks.sql
description: Data quality gate for the bowler_summary Gold table.
materialization:
  type: view

columns:
  - name: bowler
    type: string
    checks:
      - name: not_null
      - name: unique
  - name: runs_conceded
    type: bigint
    description: runs conceded (0 is valid over a very small sample of dot balls)
    checks:
      - name: not_null
  - name: balls_bowled
    type: bigint
    checks:
      - name: not_null
      - name: positive
  - name: economy
    type: double
    checks:
      - name: not_null

custom_checks:
  - name: runs_conceded is never negative
    query: SELECT count(*) FROM default.bowler_summary_quality WHERE runs_conceded < 0
    value: 0
  - name: economy is within a plausible T20 range for established bowlers
    description: >
      Bowlers with only a handful of balls can show extreme economy by
      chance (e.g. 1 ball for a six = economy 36); this check only applies
      to bowlers with 30+ balls (5+ overs) to avoid flagging that noise.
    query: SELECT count(*) FROM default.bowler_summary_quality WHERE balls_bowled >= 30 AND (economy < 0 OR economy > 15)
    value: 0
  - name: row count is greater than zero
    query: SELECT count(*) > 0 FROM default.bowler_summary_quality
    value: 1
@bruin */

SELECT * FROM databricks_e2e_cricket.default.bowler_summary