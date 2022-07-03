import json

from impact_score.imports.os_slash import get_slash_type
from impact_score.path_reference.folder_ref import valorant_model_reference

sl = get_slash_type()
model_folder = valorant_model_reference()


def load_weapon_data():
    weapon_file = open(f'{model_folder}{sl}weapon_table.json')
    return json.load(weapon_file)


def load_agent_data():
    agent_file = open(f'{model_folder}{sl}agent_table.json')
    return json.load(agent_file)


def load_map_data():
    map_file = open(f'{model_folder}{sl}map_table.json')
    return json.load(map_file)
