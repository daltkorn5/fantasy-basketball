import datetime
import time
from typing import List, Dict, Any, Union, Set

import requests

from src.utils.bball_reference_scraper_tool import BasketballReferenceWebScraper
from src.utils.query_tool import QueryTool
from src.utils.spotrac_scraper_tool import SpotracScraperTool
from src.yahootils.yahoo_api_tool import YahooFantasyApiTool


class DataLoader:
    """Class with methods for loading various data into the db"""
    def __init__(self):
        self.query_tool = QueryTool()
        self.yahoo_api_tool = YahooFantasyApiTool()
        self.bball_reference_scraper = BasketballReferenceWebScraper()
        self.spotrac_scraper = SpotracScraperTool()

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

    def load_players_and_nba_teams(self) -> None:
        """Get the players and NBA teams data from Yahoo and load it into the DB"""
        players, nba_teams = self.yahoo_api_tool.get_players_and_nba_teams()
        self._load_nba_teams(nba_teams)
        self._load_players(players)

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
            "(%(team_id)s, %(team_name)s, %(manager)s) "
            "ON CONFLICT (team_id) DO UPDATE "
            "SET team_name = %(team_name)s, manager = %(manager)s;"
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

    def load_teams_and_rosters(self) -> None:
        """Get the fantasy team and roster data from Yahoo and load it into the DB"""
        teams, rosters = self.yahoo_api_tool.get_teams_and_rosters()
        self._load_teams(teams)
        self._load_rosters(rosters)

    def load_matchups(self) -> None:
        """Load the match-ups into the database

        Note these are only the match-ups for my team

        """
        print("Loading matchups into DB")
        team_id = self.query_tool.select("select team_id from teams where manager = 'Danny'")[0]["team_id"]
        match_ups = self.yahoo_api_tool.get_match_ups(team_id)
        query = (
            "INSERT INTO match_ups(team_id, week_no, week_start, week_end, is_playoffs) VALUES "
            "(%(team_id)s, %(week_no)s, %(week_start)s, %(week_end)s, %(is_playoffs)s);"
        )
        self.query_tool.insert(query, match_ups)

    def _get_team_id_map(self) -> Dict[str, int]:
        """Helper function to create a map of NBA team names to IDs

        :return: A map of team names to IDs. Looks like:
            {
                "Chicago Bulls": 1,
                "Portland Trailblazers": 2,
                ...
            }
        """
        query = "SELECT nba_team_id, team_name FROM nba_teams;"
        nba_teams = self.query_tool.select(query)

        team_id_map = {}
        for team in nba_teams:
            team_name = team["team_name"]
            team_id = team["nba_team_id"]
            team_id_map[team_name] = team_id

        return team_id_map

    def _get_season_year(self) -> int:
        """Get the year that the current NBA season *ends in*.

        This the year that Basketball reference uses for its schedule/stats URLs

        :return: The year that the NBA season ends in
        """
        query = "select max(week_end) as season_end from match_ups"
        year = self.query_tool.select(query)[0]["season_end"].year
        return year

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
        for row in schedule:
            row["home_team_id"] = team_id_map[row["home_team"]]
            row["away_team_id"] = team_id_map[row["visiting_team"]]

        query = (
            "INSERT INTO nba_schedule(game_date, home_team_id, away_team_id) VALUES "
            "(%(game_date)s, %(home_team_id)s, %(away_team_id)s) "
            "ON CONFLICT DO NOTHING;"
        )
        self.query_tool.insert(query, schedule)

    def load_schedule(self) -> None:
        """Get the NBA season schedule from Basketball Reference and load it into the DB"""
        print("Loading schedule into DB")
        team_id_map = self._get_team_id_map()
        year = self._get_season_year()
        schedule = self.bball_reference_scraper.scrape_schedule(year)

        self._load_schedule(schedule, team_id_map)

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

    def load_salaries(self) -> None:
        """Get the player salaries from Spotrac and load them into the DB"""
        print("Loading salaries into DB")
        player_id_map = self._get_player_id_map()
        year = self._get_season_year()

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

    def _get_latest_loaded_game_log_date(self) -> datetime.date:
        """Get the latest date in the game_log table for which there is data"""
        query = "SELECT max(game_date) as latest_date from game_log;"
        latest_date = self.query_tool.select(query)[0]["latest_date"]
        return latest_date + datetime.timedelta(days=1)

    def _get_schedule(self, start_date: Union[str, datetime.date], team: str = None) -> List[Dict[str, str]]:
        """Get the NBA schedule from the provided start date to today

        :param start_date: The lower bound for the schedule select query
        :param team: Optional parameter to specify which team's schedule you want
        :return: The NBA schedule between start_date and today. Looks like:
            [
                {
                    "game_date": 2021-11-01,
                    "home_team": "CHI",
                    "away_team": "POR",
                },
                ...
            ]
        """
        team_clause = ""
        if team:
            team_clause = "AND (home_teams.team_code = %(team)s OR away_teams.team_code = %(team)s)"

        # Note we had to change some of the team codes because Basketball Reference's don't match Yahoo's
        query = (
            "WITH modified_nba_teams as (SELECT nba_team_id, "
            "CASE WHEN team_code = 'BKN' THEN 'BRK' "
            "WHEN team_code = 'PHX' THEN 'PHO' "
            "WHEN team_code = 'CHA' THEN 'CHO' "
            "else team_code END AS team_code FROM nba_teams) "
            "SELECT game_date, home_teams.team_code as home_team, away_teams.team_code as away_team "
            "FROM nba_schedule "
            "JOIN modified_nba_teams home_teams on (home_teams.nba_team_id = nba_schedule.home_team_id) "
            "JOIN modified_nba_teams away_teams on (away_teams.nba_team_id = nba_schedule.away_team_id) "
            f"WHERE game_date between %(start_date)s AND %(end_date)s {team_clause}"
        )
        params = {
            "start_date": start_date,
            "end_date": datetime.date.today() - datetime.timedelta(days=1),
            "team": team
        }
        schedule = self.query_tool.select(query, params)
        return schedule

    def _load_game_batch(
            self,
            game_logs: List[Dict[str, Any]],
            player_id_map: Dict[str, int]
    ) -> Set[str]:
        """

        :param game_logs:
        :return:
        """
        missing_players = set()
        upload = []
        for row in game_logs:
            row["player_id"] = player_id_map.get(row["player_name"])
            if row["player_id"] is None:
                missing_players.add(row["player_name"])
            else:
                upload.append(row)

        query = (
            "INSERT INTO game_log(player_id, game_date, minutes_played, field_goals, field_goal_attempts, "
            "free_throws, free_throw_attempts, three_pointers, points, rebounds, assists, steals, blocks, "
            "turnovers) VALUES (%(player_id)s, %(game_date)s, %(mp)s, %(fg)s, %(fga)s, %(ft)s, %(fta)s, %(3p)s, "
            "%(pts)s, %(trb)s, %(ast)s, %(stl)s, %(blk)s, %(tov)s) "
            "ON CONFLICT(player_id, game_date) DO UPDATE SET "
            "minutes_played = %(mp)s, field_goals = %(fg)s, field_goal_attempts = %(fga)s, "
            "free_throws = %(ft)s, free_throw_attempts = %(fta)s, three_pointers = %(3p)s, "
            "points = %(pts)s, rebounds = %(trb)s, assists = %(ast)s, steals = %(stl)s, blocks = %(blk)s, "
            "turnovers = %(tov)s"
        )
        self.query_tool.insert(query, upload)

        return missing_players

    def _get_game_logs(self, schedule: List[Dict[str, str]], player_id_map: Dict[str, int]) -> Set[str]:
        """Get the game logs from Basketball Reference

        :param schedule: The NBA schedule
        :return: The game logs for each game in the provided schedule
        """
        game_logs = []
        games_scraped = 0
        missing_players = set()
        for row in schedule:
            print(f"Getting game log for {row}")
            try:
                game_log = self.bball_reference_scraper.scrape_game_log(**row)
                time.sleep(5)
            except requests.exceptions.ConnectionError:
                print(f"Game for {row} not found")
                continue

            game_logs.extend(game_log)
            games_scraped += 1

            if games_scraped % 20 == 0:
                print("Loading batch of games")
                missing_players.union(self._load_game_batch(game_logs, player_id_map))
                game_logs = []

        return missing_players

    def load_game_logs(self, start_date: str = None, team: str = None) -> None:
        """Get the game log data from Basketball Reference and load it into the DB

        :param start_date: Optional start date for loading the game logs. If not supplied,
            defaults to the latest date in the `game_log` table
        :param team: Optional team whose game logs you want
        """
        if start_date is None:
            start_date = self._get_latest_loaded_game_log_date()

        print(f"Loading game logs from {start_date} to today into DB")
        schedule = self._get_schedule(start_date, team)
        player_id_map = self._get_player_id_map()
        missing_players = self._get_game_logs(schedule, player_id_map)

        print("These players are missing from the DB:")
        for player in missing_players:
            print(player)


