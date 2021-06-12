import json

agent_table = {1: "Breach", 2: "Raze", 3: "Cypher", 4: "Sova", 5: "Killjoy", 6: "Viper",
               7: "Phoenix", 8: "Brimstone", 9: "Sage", 10: "Reyna", 11: "Omen", 12: "Jett",
               13: "Skye", 14: "Yoru", 15: "Astra"}

f = open('matches/script_a.json')
data = json.load(f)
final_json = {}

match_id = data["series"]["seriesById"]["id"]
event_id = data["series"]["seriesById"]["eventId"]
best_of = data["series"]["seriesById"]["bestOf"]


with open('matches/result.json', 'w') as fp:
    json.dump(final_json, fp)

# team_blue_id = data["series"]["seriesById"]["team1Id"]
# team_red_id = data["series"]["seriesById"]["team2Id"]
#
# first_match_id = data["series"]["seriesById"]["matches"][0]["id"]
# first_match_map_id = data["series"]["seriesById"]["matches"][0]["map"]["id"]
# first_match_map_name = data["series"]["seriesById"]["matches"][0]["map"]["name"]
#
match_index = 0
raw_players = data["series"]["seriesById"]["matches"][match_index]["players"]
player_table = {i["playerId"]: i for i in raw_players}

aux = data["series"]["seriesById"]["matches"][match_index]["rounds"]
round_table = {i["id"]: i for i in aux}

economy_rounds = {
    j["roundId"] for j in data["matches"]["matchDetails"]["economies"]
}

event_rounds = {
    j["roundId"] for j in data["matches"]["matchDetails"]["events"]
}

print(len(economy_rounds))
# event_dict = {"events": []}
# for updt in round_table:
#     round_table[updt].update(event_dict)
#
# desired_round = 401750
#
# for i in data["matches"]["matchDetails"]["events"]:
#     round_id = i["roundId"]
#     if round_id in round_table:
#         to_add = i.copy()
#         to_add.pop("roundId", None)
#         round_table[round_id]["events"].append(to_add)
#         banana = 5 + 3
#
apple = 5 + 3