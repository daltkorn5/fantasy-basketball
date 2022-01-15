from typing import List, Dict, Any

from pandas import DataFrame
from prophet import Prophet
import datetime
import pandas as pd

from src.utils.output_suppressor import OutputSuppressor
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

    def _get_player_statistics(self, week_no: int) -> List[Dict[str, Any]]:
        """Get the statistics for each player in the matchup

        :param week_no: The week_no of the season. Used to determine who the opposing team is and the
            number of games each player has
        :return: The list of players who will be participating in the matchup, along with their relevant statistics.
            Each row is a single game log for a single player
        """
        query = (
            "WITH participating_teams AS (SELECT team_id from match_ups where week_no = %(week_no)s "
            "UNION ALL SELECT team_id from teams where manager = 'Danny'), "
            "game_count AS (SELECT nba_team_id, count as num_games FROM game_count_per_team_per_week "
            "WHERE week_no = %(week_no)s) "
            "SELECT player_name, team_name, game_count.num_games, status, game_date, field_goals, field_goal_attempts, "
            "free_throws, free_throw_attempts, three_pointers, points, rebounds, assists, steals, blocks, turnovers "
            "FROM game_log "
            "JOIN players using (player_id) "
            "JOIN rosters using (player_id) "
            "JOIN teams using (team_id) "
            "JOIN game_count game_count using (nba_team_id) "
            "WHERE rosters.team_id in (SELECT team_id from participating_teams) "
            "AND status IS DISTINCT FROM 'INJ';"
        )
        return self.query_tool.select(query, {"week_no": week_no})

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

            player_dict[team_name][player_name].setdefault("game_logs", [])
            player_dict[team_name][player_name]["game_logs"].append(
                {k: v for k, v in row.items() if k not in ("player_name", "num_games", "status", "team_name")}
            )

        return player_dict

    @staticmethod
    def _project_stat(stats_df: DataFrame, num_games: int) -> float:
        """Project a single stat for `num_games` more games

        :param stats_df: A dataframe containing just two fields: game_date and the statistic you want to project
        :param num_games: The number of games for which you want to project the statistic
        :return: The total of the statistic that the player is projected to have in the matchup.
            For example, a player could be projected to get 62 points over three games
        """
        # this is what Prophet needs the columns to be called
        stats_df.columns = ["ds", "y"]
        with OutputSuppressor():
            model = Prophet()
            model.fit(stats_df)
            future = model.make_future_dataframe(periods=num_games)
            forecast = model.predict(future)

        return sum(max(float(val), 0) for val in forecast[["yhat"]].tail(num_games).values)

    def _project_players(self, players: Dict[str, Any]) -> None:
        """Project all the stats for all the players

        :param players: The list of players whose stats you are projecting
        """
        for player, data in players.items():
            data["projections"] = {}
            stats_df = pd.DataFrame(data["game_logs"])

            stats_to_project = [stat for stat in stats_df.columns if stat != "game_date"]
            for stat in stats_to_project:
                projection = self._project_stat(stats_df[["game_date", stat]], data["num_games"])

                data["projections"][stat] = projection

    @staticmethod
    def _get_totals(players: Dict[str, Any]) -> Dict[str, float]:
        """Get the projected totals for each stat for the provided list of players

        :param players: The players for a single fantasy team
        :return: A dict containing the totals for each stat, as well as field goal and free throw percentages
        """
        totals = {"num_games": 0}
        for player, data in players.items():
            projections = data["projections"]
            totals["num_games"] += data["num_games"]
            for stat, projection in projections.items():
                totals.setdefault(stat, 0.0)
                totals[stat] += projection

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
        statistics = self._get_player_statistics(week_no)
        player_dict = self._make_player_dict(statistics)
        for team, players in player_dict.items():
            print(team)
            self._project_players(players)
            totals = self._get_totals(players)
            print(totals)


if __name__ == "__main__":
    matchup_projector = MatchupProjector()
    matchup_projector.project_matchups()
