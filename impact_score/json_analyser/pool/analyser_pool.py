# Create a Custom exception for the analyser pool
from impact_score.json_analyser.core.player_table_creation import PlayerTableCreator
from impact_score.json_analyser.core.simple_operations import get_round_events
from impact_score.json_analyser.core.analyser_file_loader import load_agent_data, load_weapon_data, load_ability_data
from impact_score.json_analyser.wrap.match_load_pipeline import load_match_info


class NoMoreAnalysersException(Exception):
    """No more objects in pool"""
    pass


class CoreAnalyser:
    def __init__(self, input_agent_data: dict, input_weapon_data: dict, input_ability_data: dict):
        self.chosen_round = 1
        self.map_dict, self.attacking_first_team, self.defending_first_team, self.round_events = None, None, None, None
        self.data, self.current_status, self.match_id, self.round_amount, self.map_name = None, None, None, None, None
        self.defuse_happened, self.round_number, self.event_type, self.team_details = None, None, None, None
        self.economy_data, self.location_data, self.player_table_creator = None, None, None
        self.agent_data: dict = input_agent_data
        self.weapon_data: dict = input_weapon_data
        self.ability_data: dict = input_ability_data

    def set_match(self, match_id: int):
        self.match_id = match_id
        self.data = load_match_info(match_id)
        self.map_dict = [item for item in self.data["series"]["seriesById"]["matches"] if item["id"] == match_id][0]
        self.economy_data = self.data["matches"]["matchDetails"]["economies"]
        self.location_data = self.data["matches"]["matchDetails"]["locations"]
        self.player_table_creator = PlayerTableCreator(map=self.map_dict, economies=self.economy_data,
                                                       locations=self.location_data)
        self.attacking_first_team: int = self.map_dict["attackingFirstTeamNumber"]
        self.defending_first_team: int = 1 if self.attacking_first_team == 2 else 2
        self.round_amount = self.map_dict["team1Score"] + self.map_dict["team2Score"]
        self.map_name = self.map_dict["map"]["name"]

    def choose_round(self, desired_round: int):
        self.chosen_round = desired_round
        self.round_events = get_round_events(self.data, self.chosen_round)
        self.__set_player_status()

    def __set_player_status(self):
        self.player_table_creator.pick_round(self.chosen_round)
        self.current_status: dict or bool = self.player_table_creator.create_player_table()

    def get_last_round(self) -> int:
        return self.round_amount

    def check_id(self):
        print(f"Using object {id(self)}")


class ReusablePool:
    def __init__(self, size=5):
        self._available_pool = []
        self.in_use = []
        self._size = size
        self._current = 0
        self.raw_agent_data = load_agent_data()
        self.raw_weapon_data = load_weapon_data()
        self.raw_ability_data = load_ability_data()
        for _ in range(size):
            self.add(CoreAnalyser(self.raw_agent_data, self.raw_weapon_data, self.raw_ability_data))

    def acquire(self) -> CoreAnalyser:
        if len(self._available_pool) <= 0:
            self.add(CoreAnalyser(self.raw_agent_data, self.raw_weapon_data, self.raw_ability_data))
            # raise NoMoreAnalysersException("No more objects in pool")
        r = self._available_pool[0]
        self._available_pool.remove(r)
        self.in_use.append(r)
        return r

    def release(self, item: CoreAnalyser):
        self._available_pool.append(item)
        self.in_use.remove(item)

    def add(self, item):
        self._available_pool.append(item)

    def reset(self):
        self._current = 0


analyser_pool = ReusablePool(2)


def __main():
    pool = ReusablePool(2)
    r = pool.acquire()
    r2 = pool.acquire()
    r.check_id()
    r2.check_id()


if __name__ == "__main__":
    __main()
