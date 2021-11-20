/* DDL for creating the table that contains the information about the NBA teams */
CREATE TABLE IF NOT EXISTS nba_teams(
    nba_team_id INTEGER PRIMARY KEY,
    team_name VARCHAR(50),
    team_code VARCHAR(3) /* This is the team abbreviation, like CHI or LAL */
);