from src.utils.player_evaluator import PlayerEvaluator

if __name__ == "__main__":
    weights = {
        'field_goal_percentage': 1.0,
        'free_throw_percentage': 2.0,
        'three_pointers': 0.0,
        'points': 0.0,
        'rebounds': 1.0,
        'assists': 1.0,
        'steals': 2.0,
        'blocks': 1.0,
        'turnovers': -1.0
    }
    player_evaluator = PlayerEvaluator(weights=weights)
    players = player_evaluator.evaluate_players(
        start_date="2023-01-09",
        end_date="2023-02-26",
        # use_totals=False
    )
    rosters = {}
    totals = {}
    for player in players:
        rosters.setdefault(player["manager"], [])
        rosters[player["manager"]].append(player)

    my_team = rosters.pop("Danny")
    free_agents = rosters.pop(None)

    print("--- My Team ---")
    for player in sorted(my_team, key=lambda x: x["relative_value"], reverse=True):
        print(f"{player['player_name']}   |   {player['relative_value']}   |   {player['salary']}")

    for stat in weights.keys():
        totals.setdefault(stat, [])
        totals[stat].append({"manager": "Danny", "total": sum(p[stat] for p in my_team)})

    print("\n")

    for manager, players in sorted(rosters.items()):
        print(f"--- {manager}'s Team ---")
        team = sorted(
            players,
            key=lambda x: x["relative_value"],
            reverse=True
        )
        for player in team:
            print(f"{player['player_name']}   |   {player['relative_value']}   |   {player['salary']}")

        for stat in weights.keys():
            totals[stat].append({"manager": manager, "total": sum(p[stat] for p in team)})
        print("\n")

    for stat, values in totals.items():
        print(f"\n--- {stat} ---")
        for value in sorted(values, key=lambda x: x["total"], reverse=True):
            print(f"{value['manager']}: {value['total']}")

    print("\n--- Free Agents ---")
    free_agents = sorted(
        free_agents,
        key=lambda x: x["relative_value"],
        reverse=True
    )
    for player in free_agents[:100]:
        print(f"{player['player_name']}   |   {player['relative_value']}   |   {player['salary']}    |    {player['status'] or ''}")