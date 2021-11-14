init-db:
	psql -U nba nba -c "\i sql/initalize_db.sql"