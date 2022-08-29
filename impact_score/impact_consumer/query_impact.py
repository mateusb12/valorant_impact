import copy

import pandas as pd

from impact_score.impact_consumer.impact_consumer import merge_impacts
from impact_score.json_analyser.core.analyser_tools import AnalyserTools
from impact_score.json_analyser.pool.analyser_pool import analyser_pool


def handle_kill_or_revival(attacker_pool: list[str], defender_pool: list[str], player_sides: dict, row: pd.Series):
    victim_name = row["victim"]
    victim_side = player_sides[victim_name]
    if victim_side == "attacking":
        if row["event"] == "kill":
            attacker_pool.remove(victim_name)
        elif row["event"] == "revival":
            attacker_pool.append(victim_name)
    elif victim_side == "defending":
        if row["event"] == "kill":
            defender_pool.remove(victim_name)
        elif row["event"] == "revival":
            defender_pool.append(victim_name)


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
            if row["event"] in ["kill", "revival"]:
                handle_kill_or_revival(attacker_pool, defender_pool, player_sides, row)
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
            for event in matching_pattern:
                handle_mid_round_event(duo_dict, event, matching_pattern)
    return duo_dict


def handle_mid_round_event(duo_dict: dict, event: dict, matching_pattern: list[dict]):
    situation_tag = event["situation"]
    if situation_tag not in duo_dict:
        duo_dict[situation_tag] = []
    alive_numbers = [int(i) for i in event["situation"].split("vs")]
    alive_dict = {"attack": alive_numbers[0], "defense": alive_numbers[-1]}
    disadvantage_side = min(alive_dict, key=alive_dict.get)
    final_winner = matching_pattern[0]["final_winner"]
    dict_conversion = {"attack": "attackers", "defense": "defenders"}
    side = dict_conversion[disadvantage_side]
    duo_names = event[side]
    opponents = [item for item in event["attackers"] + event["defenders"] if item not in duo_names]
    outcome = "won" if final_winner == disadvantage_side else "lost"
    chances = 100 * (event["probability"] if disadvantage_side == "attack" else 1 - event["probability"])
    situation_type = "equal_ground" if alive_numbers[0] == alive_numbers[-1] else "disadvantageous"
    situation_dict = {"situation": situation_tag, "outcome": outcome, "probability": chances,
                      "type": situation_type, "duo": tuple(duo_names), "opponents": tuple(opponents)}
    duo_dict[situation_tag].append(copy.deepcopy(situation_dict))
    if situation_type == "equal_ground":
        new_copy = copy.deepcopy(situation_dict)
        new_copy["duo"] = tuple(opponents)
        new_copy["opponents"] = tuple(duo_names)
        new_copy["outcome"] = "won" if final_winner != disadvantage_side else "lost"
        new_copy["probability"] = 100 - chances
        duo_dict[situation_tag].append(new_copy)


def generate_query_dataframe(match_id: int) -> pd.DataFrame:
    data = query_hardest_situations(match_id)
    df = pd.DataFrame()
    for situation in data:
        df = df.append(data[situation])
    df = df.sort_values(by=["outcome", "probability"], ascending=False)
    return df


def aggregate_dataframe(match_id: int) -> pd.DataFrame:
    df = generate_query_dataframe(match_id)
    df["win"] = df["outcome"] == "won"
    df["loss"] = df["outcome"] == "lost"
    df["win"] = df["win"].astype(int)
    df["loss"] = df["loss"].astype(int)
    agg_df = df.groupby(["duo"]).agg({"win": "sum", "loss": "sum", "probability": "sum"})
    agg_df = agg_df[agg_df.index.map(lambda x: len(x) > 1)]
    agg_df["expected_outcome"] = agg_df["win"] / agg_df["probability"]
    # Rename probability to agg_probability
    agg_df = agg_df.rename(columns={"probability": "agg_probability"})
    agg_df = agg_df.sort_values(by=["expected_outcome"], ascending=False)
    return agg_df

    # duo_performance = {}
    # # Loop through the dataframe, aggregate the amount of wins for each duo, and average the probability of winning
    # for index, row in df.iterrows():
    #     duo = row["duo"]
    #     if duo not in duo_performance:
    #         duo_performance[duo] = {"wins": 0, "losses": 0, "sum_probability_on_wins": 0}
    #     if row["outcome"] == "won":
    #         duo_performance[duo]["wins"] += 1
    #         duo_performance[duo]["avg_probability_on_wins"] += row["probability"]
    #     if row["outcome"] == "lost":
    #         duo_performance[duo]["losses"] += 1
    # # Create an "avg_probability_on_wins" for each duo
    # for duo in duo_performance:
    #     duo_performance[duo]["avg_probability_on_wins"] /= duo_performance[duo]["wins"]


def __main():
    aux = aggregate_dataframe(74098)
    print(aux)


if __name__ == "__main__":
    __main()
