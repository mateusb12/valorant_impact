def get_map_dict(input_data: dict, input_match_id: int) -> dict:
    for match in input_data["series"]["seriesById"]["matches"]:
        if match["id"] == input_match_id:
            return match


def get_round_events(input_data: dict, chosen_round: int):
    """
    Get the events of the round (kills, deaths, plants, defuses, etc)
    :return:
    """
    return [
        {
            "round_number": m["roundNumber"],
            "timing": m["roundTimeMillis"],
            "author": m["playerId"],
            "victim": m["referencePlayerId"],
            "event": m["eventType"],
            "damage_type": m["damageType"],
            "weapon_id": m["weaponId"],
            "ability": m["ability"],
            "probability_before": m["attackingWinProbabilityBefore"],
            "probability_after": m["attackingWinProbabilityAfter"],
            "impact": m["impact"],
            "kill_id": m["killId"],
            "round_id": m["roundId"],
            "bomb_id": m["bombId"],
            "res_id": m["resId"]
        }
        for m in input_data["matches"]["matchDetails"]["events"]
        if m["roundNumber"] == chosen_round
    ]


def get_economy_data(economy_data: dict, round_amount: int) -> dict:
    economy_dict = {key: [] for key in range(1, round_amount + 1)}
    # economy_data = economy_data["economies"]
    for economy in economy_data:
        economy_dict[economy["roundNumber"]].append(economy)
    return economy_dict


def create_player_table(economy_data: dict, map_data: dict) -> dict:
    ign_table = {
        b["playerId"]: {"ign": b["player"]["ign"], "team_number": b["teamNumber"]}
        for b in map_data["players"]
    }

    attacking_first_team = map_data["attackingFirstTeamNumber"]

    player_dict = {}

    for item in economy_data:
        player_id = item["playerId"]
        aux = {"name": ign_table[player_id],
               "agentId": item["agentId"],
               "combatScore": item["score"],
               "weaponId": item["weaponId"],
               "shieldId": item["armorId"],
               "loadoutValue": item["loadoutValue"],
               "spentCreds": item["spentCreds"],
               "remainingCreds": item["remainingCreds"],
               "attacking_side": ign_table[player_id]["team_number"] == attacking_first_team,
               "team_number": ign_table[player_id]["team_number"],
               "alive": True}
        player_dict[player_id] = aux
        # if item["roundNumber"] == 1:
    return player_dict
