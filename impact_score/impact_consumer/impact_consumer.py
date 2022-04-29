from typing import Union, Dict, Any

from impact_score.json_analyser.analyse_json import Analyser
from impact_score.json_analyser.api_consumer import get_impact_details


def export_impact(match_id: int, input_analyser: Analyser) -> dict:
    """
    Export the impact of each player in a match.
    :param match_id: The match id. (60206)
    :param input_analyser: Analyser object instance.
    :return: Dictionary containing event details. For example:
    {
        "round_1": [
            {
                "author": "Crashies",
                "victim": "Nivera",
                "event": "kill",
                "impact": "0.039",
                "probability_before": "0.2318",
                "probability_after": "0.2709"
                "timing": "26185",
    """
    analyser = input_analyser
    analyser.set_match(match_id)
    analyser.set_config(round=1)
    details = analyser.export_player_details()
    max_round = analyser.round_amount
    match_impact_dict = {f"Round_{i}": [] for i in range(1, max_round + 1)}
    for item in range(1, max_round + 1):
        analyser.set_config(round=item)
        for event in analyser.round_events:
            author_id = event["author"]
            victim_id = event["victim"]
            weapon_id = event["weapon_id"]
            if author_id is not None:
                event["author"] = details[author_id]["player_name"]
                event["author_agent"] = details[author_id]["agent_name"]
            if victim_id is not None:
                event["victim"] = details[victim_id]["player_name"]
                event["victim_agent"] = details[victim_id]["agent_name"]
            if weapon_id is not None:
                event["weapon_name"] = analyser.weapon_data[f"{weapon_id}"]["name"]
            match_impact_dict[f"Round_{item}"].append(event)
    return match_impact_dict


def export_players_impact(match_id: int, input_analyser: Analyser, **kwargs) -> Union[int, dict[Any, int]]:
    """
    Export the impact of each player in a match.
    :param match_id: The match id. (60206)
    :param input_analyser: Analyser object instance.
    :param kwargs: player_name="crashies"
    :return: Dictionary with impact for each player, unless kwargs player_name is set. Example:
    {
        "keznit": 0.9838,
        "Nivera": 1.141,
        "Jamppi": 3.176,
        "Mazino": 1.852,
        "ScreaM": 0.988
    }
    """
    match_data = export_impact(match_id, input_analyser)
    player_impact_dict = {}

    for round_n in match_data.values():
        for event in round_n:
            author = event['author']
            if author not in player_impact_dict and author is not None:
                player_impact_dict[author] = 0
            if author is not None:
                impact = float(event['impact'])
                player_impact_dict[author] += impact

    if "player_name" in kwargs:
        return player_impact_dict[kwargs["player_name"]]
    else:
        return player_impact_dict


if __name__ == "__main__":
    test = export_impact(match_id=60206, input_analyser=Analyser())
    test2 = export_players_impact(match_id=60206, input_analyser=Analyser())
    print(test)
