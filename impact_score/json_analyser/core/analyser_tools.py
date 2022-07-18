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
        for r in self.a.map_dict["rounds"]:
            if r["number"] == self.a.chosen_round:
                return 1 if r["winningTeamNumber"] == self.a.attacking_first_team else 0

    def are_sides_swapped(self) -> bool:
        if 1 <= self.a.chosen_round <= 12:
            return False
        elif 13 <= self.a.chosen_round <= 24:
            return True
        else:
            remaining = self.a.chosen_round - 24
            return remaining % 2 == 0

    def get_current_sides(self):
        if swap := self.are_sides_swapped():
            return {self.a.attacking_first_team: "defending", self.a.defending_first_team: "attacking"}
        else:
            return {self.a.attacking_first_team: "attacking", self.a.defending_first_team: "defending"}

    def get_player_sides(self) -> dict:
        team_sides = self.get_current_sides()
        return {player: team_sides[value["team_number"]] for player, value in self.a.current_status.items()}

    def generate_spike_timings(self, round_millis: int, plant_millis: int) -> Tuple:
        if round_millis >= 100000 or self.a.defuse_happened:
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
            current_sides_inverse = {v: k for k, v in current_sides.items()}
            item["attacking"] = {"name": self.team_details[current_sides_inverse["attacking"]]["name"],
                                 "id": self.team_details[current_sides_inverse["attacking"]]["number"]}
            item["defending"] = {"name": self.team_details[current_sides_inverse["defending"]]["name"],
                                 "id": self.team_details[current_sides_inverse["defending"]]["number"]}
            item["finalWinner"] = final_winner_dict[current_sides[item["winningTeamNumber"]]]
        return {item["number"]: item for item in self.round_details}


def __main():
    a = analyser_pool.acquire()
    a.set_match(68821)
    aw = AnalyserTools(a)
    aw.generate_round_info()
    q = aw.round_details
    print(q)


if __name__ == "__main__":
    __main()
