CREATE OR REPLACE VIEW player_stat_totals AS
SELECT
    player_id,
    SUM(field_goals) AS field_goals,
    SUM(field_goal_attempts) AS field_goal_attempts,
    SUM(free_throws) AS free_throws,
    SUM(free_throw_attempts) AS free_throw_attempts,
    SUM(three_pointers) AS three_pointers,
    SUM(points) AS points,
    SUM(rebounds) AS rebounds,
    SUM(assists) AS assists,
    SUM(steals) AS steals,
    SUM(blocks) AS blocks,
    SUM(turnovers) AS turnovers
FROM
    game_log
GROUP BY
    player_id
;
