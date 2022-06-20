from impact_score.json_analyser.analyse_json import Analyser, get_map_dict, create_player_table, get_round_events
from impact_score.json_analyser.analyser_file_loader import get_agent_data, get_weapon_data


class AnalyserRound:
    def __init__(self, json_data: dict, input_match_id: int):
        self.data = json_data
        self.chosen_round = 1
        self.map_dict = get_map_dict(json_data, input_match_id)
        self.attacking_first_team: int = self.map_dict["attackingFirstTeamNumber"]
        self.defending_first_team: int = 1 if self.attacking_first_team == 2 else 2
        self.current_status = create_player_table(json_data, self.map_dict)
        self.round_events = None
        self.agent_data = get_agent_data()
        self.weapon_data = get_weapon_data()

    def choose_round(self, desired_round: int):
        self.chosen_round = desired_round
        self.round_events = get_round_events(self.data, self.chosen_round)

    def get_plant_timestamp(self) -> float or None:
        return next((h["timing"] for h in self.round_events if h["event"] == "plant"), None)

    def get_round_winner(self) -> int:
        for r in self.map_dict["rounds"]:
            if r["number"] == self.chosen_round:
                return 1 if r["winningTeamNumber"] == self.attacking_first_team else 0

    def are_sides_swapped(self) -> bool:
        if 1 <= self.chosen_round >= 12:
            return False
        elif 13 <= self.chosen_round <= 24:
            return True
        else:
            remaining = self.chosen_round - 24
            return remaining % 2 == 0

    def get_current_sides(self):
        if swap := self.are_sides_swapped():
            return {self.attacking_first_team: "defending", self.defending_first_team: "attacking"}
        else:
            return {self.attacking_first_team: "attacking", self.defending_first_team: "defending"}

    def get_player_sides(self) -> dict:
        team_sides = self.get_current_sides()
        return {player: team_sides[value["team_number"]] for player, value in self.current_status.items()}

    def generate_full_round(self) -> list:
        plant = self.get_plant_timestamp()
        self.defuse_happened = False
        self.event_type = "start"
        round_winner = self.get_round_winner()
        round_array = []
        sides = self.get_player_sides()
        atk_kills = 0
        def_kills = 0
        for value in self.round_events:
            event_type: str = value["event"]
            timing: int = value["timing"]
            if event_type == "defuse":
                self.defuse_happened = True
            elif event_type == "kill":
                self.current_status[value["victim"]]["alive"] = False
                player_side = sides[value["author"]]
                if player_side == "attacking":
                    atk_kills += 1
                elif player_side == "defending":
                    def_kills += 1
            elif event_type == "revival":
                self.current_status[value["victim"]]["shieldId"] = None
                self.current_status[value["victim"]]["alive"] = True
            event = self.generate_single_event_values(timestamp=timing, winner=round_winner, plant=plant)
            event["ATK_kills"] = atk_kills
            event["DEF_kills"] = def_kills
            round_array.append(event)
        return round_array


def __main():
    a = Analyser()
    a.set_match(68821)
    ar = AnalyserRound(a.data, a.match_id)
    ar.choose_round(2)
    ar.generate_full_round()


if __name__ == "__main__":
    __main()
