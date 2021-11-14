/* DDL for creating the fantasy match_ups table */
CREATE TABLE IF NOT EXISTS match_ups(
    team_id INTEGER REFERENCES teams (team_id), /* this is the opposing team ID */
    week_no INTEGER,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    is_playoffs BOOL NOT NULL DEFAULT FALSE,
    PRIMARY KEY(team_id, week_no)
);