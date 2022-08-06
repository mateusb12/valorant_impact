import json
from pathlib import Path

from termcolor import colored

from impact_score.path_reference.folder_ref import json_folder_reference


class MatchNotFoundException(Exception):
    pass


def check_existing_json(match_id: int):
    filename = f"{match_id}.json"
    output_ref = Path(json_folder_reference(), filename)
    if existing := output_ref.exists():
        return True
    print(colored('Error: match file not found. Please download it using get_json() function, from rib_scrapper.py',
                  "yellow"))
    raise MatchNotFoundException(f"Error: could not find json file at [{output_ref}]")


def load_match_json(match_id: int) -> dict:
    filename = f"{match_id}.json"
    output_ref = Path(json_folder_reference(), filename)
    with open(output_ref, "r") as f:
        return json.load(f)


def __main():
    check_existing_json(4999)


if __name__ == "__main__":
    __main()
