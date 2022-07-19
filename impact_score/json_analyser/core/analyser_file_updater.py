import json
from pathlib import Path

import requests
from collections import OrderedDict

from termcolor import colored

from impact_score.path_reference.folder_ref import valorant_model_reference
from analyser_file_loader import sl


def __content_api_call() -> dict:
    link = "https://backend-dev.rib.gg/v1/content"
    response = requests.get(link)
    return response.json()


def __order_dict(input_dict: dict) -> dict:
    ordered = OrderedDict(sorted(input_dict.items()))
    ordered = {str(key): value for key, value in ordered.items()}
    return ordered


def __agent_formatting(input_data: dict) -> dict:
    agents_data = input_data["agents"]
    raw = {agent['id']: {"name": agent["name"], "role": agent["role"]} for agent in agents_data}
    return __order_dict(raw)


def __weapon_formatting(input_data: dict) -> dict:
    weapon_data = input_data["weapons"]
    raw = {weapon['id']: {"name": weapon["name"], "price": weapon["price"]} for weapon in weapon_data}
    return __order_dict(raw)


def __map_formatting(input_data: dict) -> dict:
    map_data = input_data["maps"]
    raw = {v_map['id']: {"name": v_map["name"]} for v_map in map_data}
    return __order_dict(raw)


def __ability_formatting(input_data: dict) -> dict:
    ability_data = list(enumerate(input_data["abilities"]))
    raw = {index: {"name": ability} for index, ability in ability_data}
    return __order_dict(raw)


def __save_format_to_file(input_dict: dict, filename: str):
    model_folder = valorant_model_reference()
    file_ref = Path(f"{model_folder}{sl}{filename}")
    with open(file_ref, "w") as file:
        file.write(json.dumps(input_dict, indent=4))
        print(colored(f"File {filename} successfully saved!", "green"))


def update_abilities_content():
    data = __content_api_call()
    abilities = __ability_formatting(data)
    __save_format_to_file(abilities, "abilities.json")
    print(colored("Abilities successfully updated!", "green"))


def __main():
    update_abilities_content()


if __name__ == "__main__":
    __main()
