SHELL := /bin/bash

init-db:
	psql -U nba nba -c "\i sql/initalize_db.sql"

init-season:
	PYTHONPATH=$$BBALL_HOME python src/initialize_season.py

update-season:
	PYTHONPATH=$$BBALL_HOME python src/mid_season_update.py
