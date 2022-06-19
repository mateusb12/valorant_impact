from impact_score.json_analyser.analyse_json import Analyser
from impact_score.json_analyser.analyser_file_loader import get_agent_data, get_weapon_data


class AnalyserExporter:
    def __init__(self, data: dict, match_id: int):
        self.data = data
        self.match_id = match_id
        self.map_dict = self.get_map_dict()
        self.attacking_first_team: int = self.map_dict["attackingFirstTeamNumber"]
        self.current_status = self.create_player_table()
        self.agent_data = get_agent_data()
        self.weapon_data = get_weapon_data()

    def create_player_table(self) -> dict:
        ign_table = {
            b["playerId"]: {"ign": b["player"]["ign"], "team_number": b["teamNumber"]}
            for b in self.get_map_dict()["players"]
        }

        player_dict = {}

        for i in self.data["matches"]["matchDetails"]["economies"]:
            if i["roundNumber"] == 1:
                player_id = i["playerId"]
                aux = {"name": ign_table[player_id],
                       "agentId": i["agentId"],
                       "combatScore": i["score"],
                       "weaponId": i["weaponId"],
                       "shieldId": i["armorId"],
                       "loadoutValue": i["loadoutValue"],
                       "spentCreds": i["spentCreds"],
                       "remainingCreds": i["remainingCreds"],
                       "attacking_side": ign_table[player_id]["team_number"] == self.attacking_first_team,
                       "team_number": ign_table[player_id]["team_number"],
                       "alive": True}
                player_dict[player_id] = aux
        return player_dict

    def get_map_dict(self) -> dict:
        for match in self.data["series"]["seriesById"]["matches"]:
            if match["id"] == self.match_id:
                return match

    def export_round_events(self) -> dict:
        events = self.data["matches"]["matchDetails"]["events"]

        for event in events:
            killer_id = event["playerId"]
            victim_id = event["referencePlayerId"]
            if killer_id is None and victim_id is None:
                killer_name, killer_agent_id, killer_agent_name = None, None, None
            else:
                killer_name = self.current_status[killer_id]["name"]["ign"]
                killer_agent_id = self.current_status[killer_id]["agentId"]
                killer_agent_name = self.agent_data[str(killer_agent_id)]["name"]

            if event["eventType"] in ["kill", "revival"]:
                victim_name = self.current_status[victim_id]["name"]["ign"]
                victim_agent_id = self.current_status[victim_id]["agentId"]
                victim_agent_name = self.agent_data[str(victim_agent_id)]["name"]
                event["victim_agent_name"] = victim_agent_name
                event["victim_name"] = victim_name
            else:
                event["victim_agent_name"] = "None"
                event["victim_name"] = "None"
            if event["weaponId"] is not None:
                weapon = self.weapon_data[str(event["weaponId"])]
            else:
                weapon = {"weaponId": "None", "name": event["ability"]}
            event["killer_name"] = killer_name
            event["killer_agent_name"] = killer_agent_name
            event["weapon"] = weapon

        return events

    def export_player_agent_picks(self) -> dict:
        map_dict = self.get_map_dict()
        agent_pick_dict = {}
        for item in map_dict["players"]:
            player_name = item["player"]["ign"]
            agent_id = item["agentId"]
            agent_name = self.agent_data[str(agent_id)]["name"]
            agent_pick_dict[player_name] = agent_name
        return agent_pick_dict

    def export_player_details(self) -> dict:
        map_dict = self.get_map_dict()
        details_dict = {}
        for item in map_dict["players"]:
            player_name = item["player"]["ign"]
            agent_id = item["agentId"]
            agent_name = self.agent_data[str(agent_id)]["name"]
            player_id = item["playerId"]
            details_dict[player_id] = {"agent_name": agent_name, "player_name": player_name}
        return details_dict


def __main():
    a = Analyser()
    a.set_match(65588)
    ae = AnalyserExporter(a.data, a.match_id)
    a = ae.export_round_events()
    b = ae.export_player_agent_picks()
    c = ae.export_player_details()
    print(a, b, c)


if __name__ == "__main__":
    __main()
