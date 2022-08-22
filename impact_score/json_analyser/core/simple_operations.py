from impact_score.json_analyser.core.api_consumer import request_http_match_data


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
    for economy in economy_data:
        economy_dict[economy["roundNumber"]].append(economy)
    return economy_dict


def get_location_data(location_data: dict, round_amount: int) -> dict:
    location_dict = {key: [] for key in range(1, round_amount + 1)}
    for location in location_data:
        location_dict[location["roundNumber"]].append(location)
    return location_dict


def __main():
    pass


if __name__ == "__main__":
    __main()
