from impact_score.impact_consumer.impact_consumer import merge_impacts
from impact_score.json_analyser.core.analyser_tools import AnalyserTools
from impact_score.json_analyser.pool.analyser_pool import analyser_pool


def query_clutch_situations(match_id: int) -> dict:
    a = analyser_pool.acquire()
    a.set_match(match_id)
    aw = AnalyserTools(a)
    df = merge_impacts(match_id)
    max_round = df["round_number"].max()
    round_book = {f"Round_{i}": None for i in range(1, max_round + 1)}
    for round_number in range(1, max_round + 1):
        player_sides = aw.get_player_name_sides(round_number)
        attacker_pool = [item for item in player_sides if player_sides[item] == "attacking"]
        defender_pool = [item for item in player_sides if player_sides[item] == "defending"]
        query_string = f"round_number == {round_number}"
        query = df.query(query_string)
        situation_pot = []
        for index, row in query.iterrows():
            if row["event"] == "kill":
                victim_name = row["victim"]
                victim_side = player_sides[victim_name]
                if victim_side == "attacking":
                    attacker_pool.remove(victim_name)
                elif victim_side == "defending":
                    defender_pool.remove(victim_name)
                situation = f"{len(attacker_pool)}vs{len(defender_pool)}"
                winner_dict = {0: "defense", 1: "attack"}
                situation_dict = {"situation": situation,
                                  "probability": row["Probability_after_event"],
                                  "attackers": tuple(attacker_pool),
                                  "defenders": tuple(defender_pool),
                                  "final_winner": winner_dict[row["FinalWinner"]]}
                situation_pot.append(situation_dict)
        round_book[f"Round_{round_number}"] = situation_pot
    return round_book


def query_hardest_situations(match_id: int):
    clutch_type = 2
    situations = [f"{i}vs{j}" for i in range(1, 6) for j in range(1, 6)]
    clutch_pattern = [item for item in situations if int(item[0]) == clutch_type or int(item[-1]) == clutch_type]
    round_data = query_clutch_situations(match_id)
    duo_dict = {}
    for round_events in round_data.values():
        if matching_pattern := [item for item in round_events if item["situation"] in clutch_pattern]:
            first_situation = matching_pattern[0]["situation"].split("vs")
            alive_dict = {"attack": int(first_situation[0]), "defense": int(first_situation[-1])}
            disadvantage_side = min(alive_dict, key=alive_dict.get)
            final_winner = matching_pattern[0]["final_winner"]
            if disadvantage_side == final_winner:
                dict_conversion = {"attack": "attackers", "defense": "defenders"}
                event = matching_pattern[0]
                side = dict_conversion[disadvantage_side]
                duo_names = event[side]
                impact = 100 * (event["probability"] if disadvantage_side == "attack" else 1 - event["probability"])
                duo_dict[duo_names] = impact
    return duo_dict


def __main():
    aux = query_hardest_situations(74098)
    print(aux)


if __name__ == "__main__":
    __main()
