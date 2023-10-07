from src.utils.player_evaluator import PlayerEvaluator

if __name__ == "__main__":
    weights = {
        'field_goal_percentage': 1.0,
        'free_throw_percentage': 0.0,
        'three_pointers': 0.0,
        'points': 1.0,
        'rebounds': 1.0,
        'assists': 2.0,
        'steals': 1.0,
        'blocks': 1.0,
        'turnovers': -1.0
    }
    player_evaluator = PlayerEvaluator(weights=weights)
    players = player_evaluator.evaluate_players(
        start_date="2023-01-31",
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
        print(
            f"{player['player_name']}   |   {player['relative_value']:.2f}   |   "
            f"${player['salary']:,}    |    {player['minutes_per_game']:.2f}    |    {player['status'] or ''}"
        )

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
            print(
                f"{player['player_name']}   |   {player['relative_value']:.2f}   |   "
                f"${player['salary']:,}    |    {player['minutes_per_game']:.2f}    |    {player['status'] or ''}"
            )

        for stat in weights.keys():
            totals[stat].append({"manager": manager, "total": sum(p[stat] for p in team)})
        print("\n")

    for stat, values in totals.items():
        print(f"\n--- {stat} ---")
        for value in sorted(values, key=lambda x: x["total"], reverse=True):
            print(f"{value['manager']}: {value['total']:.2f}")

    print("\n--- Summary Stats of Player Value ---")
    from statistics import median

    print("Max: " + str(max(p["relative_value"] for p in free_agents)))
    print("Median: " + str(median(p["relative_value"] for p in free_agents)))

    print("\n--- Free Agents ---")
    free_agents = sorted(
        free_agents,
        key=lambda x: x["relative_value"],
        reverse=True
    )
    for player in free_agents[:100]:
        print(f"{player['player_name']}   |   {player['relative_value']:.2f}   |   "
              f"${player['salary']:,}    |    {player['minutes_per_game']:.2f}    |    {player['status'] or ''}")

    print("\n--- High Value Players ---")
    for player in sorted(free_agents, key=lambda x: x["relative_value"] / (x["salary"] / 1_000_000), reverse=True)[:50]:
        print(f"{player['player_name']}   |   {player['relative_value']:.2f}   |   "
              f"${player['salary']:,}    |    {player['minutes_per_game']:.2f}    |    {player['status'] or ''}")
