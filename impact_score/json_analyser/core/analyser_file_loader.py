import json

from impact_score.imports.os_slash import get_slash_type
from impact_score.path_reference.folder_ref import valorant_model_reference

sl = get_slash_type()
model_folder = valorant_model_reference()


def load_weapon_data() -> dict:
    weapon_file = open(f'{model_folder}{sl}weapon_table.json')
    return json.load(weapon_file)


def load_agent_data() -> dict:
    agent_file = open(f'{model_folder}{sl}agent_table.json')
    return json.load(agent_file)


def load_map_data() -> dict:
    map_file = open(f'{model_folder}{sl}map_table.json')
    return json.load(map_file)


def load_ability_data() -> dict:
    ability_file = open(f'{model_folder}{sl}abilities.json')
    return json.load(ability_file)


def __main():
    aux = load_map_data()
    print(aux)


if __name__ == "__main__":
    __main()
