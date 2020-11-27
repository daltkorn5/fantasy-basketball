#!/Users/daltkorn5/compsci/anaconda3/bin/python
"""Script to pick a fantasy basketball team using mixed integer linear programming.

The list of available players is first queried from a PostgreSQL database. Then for each player
the counting statistics are normalized so that a "relative value" of each player can be determined.
As of now, the relative value is equal to the sum of the normalized values of all the statistics,
except for salary and turnovers are both subtracted from the total. We subtract turnovers because we want to
minimize those as much as possible (effectively giving them a weight of -1), and we subtract salary because we
want to value the players with a lower salary higher.

The team is then chosen based on some position constraints, a 12-player limit, and a "salary cap,"
and the chosen players are printed out at the end.
"""
import src.query_tool as query_tool
from mip import *

non_counting_stats = ('player_name', 'position', 'team')


def get_players():
    query = """
    select
        player_name,
        position,
        p.team,
        field_goal_percentage,
        free_throw_percentage,
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


def get_extrema(players):
    """Function to get the maximum and minimum values of each counting statistic.
    :param players: The list of players
    :return: A dict with each statistic and its maximum and minimum values. For example:
        {
            'points': {
                'min_val': 1.0,
                'max_val': 2500.0
            },
            'rebounds': {
                'min_val': 0.0,
                'max_val': 1000.0
            }
        }
    """
    extrema = {k: {'min_val': 0.0, 'max_val': 0.0} for k in players[0].keys() if k not in non_counting_stats}
    for player in players:
        for stat, value in player.items():
            if stat in non_counting_stats:
                continue

            if value < extrema[stat]['min_val']:
                extrema[stat]['min_val'] = value

            if value > extrema[stat]['max_val']:
                extrema[stat]['max_val'] = value
    return extrema


def normalize(value, min_val, max_val):
    """Function to return the normalized value of a statistic.
    The normalized value is defined as:
        (x - x_min) / (x_max - x_min)
    :param value: The value being normalized
    :param min_val: The minimum value of the corresponding statistic amongst all players
    :param max_val: The maximum value of the corresponding statistic amongst all players
    :return: The normalized value
    """
    return (value - min_val) / (max_val - min_val)


def normalize_stats(players):
    """Function to normalized all the counting statistics associated with each player.

    Salary is not normalized because we need the original salary values in order to meet our salary cap
    constraint. So in addition to salary we include a new 'normalized_salary' field
    :param players: The list of players whose stats are being normalized

    Does not return anything but modifies the player list
    """
    extrema = get_extrema(players)
    for player in players:
        for stat, value in player.items():
            if stat in non_counting_stats or stat == 'salary':
                continue

            player[stat] = normalize(value, **extrema[stat])

        player['normalized_salary'] = normalize(player['salary'], **extrema['salary'])


def get_relative_value(players):
    """Function to calculate the relative value of each player.

    Relative value is defined as the sum of all the normalized counting statistics, except for
    turnovers and normalized_salary are subtracted from the total. In other words:

    relative_value = points + three_pointers + ... + steals - turnovers - normalized_salary
    :param players: The list of players

    Does not return anything, but modifies the players list, adding a "relative_value" attribute
    to each player
    """
    for player in players:
        total = 0.0
        for stat, value in player.items():
            if stat in non_counting_stats or stat == 'salary':
                continue
            elif stat in ('turnovers', 'normalized_salary'):
                total -= value
            else:
                total += value

        player['relative_value'] = total


def pick_players(players):
    """Function to determine which players you should pick for your fantasy basketball team!

    Sets up the optimization model with salary-cap, position, and team-size constraints and determines
    the best 12 players based on 'relative_value' that fit the constraints

    :param players: The list of players
    :return: Your fantasy basketball team!
    """
    normalize_stats(players)
    get_relative_value(players)

    m = Model(sense=MAXIMIZE)
    x = [m.add_var(var_type=BINARY) for _ in range(len(players))]

    # salary cap constraint
    m += xsum(players[i]['salary'] * x[i] for i in range(len(players))) <= 140000000
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
    team_members = pick_players(players)
    for player in sorted(team_members, key=lambda p: p['relative_value'], reverse=True):
        print(player)


if __name__ == '__main__':
    main()
