/* DDL for a view that the game_date, the team ID, and the team name. No home or away information */
CREATE OR REPLACE VIEW schedule_per_team AS
SELECT
    game_date,
    nba_team_id,
    team_code
FROM
    nba_schedule s
JOIN nba_teams t on (s.home_team_id = t.nba_team_id)
UNION ALL
SELECT
    game_date,
    nba_team_id,
    team_code
FROM
    nba_schedule s
JOIN nba_teams t on (s.away_team_id = t.nba_team_id)
;