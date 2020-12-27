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
import src.query_tool as query_tool
from mip import *

NON_COUNTING_STATS = ('player_name', 'position', 'team')
# We want to keep these separate so that we don't normalize them.
# Their raw values will be used to compute the final value of their respective
# percentage stats
ATTEMPT_STATS = ('field_goal_attempts', 'free_throw_attempts')

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


def get_players():
    query = """
    select
        player_name,
        position,
        p.team,
        case
            when field_goal_attempts = 0 then 0.0
            else (field_goals::real / field_goal_attempts::real)
        end as field_goal_percentage,
        field_goal_attempts,
        case
            when free_throw_attempts = 0 then 0.0
            else (free_throws::real / free_throw_attempts::real)
        end as free_throw_percentage,
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


def get_means_and_std_devs(players, stats=None):
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
    if stats is None:
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


def normalize(value, mean, std_dev):
    """Function to return the normalized value of a statistic.

    Here we are defining "normalized" as a z-score, calculated as:
    (x - mean) / std_dev

    :param value: The value being normalized
    :param mean: The mean of the corresponding statistic amongst all players
    :param std_dev: The standard_deviation of the corresponding statistic amongst all players
    :return: The normalized value
    """
    return (value - mean) / std_dev


def normalize_stats(players):
    """Function to normalized all the counting statistics associated with each player.

    Salary is not normalized because we need the original salary values in order to meet our salary cap
    constraint.
    :param players: The list of players whose stats are being normalized

    Does not return anything but modifies the player list
    """
    means_and_std_devs = get_means_and_std_devs(players)
    for player in players:
        for stat, value in player.items():
            if stat in NON_COUNTING_STATS or stat == 'salary' or stat in ATTEMPT_STATS:
                continue

            player[stat] = normalize(value, **means_and_std_devs[stat])


def get_relative_value_for_percentage_stats(players):
    """Function to get the relative value for the percentage stats (FG% and FT%).

    The reason we can't just use a normal z-score for the percentage stats is because we want to
    take the number of attempts into account. A player who makes 900/1000 free throws is worth more
    to your team than one who makes 9/10. To account for that, we first calculate "unweighted" z-score
    of the percentage fields, to see what the league average. We then "weight" that z-score by multiplying it
    by the respective attempts field, then re-calculate the z-score of this product. The final value is then
    multiplied by its weight and added to the player's relative value.

    Please note that the setup for this function must be done prior to calling it. The players list passed
    to this function should already have the percentage z-scores * attempts computed

    :param players: The list of players. Again, they should already have their percentage z-score * attempts
        applied

    Does not return anything, but calculates the final z-scores of the percentage fields and adds them to the
    player's relative value.
    """
    percentage_stats = ('free_throw_percentage', 'field_goal_percentage')
    means_and_std_devs = get_means_and_std_devs(players, stats=percentage_stats)
    for player in players:
        for stat in percentage_stats:
            player[stat] = normalize(player[stat], **means_and_std_devs[stat])
            player['relative_value'] += player[stat] * WEIGHTS.get(stat, 0.0)


def get_relative_value(players):
    """Function to calculate the relative value of each player.

    Relative value is calculated as the sum of the z-scores of the stats multiplied by their respective weights,
    where the weights are defined in a global variable at the top of the file.

    :param players: The list of players

    Does not return anything, but modifies the players list, adding a "relative_value" attribute
    to each player
    """
    stats_to_skip = NON_COUNTING_STATS + ATTEMPT_STATS + ('salary', 'free_throw_percentage', 'field_goal_percentage')
    for player in players:
        total = 0.0
        for stat, value in player.items():
            weight = WEIGHTS.get(stat, 0.0)
            if stat in stats_to_skip:
                continue
            else:
                total += value * weight

        player['relative_value'] = total

        # Here we're setting up the process to weight the percentage statistics based on the volume of attempts
        # associated with them
        player['field_goal_percentage'] = player['field_goal_percentage'] * player['field_goal_attempts']
        player['free_throw_percentage'] = player['free_throw_percentage'] * player['free_throw_attempts']

    get_relative_value_for_percentage_stats(players)


def pick_players(players):
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
