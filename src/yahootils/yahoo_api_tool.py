from typing import List, Dict, Tuple

from yahoo_oauth import OAuth2


class YahooFantasyApiTool:
    YAHOO_API_URL = "https://fantasysports.yahooapis.com/fantasy/v2"
    LEAGUE_ID = "3890"

    def __init__(self):
        self.oauth = OAuth2(None, None, from_file="../../oauth_keys.json")
        if not self.oauth.token_is_valid():
            self.oauth.refresh_access_token()

        self.game_id = self._get_game_id()

    def _make_request_to_yahoo(self, endpoint: str) -> dict:
        """Helper function for making get requests to the Yahoo Fantasy API

        :param endpoint: The endpoint from which you want to retrieve data
        :return: The data from your request
        """
        response = self.oauth.session.get(
            url=f"{self.YAHOO_API_URL}/{endpoint}",
            params={"format": "json"}
        )
        data = response.json().get("fantasy_content")
        if not data:
            raise Exception(f"Unable to retrieve data from Yahoo because: {data}")
        else:
            return data

    def _get_game_id(self) -> str:
        """Get the Yahoo game ID

        Game here means Fantasy Basketball, for example, and does not refer to an actual NBA game

        :return: The game ID
        """
        data = self._make_request_to_yahoo("game/nba")
        return data["game"][0]["game_id"]

    @staticmethod
    def _get_team_info(team_dict: Dict) -> Dict[str, str]:
        """Get the team ID, team name, and manager from the data returned by the teams endpoint

        :param team_dict: The dict containing all the information about the fantasy team
        :return: A dict with the team_id, team_name, and manager name
        """
        team_id = team_dict[1]["team_id"]
        team_name = team_dict[2]["name"]
        manager = team_dict[19]["managers"][0]["manager"]["nickname"]
        return {
            "team_id": team_id,
            "team_name": team_name,
            "manager": manager
        }

    @staticmethod
    def _get_player_ids_for_roster(team_id: str, roster_dict: Dict) -> List[Dict[str, str]]:
        """Extract the player IDs from the roster of a single team

        :param team_id: The ID of the team on which the players are rostered
        :param roster_dict: The dict containing the team's roster
        :return: A list of dicts that represents the team's roster. Looks like:
            [
                {"team_id": "1", "player_id": "123"},
                {"team_id": "1", "player_id": "456"},
                ...
            ]
        """
        roster_dict.pop("count")
        roster = []
        for _, player in roster_dict.items():
            player_id = player["player"][0][1]["player_id"]
            roster.append({
                "team_id": team_id,
                "player_id": player_id
            })

        return roster

    def get_teams_and_rosters(self) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """Get the Fantasy Teams and their rosters from the Yahoo Fantasy API Teams endpoint

        :return: Two lists of dicts, one for the teams and one for the rosters.
            The teams list looks like:
                [
                    {"team_id": "1", "team_name": "Jo Quinoa", "manager": "Joakim"},
                    {"team_id": "2", "team_name": "Comin' Up Rose's", "manager": "Derrick"},
                    ...
                ]
            And the rosters list looks like:
                [
                    {"team_id": "1", "player_id": "123"},
                    {"team_id": "1", "player_id": "456"},
                    ...
                    {"team_id": "2", "player_id": "987"},
                    {"team_id": "2", "player_id": "654"},
                    ...
                ]
        """
        data = self._make_request_to_yahoo(f"league/{self.game_id}.l.{self.LEAGUE_ID}/teams/players")
        teams_dict = data["league"][1]["teams"]
        # keeping this key in the dict messes up the loop below, and we don't need it anyway
        teams_dict.pop("count")

        teams = []
        rosters = []
        for _, team in teams_dict.items():
            # the data structure from the API is very strange, hence all this un-nesting
            team_dict = team["team"][0]
            team_info = self._get_team_info(team_dict)
            roster_dict = team["team"][1]["players"]

            team_id = team_info["team_id"]
            roster_info = self._get_player_ids_for_roster(team_id, roster_dict)

            teams.append(team_info)
            rosters.extend(roster_info)

        return teams, rosters


def main():
    yahoo_tool = YahooFantasyApiTool()
    teams, rosters = yahoo_tool.get_teams_and_rosters()
    print(teams)
    for player in rosters:
        print(player)

# def main():
#     oauth = OAuth2(None, None, from_file="../../oauth_keys.json")
#     if not oauth.token_is_valid():
#         oauth.refresh_access_token()
#
#     response = oauth.session.get(
#         url=f"{YAHOO_API_URL}/game/nba",
#         params={"format": "json"},
#     )
#     # "Game" here means like Fantasy Basketball, not an individual NBA game
#     game_id = response.json()["fantasy_content"]["game"][0]["game_id"]
#
#     response = oauth.session.get(
#         url=f"{YAHOO_API_URL}/league/{game_id}.l.{LEAGUE_ID}/teams",
#         params={"format": "json"},
#     )
#     teams = response.json()["fantasy_content"]["league"][1]["teams"]
#
#     response = oauth.session.get(
#         url=f"{YAHOO_API_URL}/league/{game_id}.l.{LEAGUE_ID}/players",
#         params={"format": "json"}
#     )
#     players = response.json()["fantasy_content"]["league"][1]["players"]
#     for i, player_struct in players.items():
#         player = player_struct["player"][0]
#         player_key = player[0]["player_key"]
#
#         response = oauth.session.get(
#             # url=f"{YAHOO_API_URL}/league/{game_id}.l.{LEAGUE_ID}/players;player_keys={player_key}/stats",
#             url=f"{YAHOO_API_URL}/player/{player_key}/stats",
#             params={"format": "json"}
#         )
#         player_stats = response.json()["fantasy_content"]["player"][1]["player_stats"]
#         break
#
#     response = oauth.session.get(
#         url=f"{YAHOO_API_URL}/game/nba/stat_categories",
#         params={"format": "json"}
#     )
#     stat_categories = response.json()["fantasy_content"]["game"][1]["stat_categories"]["stats"]
#     for stat in stat_categories:
#         print(stat["stat"]["stat_id"], stat["stat"]["name"])


if __name__ == "__main__":
    main()
