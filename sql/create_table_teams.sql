/* DDL for creating the teams table, which contains the data pertaining to the Fantasy Basketball teams in the league */
CREATE TABLE IF NOT EXISTS teams(
    team_id INTEGER PRIMARY KEY,
    team_name VARCHAR(30) NOT NULL,
    manager VARCHAR(30) NOT NULL
);