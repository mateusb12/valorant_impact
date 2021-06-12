import json

agent_table = {1: "Breach", 2: "Raze", 3: "Cypher", 4: "Sova", 5: "Killjoy", 6: "Viper",
               7: "Phoenix", 8: "Brimstone", 9: "Sage", 10: "Reyna", 11: "Omen", 12: "Jett",
               13: "Skye", 14: "Yoru", 15: "Astra"}

f = open('matches/script_a.json')
data = json.load(f)
final_json = {}

weapon_file = open('matches/model/weapon_table.json')
weapon_data = json.load(weapon_file)

chosen_map = 0
chosen_round = 401753

attacking_team = data["series"]["seriesById"]["matches"][chosen_map]["attackingFirstTeamNumber"]

ign_table = {
    b["playerId"]: {"ign": b["player"]["ign"], "team_number": b["teamNumber"]}
    for b in data["series"]["seriesById"]["matches"][chosen_map]["players"]
}

player_status = {}

for i in data["matches"]["matchDetails"]["economies"]:
    if i["roundId"] == chosen_round:
        tp = i
        player_id = i["playerId"]
        aux = {"name": ign_table[player_id],
               "agentId": i["agentId"],
               "combatScore": i["score"],
               "weaponId": i["weaponId"],
               "shieldId": i["armorId"],
               "loadoutValue": i["loadoutValue"],
               "attacking_side": ign_table[player_id]["team_number"] == attacking_team,
               "alive": True}
        player_status[player_id] = aux

event_table = []

atk_gun_price = 0
def_gun_price = 0
atk_alive = 0
def_alive = 0
def_has_operator = 0
def_has_odin = 0
spike_time = 0

for key, value in player_status.items():
    weapon_id = str(value["weaponId"])
    weapon_tuple = weapon_data[weapon_id]
    weapon_price = weapon_tuple["price"]
    if value["attacking_side"]:
        atk_gun_price += int(weapon_price)
        if value["alive"]:
            atk_alive += 1
    else:
        def_gun_price += int(weapon_price)
        if value["alive"]:
            def_alive += 1
            if weapon_id == "15":
                def_has_operator = 1
            elif weapon_id == "2":
                def_has_odin = 1

event_table.append((chosen_round, 0, atk_gun_price,
                    def_gun_price, atk_alive, def_alive,
                    def_has_operator, def_has_odin))


match_id = data["series"]["seriesById"]["id"]
event_id = data["series"]["seriesById"]["eventId"]
best_of = data["series"]["seriesById"]["bestOf"]