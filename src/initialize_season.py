"""This script should be run at the beginning of the Fantasy Basketball season"""

from src.utils.data_loader import DataLoader
from src.utils.query_tool import QueryTool


class FantasySeasonInitializer:
    def __init__(self):
        self.data_loader = DataLoader()
        self.query_tool = QueryTool()

    def _clean_database(self) -> None:
        """Clean the database at the beginning of a season

        By "cleaning" we mean deleting all the data from the `teams`, `rosters`,
        and `match_ups` tables. We don't want to track this data year over year so we can just refresh them.

        """
        tables_to_clean = ("rosters", "match_ups", "teams")
        for table in tables_to_clean:
            print(f"Cleaning {table}")
            query = f"DELETE FROM {table};"
            self.query_tool.delete(query)

    def initialize_season(self) -> None:
        """Initialize the database for a new Fantasy Basketball season

        Initializing a season consists of cleaning the database, then uploading all the
        data that we get from Yahoo. Lastly we upload the NBA schedule from Basketball Reference
        and the player salaries from Spotrac

        """
        self._clean_database()
        self.data_loader.load_players_and_nba_teams()
        self.data_loader.load_teams_and_rosters()
        self.data_loader.load_matchups()
        self.data_loader.load_schedule()
        self.data_loader.load_salaries()


if __name__ == "__main__":
    season_initializer = FantasySeasonInitializer()
    season_initializer.initialize_season()
