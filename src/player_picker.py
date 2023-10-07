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

from mip import *

from typing import Dict, Any, List
from src.utils.player_evaluator import PlayerEvaluator

SALARY_CAP = 173_000_000


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
    weights = {
        'field_goal_percentage': 1.0,
        'free_throw_percentage': 0.0,
        'three_pointers': 0.0,
        'points': 1.0,
        'rebounds': 1.0,
        'assists': 1.0,
        'steals': 1.0,
        'blocks': 1.0,
        'turnovers': -1.0
    }
    player_evaluator = PlayerEvaluator(weights=weights)
    players = player_evaluator.evaluate_players(
        start_date="2022-10-01",
        end_date="2023-06-30"
    )
    team_members = pick_players(players)

    print(f"Your total salary is: {sum(p['salary'] for p in team_members)}")
    for player in sorted(team_members, key=lambda p: p['relative_value'], reverse=True):
        print(player)

    print()
    for player in sorted(players, key=lambda p: p['relative_value'], reverse=True)[:20]:
        print(player)


if __name__ == '__main__':
    main()
