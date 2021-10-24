#!/Users/daltkorn5/compsci/anaconda3/bin/python
"""Script to pick a fantasy basketball team using mixed integer linear programming.

The list of available players is first queried from a PostgreSQL database. Then for each player
the counting statistics are normalized so that a "relative value" of each player can be determined.
As of now, the relative value is equal to the sum of the z-scores of all the statistics,
except for turnovers which are subtracted from the total. We subtract turnovers because we want to
minimize those as much as possible (effectively giving them a weight of -1).

The team is then chosen based on some position constraints, a 12-player limit, and a "salary cap,"
and the chosen players are printed out at the end.
"""
from typing import Dict, Any, Union

import src.query_tool as query_tool
from mip import *

NON_COUNTING_STATS = ('player_name', 'position', 'team')

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

SALARY_CAP = 140000000


def get_players() -> List[Dict[str, Any]]:
    """Run a query to get the players list

    :return: A list of dicts, where each dict corresponds to a single player
    """
    query = """
    select
        player_name,
        position,
        p.team,
        field_goals,
        field_goal_attempts,
        free_throws,
        free_throw_attempts,
        three_pointers,
        points,
        rebounds,
        assists,
        steals,
        blocks,
        turnovers,
        salary
    from players p
    inner join salaries using (player_name)
    where
        is_available
    ;
    """
    return [dict(row) for row in query_tool.select(query)]


def get_average_percentage_stats() -> Dict[str, Union[int, float]]:
    """Run a query to get the team-level average percentage statistics

    The sums of the fields are divided by 30 because there are 30 teams in the
    NBA. So to get our average percentage statistic for the whole league we're looking
    at the average makes/attempts per team

    :return: A dict that contains the averages calculated in the query
    """
    query = """
    with averages as (
        select
            sum(field_goals) / 30 as avg_field_goals,
            sum(field_goal_attempts) / 30 as avg_field_goal_attempts,
            sum(free_throws) / 30 as avg_free_throws,
            sum(free_throw_attempts) / 30 as avg_free_throw_attempts
        from
            players
    )
    select
        avg_field_goals,
        avg_field_goal_attempts,
        avg_field_goals::real / avg_field_goal_attempts::real as avg_field_goal_percentage,
        avg_free_throws,
        avg_free_throw_attempts,
        avg_free_throws::real / avg_free_throw_attempts::real as avg_free_throw_percentage
    from
        averages
    """
    return [dict(row) for row in query_tool.select(query)][0]


def percent_change(original: Union[int, float], new: Union[int, float]) -> float:
    """Function to get the percent change between two values

    :param original: The original value
    :param new: The new value
    :return: The percent change between the new value and the original value
    """
    return (new - original) / abs(original)


def calculate_percentage_impacts(players: List[Dict[str, Any]]) -> None:
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
    averages = get_average_percentage_stats()
    for player in players:
        field_goals = player['field_goals']
        field_goal_attempts = player['field_goal_attempts']
        adjusted_fg_percentage = (
            (field_goals + averages["avg_field_goals"]) /
            (field_goal_attempts + averages["avg_field_goal_attempts"])
        )
        fg_impact = percent_change(averages["avg_field_goal_percentage"], adjusted_fg_percentage)

        player["field_goal_percentage"] = fg_impact

        free_throws = player['free_throws']
        free_throw_attempts = player['free_throw_attempts']
        adjusted_ft_percentage = (
            (free_throws + averages["avg_free_throws"]) /
            (free_throw_attempts + averages["avg_free_throw_attempts"])
        )
        ft_impact = percent_change(averages["avg_free_throw_percentage"], adjusted_ft_percentage)

        player["free_throw_percentage"] = ft_impact

        # Don't need these anymore because our percentage impact values will be used from now on
        [player.pop(key) for key in ("field_goals", "field_goal_attempts", "free_throws", "free_throw_attempts")]


def get_means_and_std_devs(players: List[Dict[str, Any]]) -> Dict[str, Dict]:
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
                          for field in stats if field not in NON_COUNTING_STATS}
    for field in means_and_std_devs.keys():
        # so for example this would be a list of every player's point total
        whole_leagues_stat = [p[field] for p in players]
        # we then calculate the league mean points scored
        mean = sum(whole_leagues_stat) / len(whole_leagues_stat)
        # and the variance
        variance = sum([((x - mean) ** 2) for x in whole_leagues_stat]) / len(whole_leagues_stat)
        std_dev = variance ** 0.5

        means_and_std_devs[field]['mean'] = mean
        means_and_std_devs[field]['std_dev'] = std_dev

    return means_and_std_devs


