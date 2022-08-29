import copy

import pandas as pd
from termcolor import colored

from impact_score.impact_consumer.impact_consumer import merge_impacts
from impact_score.json_analyser.core.analyser_tools import AnalyserTools
from impact_score.json_analyser.pool.analyser_pool import analyser_pool

from timeit import default_timer as timer

from impact_score.model.progress_printer import time_metrics


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


def aggregate_single_dataframe(match_id: int) -> pd.DataFrame:
    print(colored(f"Processing match {match_id}", "green"))
    df = generate_query_dataframe(match_id)
    df["win"] = df["outcome"] == "won"
    df["loss"] = df["outcome"] == "lost"
    df["win"] = df["win"].astype(int)
    df["loss"] = df["loss"].astype(int)
    df["probability"] = df["probability"] / 100
    agg_df = df.groupby(["duo"]).agg({"win": "sum", "loss": "sum", "probability": "sum"})
    agg_df = agg_df[agg_df.index.map(lambda x: len(x) > 1)]
    agg_df = agg_df.rename(columns={"probability": "agg_probability"})
    return agg_df


def aggregate_multiple_dataframes() -> pd.DataFrame:
    df_pot = generate_match_pot()
    final_df = pd.concat(df_pot)
    final_df = final_df.groupby(["duo"]).agg({"win": "sum", "loss": "sum", "agg_probability": "sum"})
    final_df = final_df[final_df.index.map(lambda x: len(x) > 1)]
    final_df["expected_outcome"] = final_df["win"] / final_df["agg_probability"]
    final_df["expected_wins"] = final_df["agg_probability"].round(1)
    performance_tag = "rounds_above_expected"
    final_df[performance_tag] = final_df["win"] - final_df["expected_wins"]
    final_df = final_df.rename(columns={"probability": "agg_probability"})
    final_df = final_df.drop(columns=["agg_probability", "expected_outcome"])
    for column in ["expected_wins", performance_tag]:
        final_df[column] = final_df[column].apply(lambda x: float("{:.1f}".format(x)))
    final_df = final_df.sort_values(by=[performance_tag], ascending=False)
    final_df.to_csv("duo_performance.csv")
    return final_df


def generate_match_pot() -> list[pd.DataFrame]:
    match_list = pd.read_csv("vct_matches.csv")["Match Id"].tolist()
    start = timer()
    size = len(match_list)
    df_pot = []
    for index, match_id in enumerate(match_list, 1):
        loop = timer()
        print(colored(f"Processing match #{index} of {len(match_list)}", "green"))
        time_metrics(start=start, end=loop, index=index, size=size, tag="match", element=match_id)
        try:
            df = aggregate_single_dataframe(match_id)
        except KeyError:
            continue
        else:
            df_pot.append(df)
    return df_pot


def __main():
    # aux = aggregate_multiple_dataframes([74097, 74098, 74099])
    aux = aggregate_multiple_dataframes()
    print(aux)


if __name__ == "__main__":
    __main()
