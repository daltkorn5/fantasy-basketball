"""This script updates the players and rosters tables and will upload any new game logs"""
from src.utils.data_loader import DataLoader
from src.utils.query_tool import QueryTool


class MidSeasonUpdater:
    def __init__(self):
        self.query_tool = QueryTool()
        self.data_loader = DataLoader()

    def _clean_rosters(self) -> None:
        """Clean the rosters table before they are re-uploaded from Yahoo"""
        print("Cleaning rosters")
        query = "DELETE FROM rosters;"
        self.query_tool.delete(query)

    def update_season(self) -> None:
        """Update the database mid-season.

        This consists of:
            - Updating the players table to add any new players and update their statuses
            - Reloading the salaries
            - Updating the teams in case someone changed their team name
            - Reloading the rosters
            - Loading any new game logs
        """
        self._clean_rosters()
        self.data_loader.load_players_and_nba_teams()
        self.data_loader.load_salaries()
        self.data_loader.load_teams_and_rosters()
        self.data_loader.load_game_logs()


if __name__ == "__main__":
    season_updater = MidSeasonUpdater()
    season_updater.update_season()
