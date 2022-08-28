from typing import Tuple

from impact_score.json_analyser.pool.analyser_pool import CoreAnalyser, analyser_pool


class AnalyserTools:
    def __init__(self, input_core_analyser: CoreAnalyser):
        self.a = input_core_analyser
        series_by_id = self.a.data["series"]["seriesById"]
        self.team_details: dict = {1: series_by_id["team1"], 2: series_by_id["team2"]}
        self.team_details[1]["number"] = 1
        self.team_details[2]["number"] = 2
        self.round_details: list = self.a.map_dict["rounds"]

    def get_plant_timestamp(self) -> float or None:
        return next((h["timing"] for h in self.a.round_events if h["event"] == "plant"), None)

    def get_round_winner(self) -> int:
        round_dict = {key["number"]: key for key in self.a.map_dict["rounds"]}
        attacking_first = self.a.attacking_first_team
        current_sides = self.get_current_sides()
        current_round = round_dict[self.a.chosen_round]
        winning_team_number = current_round["winningTeamNumber"]
        final_winner_tag = current_sides[winning_team_number]
        final_winner_dict = {"attacking": 1, "defending": 0}
        return final_winner_dict[final_winner_tag]
        # for r in self.a.map_dict["rounds"]:
        #     if r["number"] == self.a.chosen_round:
        #         official_winner = r["finalWinner"]
        #
        # return 1 if r["winningTeamNumber"] == self.a.attacking_first_team else 0

    def __are_sides_swapped(self) -> bool:
        if 1 <= self.a.chosen_round <= 12:
            return False
        elif 13 <= self.a.chosen_round <= 24:
            return True
        else:
            remaining = self.a.chosen_round - 24
            return remaining % 2 == 0

    def get_current_sides(self) -> dict:
        if swap := self.__are_sides_swapped():
            return {self.a.attacking_first_team: "defending", self.a.defending_first_team: "attacking"}
        else:
            return {self.a.attacking_first_team: "attacking", self.a.defending_first_team: "defending"}

    def get_player_sides(self) -> dict:
        team_sides = self.get_current_sides()
        return {player: team_sides[value["team_number"]] for player, value in self.a.current_status.items()}

    def get_player_name_sides(self, input_round: int) -> dict:
        self.a.choose_round(input_round)
        players = self.a.map_dict["players"]
        id_dict = {player["player"]["id"]: player["player"]["ign"] for player in players}
        side_dict = self.get_player_sides()
        return {id_dict[key]: side_dict[key] for key in side_dict}

    def generate_spike_timings(self, round_millis: int, plant_millis: int) -> Tuple[int, int]:
        maximum_time = plant_millis + 45000 if plant_millis is not None else 100000
        if round_millis >= maximum_time or self.a.defuse_happened:
            regular_time = 0
            spike_time = 0
        elif round_millis == plant_millis:
            regular_time = 0
            spike_time = 45000
        elif (
                plant_millis is not None
                and round_millis <= plant_millis
                or plant_millis is None
        ):
            regular_time = 100000 - round_millis
            spike_time = 0
        else:
            regular_time = 0
            spike_time = 45000 - (round_millis - plant_millis)

        def round_func(x):
            return int(round(x / 1000))

        regular_time = round_func(regular_time)
        spike_time = round_func(spike_time)
        return regular_time, spike_time

    def get_team_a(self) -> dict:
        """
        Get the team A of the current map
        :return: {'id': 3975, 'name': 'Pioneers'}
        """
        aux = self.a.data["series"]["seriesById"]
        return {"id": aux["team1"]["id"], "name": aux["team1"]["name"]}

    def get_team_b(self) -> dict:
        """
        Get the team B of the current map
        :return: {'id': 588, 'name': 'Knights'}
        """
        aux = self.a.data["series"]["seriesById"]
        return {"id": aux["team2"]["id"], "name": aux["team2"]["name"]}

    def get_round_table(self) -> dict:
        """
        Returns a dictionary of rounds raw order and their IDs
        :return: round[6] = 509225
        """
        return {
            round_data["roundNumber"]: round_data["roundId"]
            for round_data in self.a.data["matches"]["matchDetails"]["events"]
        }

    def generate_round_info(self) -> dict:
        final_winner_dict = {"attacking": 1, "defending": 0}
        for item in self.round_details:
            self.a.choose_round(item["number"])
            current_sides = self.get_current_sides()
            current_sides_inverse = {value: key for key, value in current_sides.items()}
            item["attacking"] = {"name": self.team_details[current_sides_inverse["attacking"]]["name"],
                                 "id": self.team_details[current_sides_inverse["attacking"]]["number"]}
            item["defending"] = {"name": self.team_details[current_sides_inverse["defending"]]["name"],
                                 "id": self.team_details[current_sides_inverse["defending"]]["number"]}
            item["finalWinner"] = final_winner_dict[current_sides[item["winningTeamNumber"]]]
        return {item["number"]: item for item in self.round_details}

    def generate_side_dict(self) -> dict:
        aux = self.generate_round_info()
        return {value["number"]: value["finalWinner"] for value in aux.values()}

    def get_side_dict(self) -> dict:
        round_amount = 32

        pattern = ["normal"] * 12
        if 12 < round_amount < 24:
            remaining = round_amount - 12
            pattern += ["swap"] * remaining
        else:
            pattern += ["swap"] * 12
            remaining = round_amount - 24
            pattern += ["normal", "swap"] * remaining
        rounds = list(range(1, round_amount + 1))
        pattern_dict = {r: pattern[r - 1] for r in rounds}

        base = self.a.data["series"]["seriesById"]
        team_details = {1: {"name": base["team1"]["name"], "id": base["team1"]["id"], "team_id": 1},
                        2: {"name": base["team2"]["name"], "id": base["team2"]["id"], "team_id": 2}}

        attacking_first = self.a.map_dict["attackingFirstTeamNumber"]
        defending_first_dict = {1: 2, 2: 1}
        defending_first = defending_first_dict[attacking_first]
        normal = {"attack": team_details[attacking_first], "defense": team_details[defending_first]}
        swap = {"attack": team_details[defending_first], "defense": team_details[attacking_first]}

        for key in pattern_dict:
            pattern_dict[key] = normal if pattern_dict[key] == "normal" else swap

        tag_dict = {1: "attack", 2: "defense"}
        reverse_tag_dict = {"attack": 1, "defense": 0}
        round_winners = {item["number"]: item["winningTeamNumber"] for item in self.a.map_dict["rounds"]}
        final_dict = {}
        for key, value in pattern_dict.items():
            winner = round_winners[key]
            winner_tag = tag_dict[winner]
            final_winner = reverse_tag_dict[winner_tag]
            winner_details = pattern_dict[key][winner_tag]
            winner_details["side"] = winner_tag
            winner_details["finalWinner"] = final_winner
            final_dict[key] = winner_details
        return final_dict


def __main():
    a = analyser_pool.acquire()
    a.set_match(74099)
    aw = AnalyserTools(a)
    aw.a.choose_round(5)
    test1 = aw.get_player_name_sides()
    print(test1)


if __name__ == "__main__":
    __main()
