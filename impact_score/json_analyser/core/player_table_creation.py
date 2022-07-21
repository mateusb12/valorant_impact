import dataclasses

from impact_score.json_analyser.core.api_consumer import get_match_info


@dataclasses.dataclass
class PlayerTableCreator:
    map: dict
    economies: dict
    locations: dict

    def create_player_table(self) -> dict:
        ign_table = {
            b["playerId"]: {"ign": b["player"]["ign"], "team_number": b["teamNumber"]}
            for b in self.map["players"]
        }

        attacking_first_team = self.map["attackingFirstTeamNumber"]

        player_dict = {}

        for item in self.economies:
            player_id = item["playerId"]
            aux = {"name": ign_table[player_id],
                   "agentId": item["agentId"],
                   "combatScore": item["score"],
                   "weaponId": item["weaponId"],
                   "shieldId": item["armorId"],
                   "loadoutValue": item["loadoutValue"],
                   "spentCreds": item["spentCreds"],
                   "remainingCreds": item["remainingCreds"],
                   "attacking_side": ign_table[player_id]["team_number"] == attacking_first_team,
                   "team_number": ign_table[player_id]["team_number"],
                   "alive": True}
            player_dict[player_id] = aux
            # if item["roundNumber"] == 1:
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