def normalize(value: Union[int, float], mean: float, std_dev: float) -> float:
    """Function to return the normalized value of a statistic.

    Here we are defining "normalized" as a z-score, calculated as:
    (x - mean) / std_dev

    :param value: The value being normalized
    :param mean: The mean of the corresponding statistic amongst all players
    :param std_dev: The standard_deviation of the corresponding statistic amongst all players
    :return: The normalized value
    """
    return (value - mean) / std_dev


def normalize_stats(players: List[Dict[str, Any]]) -> None:
    """Function to normalized all the counting statistics associated with each player.

    Salary is not normalized because we need the original salary values in order to meet our salary cap
    constraint.
    :param players: The list of players whose stats are being normalized

    Does not return anything but modifies the player list
    """
    means_and_std_devs = get_means_and_std_devs(players)
    for player in players:
        for stat, value in player.items():
            if stat in NON_COUNTING_STATS or stat == 'salary':
                continue

            player[stat] = normalize(value, **means_and_std_devs[stat])


def get_relative_value(players: List[Dict[str, Any]]) -> None:
    """Function to calculate the relative value of each player.

    Relative value is calculated as the sum of the z-scores of the stats multiplied by their respective weights,
    where the weights are defined in a global variable at the top of the file.

    :param players: The list of players

    Does not return anything, but modifies the players list, adding a "relative_value" attribute
    to each player
    """
    stats_to_skip = NON_COUNTING_STATS + ('salary',)
    for player in players:
        total = 0.0
        for stat, value in player.items():
            weight = WEIGHTS.get(stat, 0.0)
            if stat in stats_to_skip:
                continue
            else:
                total += value * weight

        player['relative_value'] = total


def pick_players(players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Function to determine which players you should pick for your fantasy basketball team!

    Sets up the optimization model with salary-cap, position, and team-size constraints and determines
    the best 12 players based on 'relative_value' that fit the constraints

    :param players: The list of players
    :return: Your fantasy basketball team!
    """

    m = Model(sense=MAXIMIZE)
    x = [m.add_var(var_type=BINARY) for _ in range(len(players))]

    # salary cap constraint
    m += xsum(players[i]['salary'] * x[i] for i in range(len(players))) <= SALARY_CAP
    # 12 players on the team constraint
    m += xsum(1 * x[i] for i in range(len(players))) == 12

    # We can have between 1 and 6 point/shooting guards (PG/SG, G, Util, Util, Bench, Bench)
    # but I want at least 2 of each position for roster flexibility
    m += xsum(('PG' in players[i]['position']) * x[i] for i in range(len(players))) >= 2
    m += xsum(('PG' in players[i]['position']) * x[i] for i in range(len(players))) <= 6

    m += xsum(('SG' in players[i]['position']) * x[i] for i in range(len(players))) >= 2
    m += xsum(('SG' in players[i]['position']) * x[i] for i in range(len(players))) <= 6

    # Same for small/power forwards
    m += xsum(('SF' in players[i]['position']) * x[i] for i in range(len(players))) >= 2
    m += xsum(('SF' in players[i]['position']) * x[i] for i in range(len(players))) <= 6

    m += xsum(('PF' in players[i]['position']) * x[i] for i in range(len(players))) >= 2
    m += xsum(('PF' in players[i]['position']) * x[i] for i in range(len(players))) <= 6

    # We can have between 2 and 6 centers, but I want at least three for more roster flexibility
    m += xsum(('C' in players[i]['position']) * x[i] for i in range(len(players))) >= 3
    m += xsum(('C' in players[i]['position']) * x[i] for i in range(len(players))) <= 6

    m.objective = xsum(players[i]['relative_value'] * x[i] for i in range(len(players)))
    m.optimize()

    team_members = []
    for i, var in enumerate(m.vars):
        if round(var.x, 2) == 1.0:
            team_members.append(players[i])

    return team_members


def main():
    players = get_players()
    calculate_percentage_impacts(players)
    normalize_stats(players)
    get_relative_value(players)
    team_members = pick_players(players)

    print(f"Your total salary is: {sum(p['salary'] for p in team_members)}")
    for player in sorted(team_members, key=lambda p: p['relative_value'], reverse=True):
        print(player)

    print()
    for player in sorted(players, key=lambda p: p['relative_value'], reverse=True)[:20]:
        print(player)


if __name__ == '__main__':
    main()
