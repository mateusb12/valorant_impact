# Create a Custom exception for the analyser pool
from impact_score.json_analyser.analyse_json import get_map_dict, create_player_table, get_round_events
from impact_score.json_analyser.analyser_file_loader import get_agent_data, get_weapon_data
from impact_score.json_analyser.api_consumer import get_match_info


class NoMoreAnalysersException(Exception):
    """No more objects in pool"""
    pass


class CoreAnalyser:
    def __init__(self, input_agent_data: dict, input_weapon_data: dict):
        self.chosen_round = 1
        self.map_dict, self.attacking_first_team, self.defending_first_team, self.round_events = None, None, None, None
        self.data, self.current_status, self.match_id, self.round_amount, self.map_name = None, None, None, None, None
        self.defuse_happened, self.round_number, self.event_type = None, None, None
        self.agent_data = input_agent_data
        self.weapon_data = input_weapon_data

    def set_match(self, match_id: int):
        self.match_id = match_id
        self.data = get_match_info(match_id)
        self.map_dict = get_map_dict(self.data, match_id)
        self.attacking_first_team: int = self.map_dict["attackingFirstTeamNumber"]
        self.defending_first_team: int = 1 if self.attacking_first_team == 2 else 2
        self.current_status = create_player_table(self.data, self.map_dict)
        self.round_amount = self.map_dict["team1Score"] + self.map_dict["team2Score"]
        self.map_name = self.map_dict["map"]["name"]

    def choose_round(self, desired_round: int):
        self.chosen_round = desired_round
        self.round_events = get_round_events(self.data, self.chosen_round)

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
        raw_agent_data = get_agent_data()
        raw_weapon_data = get_weapon_data()
        for _ in range(size):
            self.add(CoreAnalyser(raw_agent_data, raw_weapon_data))

    def acquire(self) -> CoreAnalyser:
        if len(self._available_pool) <= 0:
            raise NoMoreAnalysersException("No more objects in pool")
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

# def __main():
#     pool = ReusablePool(2)
#     r = pool.acquire()
#     r2 = pool.acquire()
#     r.check_id()
#     r2.check_id()
#
#
# if __name__ == "__main__":
#     __main()
