import requests

# from impact_score.impact.match_analysis import RoundReplay
from impact_score.json_analyser.analyse_json import Analyser


def export_impact(match_id: int, input_analyser: Analyser) -> dict:
    analyser = input_analyser
    analyser.set_match(match_id)
    analyser.set_config(round=1)
    # rr_object = RoundReplay()
    details = analyser.export_player_details()
    max_round = analyser.round_amount
    match_impact_dict = {f"Round_{i}": [] for i in range(1, max_round + 1)}
    for item in range(1, max_round + 1):
        analyser.set_config(round=item)
        # probability_table = rr_object.get_round_probability(side="atk")
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


if __name__ == "__main__":
    test = export_impact(match_id=60206, input_analyser=Analyser())
