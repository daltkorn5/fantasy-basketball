CREATE OR REPLACE VIEW player_stat_averages AS
SELECT
    player_id,
    ROUND(AVG(field_goals), 2) AS field_goals,
    ROUND(AVG(field_goal_attempts), 2) AS field_goal_attempts,
    ROUND(AVG(free_throws), 2) AS free_throws,
    ROUND(AVG(free_throw_attempts), 2) AS free_throw_attempts,
    ROUND(AVG(three_pointers), 2) AS three_pointers,
    ROUND(AVG(points), 2) AS points,
    ROUND(AVG(rebounds), 2) AS rebounds,
    ROUND(AVG(assists), 2) AS assists,
    ROUND(AVG(steals), 2) AS steals,
    ROUND(AVG(blocks), 2) AS blocks,
    ROUND(AVG(turnovers), 2) AS turnovers
FROM
    game_log
GROUP BY
    player_id
;
