import copy
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
        """
        Returns a dictionary of player names and their sides
        :param input_round: chosen round (int)
        :return: {'dimasick': 'attacking', 'ScreaM': 'attacking', 'soulcas': 'attacking', 'Melser': 'defending',
         'adverso': 'defending', 'Tacolilla': 'defending', 'kiNgg': 'defending', 'Jamppi': 'attacking',
          'Nivera': 'attacking', 'Shyy': 'defending'}
        """
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
        :return: {1: 1226197, 2: 1226198, 3: 1226199, 4: 1226200, 5: 1226201, 6: 1226202, 7: 1226203, 8: 1226204}
        """
        return {
            round_data["roundNumber"]: round_data["roundId"]
            for round_data in self.a.data["matches"]["matchDetails"]["events"]
        }

    def generate_round_info(self) -> dict:
        """
        Generates a dictionary with detailed info for each round
        :return:
        {1:
            {'id': 1226197, 'matchId': 77103, 'number': 1, 'winCondition': 'kills', 'winningTeamNumber': 1,
            'ceremony': 'default', 'team1LoadoutTier': None, 'team2LoadoutTier': None, 'team1LoadoutValue': None,
            'attacking': {'name': 'Team Liquid', 'id': 2},
            'defending': {'name': 'Leviathan', 'id': 1},
            'finalWinner': 0
        }
        """
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

    def generate_side_outcomes_dict(self) -> dict:
        """
        Generates a dictionary giving the outcomes of each round
        :return:
        {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 1, 7: 0, 8: 1, 9: 1, 10: 0, 11: 1, 12: 0, 13: 1, 14: 1,
         15: 0, 16: 0, 17: 0, 18: 0, 19: 1, 20: 0, 21: 1, 22: 0, 23: 1}
        """
        aux = self.generate_round_info()
        return {value["number"]: value["finalWinner"] for value in aux.values()}

    def get_side_dict(self) -> dict:
        """Output format
        {1:
            {'Leviathan':
                {'name': 'Leviatán', 'id': 738, 'team_id': 1, 'side': 'defense', 'outcome': 'win'},
            'Team Liquid':
                {'name': 'Team Liquid', 'id': 224, 'team_id': 2, 'side': 'attack', 'outcome': 'loss'}}
        """
        round_amount = self.a.map_dict["rounds"][-1]["number"]
        side_pattern = self.generate_side_outcomes_dict()

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

        final_dict = {}
        for key, value in pattern_dict.items():
            winner = side_pattern[key]
            new_value = copy.deepcopy(value)
            winner_tag = "defense" if winner == 0 else "attack"
            loser_tag = "defense" if winner_tag == "attack" else "attack"
            new_value[winner_tag]["side"] = winner_tag
            new_value[loser_tag]["side"] = loser_tag
            new_value[winner_tag]["outcome"] = "win"
            new_value[loser_tag]["outcome"] = "loss"
            loser_name = new_value[loser_tag]["name"]
            winner_name = new_value[winner_tag]["name"]
            final_dict[key] = {winner_name: new_value[winner_tag], loser_name: new_value[loser_tag]}
        return final_dict

    def get_economy_dict(self, round_number: int) -> dict:
        economy_pool = self.a.data["matches"]["matchDetails"]["economies"]
        round_economies = [economy for economy in economy_pool if economy["roundNumber"] == round_number]
        player_economies = {}
        for economy in round_economies:
            economy["agent"] = self.a.agent_data[str(economy["agentId"])]
            economy["weapon"] = self.a.weapon_data[str(economy["weaponId"])]
            player_economies[economy["playerId"]] = economy
        return player_economies

    def get_round_loss_bonus_by_players(self, round_number: int):
        """Gets the round loss bonus for each player in a given round.
        A team earns 1900 credits per member for a single round loss
        A team earns 2400 credits per member for a double round loss
        A team earns 2900 credits per member for 3 round losses or more in a row"""
        players = self.a.map_dict["players"]
        team_1_players = [item["player"] for item in players if item["teamNumber"] == 1]
        outcomes = self.generate_side_outcomes_dict()
        side_format = {0: "defending", 1: "attacking"}
        mirrored_side_format = {1: "defending", 0: "attacking"}
        last_round_outcome = outcomes[round_number - 1] if round_number not in (1, 13) else None
        if last_round_outcome is None:
            return {player["ign"]: 0 for player in team_1_players}
        last_round_winning_side = side_format[last_round_outcome]
        last_round_defeated_side = mirrored_side_format[last_round_outcome]
        side_table = self.get_player_name_sides(round_number)
        losing_players = [player for player in side_table if side_table[player] != last_round_winning_side]
        penultimate_round_outcome = outcomes[round_number - 2] if round_number not in (1, 13, 2, 14) else None
        penultimate_round_losing_side = mirrored_side_format[penultimate_round_outcome] \
            if penultimate_round_outcome is not None else None
        antepenultimate_round_outcome = outcomes[round_number - 3] \
            if round_number not in (1, 13, 2, 14, 3, 15) else None
        antepenultimate_round_losing_side = mirrored_side_format[antepenultimate_round_outcome]\
            if antepenultimate_round_outcome is not None else None
        loss_streak = 1
        if last_round_defeated_side == penultimate_round_losing_side:
            loss_streak += 1
        if last_round_defeated_side == antepenultimate_round_losing_side:
            loss_streak += 1
        loss_streak_bonus_table = {0: 0, 1: 1900, 2: 2400, 3: 2900}
        current_loss_streak_bonus = loss_streak_bonus_table[loss_streak]
        return {player: current_loss_streak_bonus for player in losing_players}


def __main():
    a = analyser_pool.acquire()
    a.set_match(78746)
    aw = AnalyserTools(a)
    aw.a.choose_round(1)
    # for i in range(1, 25):
    #     print(i)
    #     test1 = aw.get_round_loss_bonus_by_players(i)
    #     print(test1)
    test1 = aw.get_round_loss_bonus_by_players(13)
    print(test1)


if __name__ == "__main__":
    __main()
