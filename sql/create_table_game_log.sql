/* DDL for creating the game_log table. This table contains the stats accrued by each player in each game */
CREATE TABLE IF NOT EXISTS game_log(
    player_id INTEGER REFERENCES players (player_id),
    game_date DATE,
    minutes_played REAL NOT NULL DEFAULT 0.0,
    field_goals INTEGER NOT NULL DEFAULT 0,
    field_goal_attempts INTEGER NOT NULL DEFAULT 0,
    free_throws INTEGER NOT NULL DEFAULT 0,
    free_throw_attempts INTEGER NOT NULL DEFAULT 0,
    three_pointers INTEGER NOT NULL DEFAULT 0,
    points INTEGER NOT NULL DEFAULT 0,
    rebounds INTEGER NOT NULL DEFAULT 0,
    assists INTEGER NOT NULL DEFAULT 0,
    steals INTEGER NOT NULL DEFAULT 0,
    blocks INTEGER NOT NULL DEFAULT 0,
    turnovers INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (player_id, game_date)
);