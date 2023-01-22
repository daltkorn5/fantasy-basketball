from typing import List, Dict, Any, Union, Optional

from src.utils.query_tool import QueryTool


class PlayerEvaluator:
    """This class evaluates all the players based on their stat totals.

    A player's relative value is determined by calculating the z-score for each of their statistics,
    multiplying each z-score by a configurable weight (if you want to weight certain stats more or less than others),
    then summing those values.
    """

    NON_COUNTING_STATS = ("player_name", "positions", "team_code", "status", "fantasy_team", "salary", "manager")

    WEIGHTS = {
        'field_goal_percentage': 1.0,
        'free_throw_percentage': 1.0,
        'three_pointers': 1.0,
        'points': 1.0,
        'rebounds': 1.0,
        'assists': 1.0,
        'steals': 1.0,
        'blocks': 1.0,
        'turnovers': -1.0
    }

    def __init__(self, weights: Dict[str, float] = None):
        """Instantiate a PlayerEvaluator

        :param weights: The weights you want to apply to each stat. If not supplied, defaults to 1.0 for everything
            except turnovers. Turnovers get a -1.0 weight (because more turnovers is bad!)
        """
        self.query_tool = QueryTool()
        self.weights = weights or self.WEIGHTS

    def _get_players_totals(
            self,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Load all the players and their statistics from the database

        :param start_date: The lower bound for game_date for the query
        :param end_date: The upper bound for game_date for the query
        :return: A list of all the players and their stat totals
        """
        where_clause = ""
        if start_date and end_date:
            where_clause = f" WHERE game_log.game_date BETWEEN '{start_date}'::DATE AND '{end_date}'::DATE "
        query = (
            "SELECT player_name, team_code, ARRAY_TO_STRING(positions, ',') as positions, status, COALESCE(salary, 0) as salary, "
            "SUM(field_goals) AS field_goals, SUM(field_goal_attempts) AS field_goal_attempts, "
            "SUM(free_throws) as free_throws, SUM(free_throw_attempts) as free_throw_attempts, "
            "SUM(three_pointers) AS three_pointers, SUM(points) AS points, "
            "SUM(rebounds) as rebounds, SUM(assists) AS assists, SUM(steals) as steals, "
            "SUM(blocks) as blocks, SUM(turnovers) as turnovers, fantasy_teams.team_name AS fantasy_team, "
            "fantasy_teams.manager "
            "FROM players "
            "JOIN game_log USING (player_id) "
            "JOIN nba_teams USING (nba_team_id) "
            "LEFT JOIN rosters USING (player_id) "
            "LEFT JOIN teams AS fantasy_teams USING (team_id)"
            f"{where_clause}"
            "GROUP BY player_name, team_code, positions, status, salary, fantasy_team, manager;"
        )
        return self.query_tool.select(query)

    def _get_players_averages(
            self,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Load all the players and their statistics from the database

        :param start_date: The lower bound for game_date for the query
        :param end_date: The upper bound for game_date for the query
        :return: A list of all the players and their stat totals
        """
        where_clause = ""
        if start_date and end_date:
            where_clause = f" WHERE game_log.game_date BETWEEN '{start_date}'::DATE AND '{end_date}'::DATE "
        query = (
            "SELECT player_name, team_code, ARRAY_TO_STRING(positions, ',') as positions, status, COALESCE(salary, 0) as salary, "
            "AVG(field_goals) AS field_goals, AVG(field_goal_attempts) AS field_goal_attempts, "
            "AVG(free_throws) as free_throws, AVG(free_throw_attempts) as free_throw_attempts, "
            "AVG(three_pointers) AS three_pointers, AVG(points) AS points, "
            "AVG(rebounds) as rebounds, AVG(assists) AS assists, AVG(steals) as steals, "
            "AVG(blocks) as blocks, AVG(turnovers) as turnovers, fantasy_teams.team_name AS fantasy_team, "
            "fantasy_teams.manager "
            "FROM players "
            "JOIN game_log USING (player_id) "
            "JOIN nba_teams USING (nba_team_id) "
            "LEFT JOIN rosters USING (player_id) "
            "LEFT JOIN teams AS fantasy_teams USING (team_id)"
            f"{where_clause}"
            "GROUP BY player_name, team_code, positions, status, salary, fantasy_team, manager;"
        )
        return self.query_tool.select(query)

    def _get_average_percentage_stats(self) -> Dict[str, Union[int, float]]:
        """Run a query to get the team-level average percentage statistics

        The sums of the fields are divided by 30 because there are 30 teams in the
        NBA. So to get our average percentage statistic for the whole league we're looking
        at the average makes/attempts per team

        :return: A dict that contains the averages calculated in the query
        """
        query = (
            "WITH averages AS (SELECT SUM(field_goals) / 30 AS avg_field_goals, "
            "SUM(field_goal_attempts) / 30 AS avg_field_goal_attempts, "
            "SUM(free_throws) / 30 AS avg_free_throws, "
            "SUM(free_throw_attempts) / 30 AS avg_free_throw_attempts "
            "FROM player_stat_totals) "
            "SELECT avg_field_goals, avg_field_goal_attempts, "
            "avg_field_goals::real / avg_field_goal_attempts::real as avg_field_goal_percentage, "
            "avg_free_throws, avg_free_throw_attempts, "
            "avg_free_throws::real / avg_free_throw_attempts::real as avg_free_throw_percentage "
            "FROM averages;"
        )

        return self.query_tool.select(query)[0]

    @staticmethod
    def _percent_change(original: Union[int, float], new: Union[int, float]) -> float:
        """Function to get the percent change between two values

        :param original: The original value
        :param new: The new value
        :return: The percent change between the new value and the original value
        """
        return (float(new) - original) / abs(original)

    def _calculate_percentage_impacts(self, players: List[Dict[str, Any]]) -> None:
        """Calculates the "impacts" each player has on percentage statistics.

        The idea here is that first we get our per-team averages for, for example,
        field goals, field goal attempts, and field goal percentage. Then for each player
        we see how they would impact those per-team averages by adding their field goals to the
        per-team field goal average, their field goal attempts to the per-team field goal attempts
        average, getting that field goal new percentage, then calculating the percent change
        from the per-team field goal percentage average.

        This makes it so that a player who shoots 60% from the field  on 20 attempts per game
        will have their field goal percentage count more towards the player's relative value
        than a player who shoots 60% on 5 attempts per game.

        :param players: The list of players
        """
        averages = self._get_average_percentage_stats()
        for player in players:
            field_goals = player['field_goals']
            field_goal_attempts = player['field_goal_attempts']
            adjusted_fg_percentage = (
                    (field_goals + averages["avg_field_goals"]) /
                    (field_goal_attempts + averages["avg_field_goal_attempts"])
            )
            fg_impact = self._percent_change(averages["avg_field_goal_percentage"], adjusted_fg_percentage)

            player["field_goal_percentage"] = fg_impact

            free_throws = player['free_throws']
            free_throw_attempts = player['free_throw_attempts']
            adjusted_ft_percentage = (
                    (free_throws + averages["avg_free_throws"]) /
                    (free_throw_attempts + averages["avg_free_throw_attempts"])
            )
            ft_impact = self._percent_change(averages["avg_free_throw_percentage"], adjusted_ft_percentage)

            player["free_throw_percentage"] = ft_impact

            # Don't need these anymore because our percentage impact values will be used from now on
            [player.pop(key) for key in ("field_goals", "field_goal_attempts", "free_throws", "free_throw_attempts")]

    def _get_means_and_std_devs(self, players: List[Dict[str, Any]]) -> Dict[str, Dict]:
        """Function to get the means and standard deviations of each counting statistic
        :param players: The list of players
        :param stats: The list of stats for which you want to calculate the mean/std dev.
            If `None` provided will calculate them for all the fields in a player dict
            (besides those in NON_COUNTING_STATS).
        :return: A dict with each statistic and its mean and standard deviation. For example:
            {
                'points': {
                    'mean': 1.0,
                    'std_dev': 2500.0
                },
                'rebounds': {
                    'mean': 0.0,
                    'std_dev': 1000.0
                }
            }
        """
        stats = players[0].keys()

        means_and_std_devs = {field: {'mean': 0.0, 'std_dev': 0.0}
                              for field in stats if field not in self.NON_COUNTING_STATS}
        for field in means_and_std_devs.keys():
            # so for example this would be a list of every player's point total
            whole_leagues_stat = [p[field] for p in players]
            # we then calculate the league mean points scored
            mean = sum(whole_leagues_stat) / len(whole_leagues_stat)
            # and the variance
            variance = sum([((x - mean) ** 2) for x in whole_leagues_stat]) / len(whole_leagues_stat)
            std_dev = float(variance) ** 0.5

            means_and_std_devs[field]['mean'] = mean
            means_and_std_devs[field]['std_dev'] = std_dev

        return means_and_std_devs

    @staticmethod
    def _normalize(value: Union[int, float], mean: float, std_dev: float) -> float:
        """Function to return the normalized value of a statistic.

        Here we are defining "normalized" as a z-score, calculated as:
        (x - mean) / std_dev

        :param value: The value being normalized
        :param mean: The mean of the corresponding statistic amongst all players
        :param std_dev: The standard_deviation of the corresponding statistic amongst all players
        :return: The normalized value
        """
        return float((value - mean)) / float(std_dev)

    def _normalize_stats(self, players: List[Dict[str, Any]]) -> None:
        """Function to normalized all the counting statistics associated with each player.

        Salary is not normalized because we need the original salary values in order to meet our salary cap
        constraint.
        :param players: The list of players whose stats are being normalized

        Does not return anything but modifies the player list
        """
        means_and_std_devs = self._get_means_and_std_devs(players)
        for player in players:
            for stat, value in player.items():
                if stat in self.NON_COUNTING_STATS:
                    continue

                player[stat] = self._normalize(value, **means_and_std_devs[stat])

    def _get_relative_value(self, players: List[Dict[str, Any]]) -> None:
        """Function to calculate the relative value of each player.

        Relative value is calculated as the sum of the z-scores of the stats multiplied by their respective weights,
        where the weights are defined in a global variable at the top of the file.

        :param players: The list of players

        Does not return anything, but modifies the players list, adding a "relative_value" attribute
        to each player
        """
        stats_to_skip = self.NON_COUNTING_STATS
        for player in players:
            total = 0.0
            for stat, value in player.items():
                weight = self.weights.get(stat, 0.0)
                if stat in stats_to_skip:
                    continue
                else:
                    total += value * weight

            player['relative_value'] = total

    def evaluate_players(
            self,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            use_totals: bool = True
    ) -> List[Dict[str, Any]]:
        """Determine each players relative value

        :param start_date: The start date that will be used to pull the game logs to evaluate the players
        :param end_date: The end date that will be used to pull the game logs to evaluate the players
        :param use_totals: Whether or not you want to evaluate the players based on their stat totals. If false,
            players will be evaluate based on their stat averages
        :return: The list of players with all their counting stats normalized and their relative value calculated
        """
        if use_totals:
            players = self._get_players_totals(
                start_date=start_date,
                end_date=end_date
            )
        else:
            players = self._get_players_averages(
                start_date=start_date,
                end_date=end_date
            )
        self._calculate_percentage_impacts(players)
        self._normalize_stats(players)
        self._get_relative_value(players)

        return players
