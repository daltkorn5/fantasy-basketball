"""This script should be run at the beginning of the Fantasy Basketball season"""
from typing import List, Dict, Any
from unidecode import unidecode

from src.utils.bball_reference_scraper_tool import BasketballReferenceWebScraper
from src.utils.query_tool import QueryTool
from src.utils.spotrac_scraper_tool import SpotracScraperTool
from src.yahootils.yahoo_api_tool import YahooFantasyApiTool


class FantasySeasonInitializer:
    def __init__(self):
        self.query_tool = QueryTool()
        self.yahoo_api_tool = YahooFantasyApiTool()
        self.bball_reference_scraper = BasketballReferenceWebScraper()
        self.spotrac_scraper = SpotracScraperTool()

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

    def _load_nba_teams(self, nba_teams: List[Dict[str, Any]]) -> None:
        """Load the NBA team data into the nba_teams table

        :param nba_teams: The NBA team data that will be loaded into the DB. Looks like:
            [
                {
                    "team_id": 1,
                    "team_name": "Chicago Bulls",
                    "team_code": "CHI"
                },
                ...
            ]
        """
        print("Loading NBA teams into DB")
        query = (
            "INSERT INTO nba_teams VALUES "
            "(%(team_id)s, %(team_name)s, %(team_code)s) "
            "ON CONFLICT (nba_team_id) DO UPDATE "
            "SET team_name = %(team_name)s, team_code = %(team_code)s;"
        )
        self.query_tool.insert(query, nba_teams)

    def _load_players(self, players: List[Dict[str, Any]]) -> None:
        """Load the players into the database

        :param players: The player data that will be loaded. Looks like:
            [
                {"player_id": 123, "player_name": Michael Jordan, "status": None, "positions": ["SG", "SF"], "team_id": 1},
                {"player_id": 456, "player_name": Scottie Pippen, "status": "INJ", "positions": ["SF", "PF"], "team_id": 1},
                {"player_id": 789, "player_name": Dennis Rodman, "status": "O", "positions": ["PF", "C"], "team_id": 1},
                ...
            ]
        """
        print("Loading players into DB")
        query = (
            "INSERT INTO players(player_id, player_name, nba_team_id, positions, status) VALUES "
            "(%(player_id)s, %(player_name)s, %(team_id)s, %(positions)s, %(status)s) "
            "ON CONFLICT (player_id) DO UPDATE "
            "SET player_name = %(player_name)s, nba_team_id = %(team_id)s, "
            "positions = %(positions)s, status = %(status)s;"
        )
        self.query_tool.insert(query, players)

    def _load_teams(self, teams: List[Dict[str, Any]]) -> None:
        """Load the fantasy teams into the database

        :param teams: The team data that will be loaded. Looks like:
            [
                {"team_id": "1", "team_name": "Jo Quinoa", "manager": "Joakim"},
                {"team_id": "2", "team_name": "Comin' Up Rose's", "manager": "Derrick"},
                ...
            ]
        """
        print("Loading teams into DB")
        query = (
            "INSERT INTO teams(team_id, team_name, manager) VALUES"
            "(%(team_id)s, %(team_name)s, %(manager)s);"
        )
        self.query_tool.insert(query, teams)

    def _load_rosters(self, rosters: List[Dict[str, Any]]) -> None:
        """Load the rosters into the database

        :param rosters: The roster data that will be loaded. Looks like:
            [
                {
                    "team_id": 1,
                    "player_id": 123
                },
                ...
            ]
        """
        print("Loading rosters into DB")
        query = (
            "INSERT INTO rosters(player_id, team_id) VALUES "
            "(%(player_id)s, %(team_id)s);"
        )
        self.query_tool.insert(query, rosters)

    def _load_match_ups(self) -> None:
        """Load the match-ups into the database

        Note these are only the match-ups for my team

        """
        print("Loading match ups into DB")
        team_id = self.query_tool.select("select team_id from teams where manager = 'Danny'")[0]["team_id"]
        match_ups = self.yahoo_api_tool.get_match_ups(team_id)
        query = (
            "INSERT INTO match_ups(team_id, week_no, week_start, week_end, is_playoffs) VALUES "
            "(%(team_id)s, %(week_no)s, %(week_start)s, %(week_end)s, %(is_playoffs)s);"
        )
        self.query_tool.insert(query, match_ups)

    def _get_season_year(self) -> int:
        """Get the year that the current NBA season *ends in*.

        This the year that Basketball reference uses for its schedule/stats URLs

        :return: The year that the NBA season ends in
        """
        query = "select max(week_end) as season_end from match_ups"
        year = self.query_tool.select(query)[0]["season_end"].year
        return year

    @staticmethod
    def _get_team_id_map(nba_teams: List[Dict[str, Any]]) -> Dict[str, int]:
        """Helper function to create a map of NBA team names to IDs

        :param nba_teams: The list of NBA teams. Looks like:
            [
                {
                    "team_id": 1,
                    "team_name": "Chicago Bulls",
                    "team_code": "CHI"
                },
                ...
            ]
        :return: A map of team names to IDs. Looks like:
            {
                "Chicago Bulls": 1,
                "Portland Trailblazers": 2,
                ...
            }
        """
        nba_team_map = {}
        for team in nba_teams:
            nba_team_map[team["team_name"]] = team["team_id"]

        return nba_team_map

    def _load_schedule(self, schedule: List[Dict[str, Any]], team_id_map: Dict[str, int]) -> None:
        """Load the NBA schedule into the database

        :param team_id_map: A map of team names to team IDs
        :param schedule: The NBA schedule scraped. Looks like:
            [
                {
                    "game_date": 2021-11-19,
                    "home_team": "Chicago Bulls",
                    "visiting_team": "Portland Trailblazers"
                },
                ...
            ]
        """
        print("Loading schedule into DB")

        for row in schedule:
            row["home_team_id"] = team_id_map[row["home_team"]]
            row["away_team_id"] = team_id_map[row["visiting_team"]]

        query = (
            "INSERT INTO nba_schedule(game_date, home_team_id, away_team_id) VALUES "
            "(%(game_date)s, %(home_team_id)s, %(away_team_id)s) "
            "ON CONFLICT DO NOTHING;"
        )
        self.query_tool.insert(query, schedule)

    def _get_player_id_map(self) -> Dict[str, int]:
        """Create a map for player name to ID

        Also includes any player "aliases" mapped to the correct ID.
        For example, "Mo Bamba" vs "Mohamad Bamba"

        :return: A map for player names to IDs. Looks like:
            {
                "Michael Jordan": 1,
                "MJ": 1,
                "Scottie Pippen": 2,
                ...
            }
        """
        player_id_map = {}

        query = (
            "WITH aliases AS ("
            "SELECT player_id, player_name, UNNEST(player_aliases) as alias "
            "FROM players) "
            "SELECT player_id, players.player_name, alias "
            "FROM players "
            "LEFT JOIN aliases USING (player_id)"
        )
        results = self.query_tool.select(query)
        for row in results:
            player_name = row["player_name"]
            player_id = row["player_id"]
            player_id_map[player_name] = player_id

            alias = row["alias"]
            if alias:
                player_id_map[alias] = player_id

        return player_id_map

    def _load_salaries(self, year: int) -> None:
        """Get player salaries from Spotrac and update the players table accordingly

        :param year: The year for which you want the salaries
        """
        print("Loading salaries into DB")
        player_id_map = self._get_player_id_map()

        salaries = self.spotrac_scraper.scrape_salaries(year)
        missing_players = []
        for row in salaries:
            row["player_id"] = player_id_map.get(row["player_name"])
            if row["player_id"] is None:
                missing_players.append(row)

        query = (
            "UPDATE players SET salary = %(salary)s WHERE player_id = %(player_id)s;"
        )
        self.query_tool.insert(query, salaries)

        print("These players are missing from the DB:")
        for player in missing_players:
            print(player["player_name"])

    def initialize_season(self) -> None:
        """Initialize the database for a new Fantasy Basketball season

        Initializing a season consists of cleaning the database, then uploading all the
        data that we get from Yahoo. Lastly we upload the NBA schedule from Basketball Reference
        and the player salaries from Spotrac

        """
        self._clean_database()

        players, nba_teams = self.yahoo_api_tool.get_players_and_nba_teams()
        self._load_nba_teams(nba_teams)
        self._load_players(players)

        teams, rosters = self.yahoo_api_tool.get_teams_and_rosters()
        self._load_teams(teams)
        self._load_rosters(rosters)

        self._load_match_ups()

        year = self._get_season_year()
        team_id_map = self._get_team_id_map(nba_teams)
        schedule = self.bball_reference_scraper.scrape_schedule(year)
        self._load_schedule(schedule, team_id_map)

        self._load_salaries(year)


if __name__ == "__main__":
    season_initializer = FantasySeasonInitializer()
    season_initializer.initialize_season()
