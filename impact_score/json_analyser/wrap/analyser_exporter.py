from impact_score.json_analyser.pool.analyser_pool import analyser_pool, CoreAnalyser


class AnalyserExporter:
    def __init__(self, input_core_analyser: CoreAnalyser):
        self.a = input_core_analyser

    def export_round_events(self) -> dict:
        events = self.a.data["matches"]["matchDetails"]["events"]

        for event in events:
            killer_id = event["playerId"]
            victim_id = event["referencePlayerId"]
            if killer_id is None and victim_id is None:
                killer_name, killer_agent_id, killer_agent_name = None, None, None
            else:
                killer_name = self.a.current_status[killer_id]["name"]["ign"]
                killer_agent_id = self.a.current_status[killer_id]["agentId"]
                killer_agent_name = self.a.agent_data[str(killer_agent_id)]["name"]

            if event["eventType"] in ["kill", "revival"]:
                victim_name = self.a.current_status[victim_id]["name"]["ign"]
                victim_agent_id = self.a.current_status[victim_id]["agentId"]
                victim_agent_name = self.a.agent_data[str(victim_agent_id)]["name"]
                event["victim_agent_name"] = victim_agent_name
                event["victim_name"] = victim_name
            else:
                event["victim_agent_name"] = "None"
                event["victim_name"] = "None"
            if event["weaponId"] is not None:
                weapon = self.a.weapon_data[str(event["weaponId"])]
            else:
                weapon = {"weaponId": "None", "name": event["ability"]}
            event["killer_name"] = killer_name
            event["killer_agent_name"] = killer_agent_name
            event["weapon"] = weapon

        return events

    def export_player_agent_picks(self) -> dict:
        map_dict = self.a.map_dict
        agent_pick_dict = {}
        for item in map_dict["players"]:
            player_name = item["player"]["ign"]
            agent_id = item["agentId"]
            agent_name = self.a.agent_data[str(agent_id)]["name"]
            agent_pick_dict[player_name] = agent_name
        return agent_pick_dict

    def export_player_details(self) -> dict:
        map_dict = self.a.map_dict
        details_dict = {}
        for item in map_dict["players"]:
            player_name = item["player"]["ign"]
            agent_id = item["agentId"]
            agent_name = self.a.agent_data[str(agent_id)]["name"]
            player_id = item["playerId"]
            details_dict[player_id] = {"agent_name": agent_name, "player_name": player_name}
        return details_dict

    def export_player_names(self):
        """
        Export the player names in format of a dictionary
        :return:    {'ban': {'gained': 0, 'lost': 0, 'delta': 0},
                    'Frosty': {'gained': 0, 'lost': 0, 'delta': 0},
                    'Genghsta': {'gained': 0, 'lost': 0, 'delta': 0},
                    'HUYNH': {'gained': 0, 'lost': 0, 'delta': 0},
        """
        return {
            value["name"]["ign"]: {"gained": 0, "lost": 0, "delta": 0} for item, value in self.a.current_status.items()
        }


def __main():
    a = analyser_pool.acquire()
    a.set_match(65588)
    ae = AnalyserExporter(a)
    a = ae.export_round_events()
    b = ae.export_player_agent_picks()
    c = ae.export_player_details()
    print(a, b, c)


if __name__ == "__main__":
    __main()
