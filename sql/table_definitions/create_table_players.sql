/* DDL for creating the players table */
CREATE TABLE IF NOT EXISTS players(
    player_id INTEGER PRIMARY KEY,
    player_name VARCHAR(30) NOT NULL,
    player_aliases VARCHAR[] NOT NULL DEFAULT ARRAY[]::VARCHAR[], /* other names the player might go by, like nicknames */
    nba_team_id INTEGER REFERENCES nba_teams (nba_team_id),
    salary INTEGER,
    positions VARCHAR(2)[],
    status VARCHAR(3)
);