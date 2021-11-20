/* DDL the create a view that calculates the number of games teams play each week */
CREATE OR REPLACE VIEW game_count_per_team_per_week AS
SELECT
    nba_team_id,
    team_code,
    week_no,
    week_start,
    week_end,
    count(*)
FROM
    schedule_per_team
JOIN match_ups on (game_date between week_start and week_end)
GROUP BY
    1, 2, 3, 4, 5
;