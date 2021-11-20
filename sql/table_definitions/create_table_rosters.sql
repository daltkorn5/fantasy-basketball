/* DDL for creating the rosters table, which has the rosters of the Fantasy teams */
CREATE TABLE IF NOT EXISTS rosters(
    player_id INTEGER PRIMARY KEY REFERENCES players (player_id),
    team_id INTEGER NOT NULL REFERENCES teams (team_id)
);