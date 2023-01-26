from typing import List, Dict, Any, Optional

from pandas import DataFrame
import datetime
import pandas as pd

from src.utils.query_tool import QueryTool


class MatchupProjector:
    def __init__(self):
        self.query_tool = QueryTool()

    def _get_week_no(self) -> int:
        """Get the week_no of *next week's matchup*

        Only run if the week number isn't provided by the user
        """
        query = "SELECT week_no from match_ups where %(dte)s between week_start and week_end"
        result = self.query_tool.select(query, {"dte": datetime.date.today() + datetime.timedelta(weeks=1)})
        return result[0]["week_no"]

    def _get_player_statistics(
        self,
        week_no: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get the statistics for each player in the matchup

        :param week_no: The week_no of the season. Used to determine who the opposing team is and the
            number of games each player has
        :param start_date:
        :param end_date:
        :return: The list of players who will be participating in the matchup, along with their relevant statistics.
            Each row is a single game log for a single player
        """
        if start_date and end_date:
            date_filter = "AND game_log.game_date BETWEEN %(start_date)s::DATE and %(end_date)s::DATE "

        else:
            date_filter = "AND game_log.game_date BETWEEN (SELECT get_season_start()) AND (SELECT get_season_end()) "

        query = (
            "WITH participating_teams AS (SELECT team_id from match_ups where week_no = %(week_no)s "
            "UNION ALL SELECT team_id from teams where manager = 'Danny'), "
            "game_count AS (SELECT nba_team_id, count as num_games FROM game_count_per_team_per_week "
            "WHERE week_no = %(week_no)s) "
            "SELECT player_name, team_name, game_count.num_games, status, "
            "AVG(field_goals) AS field_goals, AVG(field_goal_attempts) AS field_goal_attempts, "
            "AVG(free_throws) as free_throws, AVG(free_throw_attempts) as free_throw_attempts, "
            "AVG(three_pointers) AS three_pointers, AVG(points) AS points, "
            "AVG(rebounds) as rebounds, AVG(assists) AS assists, AVG(steals) as steals, "
            "AVG(blocks) as blocks, AVG(turnovers) as turnovers "
            "FROM game_log "
            "JOIN players using (player_id) "
            "JOIN rosters using (player_id) "
            "JOIN teams using (team_id) "
            "JOIN game_count game_count using (nba_team_id) "
            "WHERE rosters.team_id in (SELECT team_id from participating_teams) "
            f"{date_filter}"
            "AND status IS DISTINCT FROM 'INJ' "
            "GROUP BY player_name, team_name, num_games, status;"
        )
        return self.query_tool.select(query, {"week_no": week_no, "start_date": start_date, "end_date": end_date})

    @staticmethod
    def _make_player_dict(statistics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Take the list of rows from the database and turn it into a dict organized by team and player

        :param statistics: The list of players and their statistics
        :return: A dict containing all the players. Looks like:
            {
                "Fantasy Team 1": {
                    "Michael Jordan": {
                        "num_games": 4,  # this is the number of games the player is playing in the week you're checking
                        "status": None,
                        "game_logs": [
                            {
                                "field_goals": 12,
                                "field_goal_attempts": 16,
                                "free_throws": 7,
                                "free_throw_attempts": 8,
                                "three_pointers": 2,
                                "points": 33,
                                "rebounds": 6,
                                "assists": 5,
                                "steals": 2,
                                "blocks": 0,
                                "turnovers": 4
                            },
                            ...
                        ]
                    },
                    "Scottie Pippen: {
                        ...
                    },
                    ...
                },
                "Fantasy Team 2": {
                    ...
                }
            }
        """
        player_dict = {}
        for row in statistics:
            team_name = row["team_name"]
            player_dict.setdefault(team_name, {})
            player_name = row["player_name"]
            player_dict[team_name].setdefault(player_name, {})

            player_dict[team_name][player_name]["num_games"] = row["num_games"]
            player_dict[team_name][player_name]["status"] = row["status"]

            player_dict[team_name][player_name].setdefault("stats", {})
            player_dict[team_name][player_name]["stats"] = (
                {k: v for k, v in row.items() if k not in ("player_name", "num_games", "status", "team_name")}
            )

        return player_dict

    @staticmethod
    def _get_totals(players: Dict[str, Any]) -> Dict[str, float]:
        """Get the projected totals for each stat for the provided list of players

        :param players: The players for a single fantasy team
        :return: A dict containing the totals for each stat, as well as field goal and free throw percentages
        """
        totals = {"num_games": 0}
        for player, data in players.items():
            stats = data["stats"]
            num_games = data["num_games"]
            totals["num_games"] += num_games
            for stat, average in stats.items():
                totals.setdefault(stat, 0.0)
                totals[stat] += float(average) * num_games

        totals["field_goal_percentage"] = totals["field_goals"] / totals["field_goal_attempts"]
        totals["free_throw_percentage"] = totals["free_throws"] / totals["free_throw_attempts"]

        for stat, total in totals.items():
            totals[stat] = round(total, 2)
        return totals

    def project_matchups(self, week_no: int = None) -> None:
        """Project a Fantasy matchup

        :param week_no: Optional week number whose matchup you want to project.
            If not provided, will project next week's matchup
        """
        if not week_no:
            week_no = self._get_week_no()
        statistics = self._get_player_statistics(week_no, start_date="2023-01-01", end_date="2023-03-01")
        player_dict = self._make_player_dict(statistics)
        for team, players in player_dict.items():
            print(team)
            totals = self._get_totals(players)
            print(totals)


if __name__ == "__main__":
    matchup_projector = MatchupProjector()
    matchup_projector.project_matchups()
