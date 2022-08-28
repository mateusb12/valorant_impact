from impact_score.impact_consumer.impact_consumer import merge_impacts
from impact_score.json_analyser.core.analyser_tools import AnalyserTools
from impact_score.json_analyser.pool.analyser_pool import analyser_pool


def query_clutch_situations(match_id: int):
    a = analyser_pool.acquire()
    a.set_match(match_id)
    aw = AnalyserTools(a)
    df = merge_impacts(match_id)
    max_round = df["round_number"].max()
    round_book = {f"Round_{i}": None for i in range(1, max_round + 1)}
    for round_number in range(1, max_round + 1):
        player_sides = aw.get_player_name_sides(round_number)
        attackers = [item for item in player_sides if player_sides[item] == "attacking"]
        defenders = [item for item in player_sides if player_sides[item] == "defending"]
        query_string = f"round_number == {round_number}"
        query = df.query(query_string)
        situation_pot = []
        for index, row in query.iterrows():
            if row["event"] == "kill":
                victim_name = row["victim"]
                victim_side = player_sides[victim_name]
                if victim_side == "attacking":
                    attackers.remove(victim_name)
                elif victim_side == "defending":
                    defenders.remove(victim_name)
                situation = f"{len(attackers)}vs{len(defenders)}"
                winner_dict = {0: "defense", 1: "attack"}
                situation_pot.append({"situation": situation,
                                      "probability": row["Probability_after_event"],
                                      "attackers": tuple(attackers),
                                      "defenders": tuple(defenders),
                                      "final_winner": winner_dict[row["FinalWinner"]]})
        round_book[f"Round_{round_number}"] = situation_pot
    return round_book


def __main():
    aux = query_clutch_situations(74099)
    print("nice")


if __name__ == "__main__":
    __main()
