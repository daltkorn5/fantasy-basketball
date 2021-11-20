/* Create the 7 tables in the correct order */
\i sql/table_definitions/create_table_teams.sql
\i sql/table_definitions/create_table_nba_teams.sql
\i sql/table_definitions/create_table_players.sql
\i sql/table_definitions/create_table_match_ups.sql
\i sql/table_definitions/create_table_nba_schedule.sql
\i sql/table_definitions/create_table_rosters.sql
\i sql/table_definitions/create_table_game_log.sql

/* Then create the views */
\i sql/view_definitions/create_view_schedule_per_team.sql
\i sql/view_definitions/create_view_game_count_per_team_per_week.sql