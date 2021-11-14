/* DDL for creating the nba_schedule table */
CREATE TABLE IF NOT EXISTS nba_schedule(
    game_date DATE,
    home_team_id INTEGER REFERENCES nba_teams (nba_team_id),
    away_team_id INTEGER REFERENCES nba_teams (nba_team_id),
    PRIMARY KEY (game_date, home_team_id, away_team_id)
);