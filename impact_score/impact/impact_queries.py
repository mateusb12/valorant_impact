import copy

import pandas as pd
from termcolor import colored

from impact_score.impact.match_analysis import RoundReplay


class PlayerNotFoundException(Exception):
    pass


class ImpactQuery:
    def __init__(self):
        self.rr = RoundReplay()

    def set_match(self, match_id: int):
        self.rr.set_match(match_id)

    def __most_difficult_rounds(self, match_id: int) -> list[dict]:
        self.rr.set_match(match_id)
        round_outcomes = self.rr.tools.generate_side_outcomes_dict()
        outcome_pot = []
        for r in range(1, self.rr.round_amount + 1):
            self.rr.chosen_round = r
            final_winner = "def" if round_outcomes[r] == 0 else "atk"
            prob = self.rr.get_round_probability(side=final_winner, add_events=True)
            prob_pot = prob["Probability_before_event"].to_list()[:-1] + prob["Probability_after_event"].to_list()[:-1]
            lowest = min(prob_pot)
            outcome_pot.append({"Match": match_id, "Round": r, "Lowest": lowest})
        return sorted(outcome_pot, key=lambda k: k["Lowest"])

    def most_difficult_rounds_multiple_matches(self, match_list: list[int]) -> pd.DataFrame:
        round_pot = []
        for match_id in match_list:
            print(colored(f"Processing match {match_id}", "green"))
            query = self.__most_difficult_rounds(match_id)
            round_pot.extend(query)
        sorted_pot = sorted(round_pot, key=lambda k: k["Lowest"])
        for item in sorted_pot:
            item["Lowest"] = f"{100 * item['Lowest']:.2f}%"
        sorted_dict = {"Round": [], "Match": [], "Lowest": []}
        for item in sorted_pot:
            sorted_dict["Round"].append(item["Round"])
            sorted_dict["Match"].append(item["Match"])
            sorted_dict["Lowest"].append(item["Lowest"])
        return pd.DataFrame(sorted_dict)

    def __get_round_impact(self) -> dict:
        prob_table = self.rr.get_round_probability(side="def", add_events=True)
        player_impact_table = copy.deepcopy(self.rr.player_impact)
        for index in range(len(prob_table)):
            row = prob_table.iloc[index]
            event_type = row["EventType"]
            if event_type != "start":
                actor = row["Killer"]
                victim = row["Victim"]
                impact_value = row["Impact"]
                player_impact_table[actor]["gained"] += impact_value
                if event_type == "kill":
                    player_impact_table[victim]["lost"] += impact_value
        for key, value in player_impact_table.items():
            value["delta"] = value["gained"] - value["lost"]
        return player_impact_table

    def __get_map_impact(self) -> dict:
        pi = copy.deepcopy(self.rr.player_impact)
        impact_list = []
        for i in range(1, self.rr.round_amount + 1):
            self.rr.choose_round(i)
            round_impact = self.__get_round_impact()
            impact_list.append(round_impact)

        for round_impact in impact_list:
            for key, value in round_impact.items():
                pi[key]["gained"] += value["gained"]
                pi[key]["lost"] += value["lost"]
                pi[key]["delta"] += value["delta"]

        return dict(sorted(pi.items(), key=lambda item: item[1]["delta"], reverse=True))

    def get_map_impact_dataframe(self) -> pd.DataFrame:
        igns = []
        gains = []
        losses = []
        deltas = []
        map_impact = self.__get_map_impact()
        for key, value in map_impact.items():
            igns.append(key)
            gains.append(value["gained"])
            losses.append(value["lost"])
            deltas.append(value["delta"])
        match_id = [self.match_id] * len(igns)

        impact_table = {"Name": igns, "Gain": gains, "Lost": losses, "Delta": deltas, "MatchID": match_id}
        aux_impact = pd.DataFrame(impact_table)
        agent_dict = self.rr.exporter.export_player_agent_picks()
        aux_impact["Agent"] = aux_impact["Name"].map(agent_dict)
        return aux_impact

    def __is_player_in_this_match(self, player_name: str) -> bool:
        return player_name in self.rr.player_impact

    def get_player_most_impactful_rounds(self, input_player_name: str) -> pd.DataFrame:
        if not self.__is_player_in_this_match(input_player_name):
            raise PlayerNotFoundException(f"Player {input_player_name} not in this match")
        pot = []
        columns = ["Name", "Round", "Gained", "Lost", "Delta"]
        player_name = input_player_name.lower()
        for i in range(1, self.rr.round_amount + 1):
            self.rr.choose_round(i)
            impact_dict = self.__get_round_impact()
            impact_dict_lower = {k.lower(): v for k, v in impact_dict.items()}
            player_impact = impact_dict_lower[player_name]
            pot.append((player_name, i, player_impact["gained"], player_impact["lost"], player_impact["delta"]))
        res = pd.DataFrame(pot, columns=columns)
        res = res.sort_values("Gained", ascending=False)
        return res

    def get_biggest_throws(self, team_name: str = "Team Liquid") -> dict:
        original_round = self.rr.chosen_round
        team_sides = self.rr.tools.get_side_dict()
        dtb = self.rr.tools.generate_round_info()
        round_amount = max(dtb.keys())
        maximum_probabilities_dict = {}
        for i in range(1, round_amount + 1):
            self.rr.chosen_round = i
            side_info = team_sides[i][team_name]
            current_side = side_info["side"]
            formatted_side = {"defense": "def", "attack": "atk"}
            prob = self.rr.get_round_probability(side=formatted_side[current_side], add_events=True)
            if side_info["outcome"] == "loss":
                round_id = dtb[i]["number"]
                max_prob = max(list(prob["Probability_before_event"]))
                maximum_probabilities_dict[round_id] = round(100 * max_prob, 2)
        self.rr.chosen_round = original_round
        sorted_dict = dict(sorted(maximum_probabilities_dict.items(), key=lambda item: item[1], reverse=True))
        return {key: f"{value}%" for key, value in sorted_dict.items()}

    def get_biggest_clutches(self, team_name: str = "Team Liquid") -> dict:
        biggest_throws = self.get_biggest_throws(team_name)
        without_percentage = {key: float(value[:-1]) for key, value in biggest_throws.items()}
        inverse_prob_dict = {key: round(100 - value, 2) for key, value in without_percentage.items()}
        sorted_dict = dict(sorted(inverse_prob_dict.items(), key=lambda item: item[1], reverse=False))
        return {key: f"{value}%" for key, value in sorted_dict.items()}

    def get_clutchy_rounds(self, chosen_side: str) -> dict:
        dtb = self.rr.tools.generate_round_info()
        winner_dict = {0: "def", 1: "atk"}
        round_amount = max(dtb.keys())
        minimum_probabilities_dict = {}
        original_round = self.rr.chosen_round
        for i in range(1, round_amount + 1):
            self.rr.chosen_round = i
            prob = self.rr.get_round_probability(side=chosen_side, add_events=True)
            winner = winner_dict[dtb[i]["finalWinner"]]
            if winner == chosen_side:
                round_id = dtb[i]["number"]
                min_prob = min(list(prob["Probability_before_event"]))
                minimum_probabilities_dict[round_id] = round(100 * min_prob, 2)

        self.rr.chosen_round = original_round
        sorted_d = dict(
            sorted(minimum_probabilities_dict.items(), key=lambda item: item[1])
        )
        return {key: f"{value}%" for key, value in sorted_d.items()}


def __main():
    iq = ImpactQuery()
    iq.set_match(77104)


if __name__ == "__main__":
    __main()
