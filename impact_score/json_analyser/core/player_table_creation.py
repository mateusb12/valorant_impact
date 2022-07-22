import dataclasses

from impact_score.json_analyser.core.api_consumer import get_match_info


@dataclasses.dataclass
class PlayerTableCreator:
    map: dict
    economies: dict
    locations: dict
    round_number: int = 1

    def pick_round(self, input_round_number: int):
        self.round_number = input_round_number

    def create_player_table(self) -> dict:
        ign_table = {
            b["playerId"]: {"ign": b["player"]["ign"], "team_number": b["teamNumber"]}
            for b in self.map["players"]
        }

        player_dict = {}
        current_round_economies = [item for item in self.economies if item["roundNumber"] == self.round_number]
        current_round_locations = [item for item in self.locations if item["roundNumber"] == self.round_number]
        first_timing = current_round_locations[0]["roundTimeMillis"]
        initial_locations = [item for item in current_round_locations if item["roundTimeMillis"] == first_timing]
        current_round_economies.sort(key=lambda x: x["playerId"])
        initial_locations.sort(key=lambda x: x["playerId"])

        for economy, location in zip(current_round_economies, initial_locations):
            player_id = economy["playerId"]
            aux = {"name": ign_table[player_id],
                   "agentId": economy["agentId"],
                   "combatScore": economy["score"],
                   "weaponId": economy["weaponId"],
                   "shieldId": economy["armorId"],
                   "loadoutValue": economy["loadoutValue"],
                   "spentCreds": economy["spentCreds"],
                   "remainingCreds": economy["remainingCreds"],
                   "attacking_side": True,
                   "team_number": ign_table[player_id]["team_number"],
                   "timing": location["roundTimeMillis"],
                   "locationX": location["locationX"],
                   "locationY": location["locationY"],
                   "viewRadians": location["viewRadians"],
                   "playerId": player_id,
                   "alive": True}
            player_dict[player_id] = aux
        return player_dict


def __main():
    match_id = 74099
    data = get_match_info(74099)
    map_data = [item for item in data["series"]["seriesById"]["matches"] if item["id"] == match_id][0]
    location_data = data["matches"]["matchDetails"]["locations"]
    economy_data = data["matches"]["matchDetails"]["economies"]
    ptc = PlayerTableCreator(map=map_data, economies=economy_data, locations=location_data)
    pt = ptc.create_player_table()
    print("done")


if __name__ == "__main__":
    __main()
