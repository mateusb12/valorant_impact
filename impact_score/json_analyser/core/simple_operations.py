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


def create_player_table(input_data: dict, map_data: dict) -> dict:
    ign_table = {
        b["playerId"]: {"ign": b["player"]["ign"], "team_number": b["teamNumber"]}
        for b in map_data["players"]
    }

    attacking_first_team = map_data["attackingFirstTeamNumber"]

    player_dict = {}

    for i in input_data["matches"]["matchDetails"]["economies"]:
        if i["roundNumber"] == 1:
            player_id = i["playerId"]
            aux = {"name": ign_table[player_id],
                   "agentId": i["agentId"],
                   "combatScore": i["score"],
                   "weaponId": i["weaponId"],
                   "shieldId": i["armorId"],
                   "loadoutValue": i["loadoutValue"],
                   "spentCreds": i["spentCreds"],
                   "remainingCreds": i["remainingCreds"],
                   "attacking_side": ign_table[player_id]["team_number"] == attacking_first_team,
                   "team_number": ign_table[player_id]["team_number"],
                   "alive": True}
            player_dict[player_id] = aux
    return player_dict
