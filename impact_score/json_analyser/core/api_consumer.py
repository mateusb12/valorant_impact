import os

import requests

from impact_score.json_analyser.wrap.env_loader import load_environment_tokens

load_environment_tokens()


def __generate_api_link(match_id: int):
    prefix = os.environ["API_TOKEN_A"]
    suffix = os.environ["API_TOKEN_B"]
    return f"{prefix}{match_id}{suffix}"


def get_match_info(match_id: int):
    match_link = __generate_api_link(match_id)
    response = requests.get(match_link)
    return response.json()


def get_impact_details(match_id: int):
    prefix = os.environ["IMPACT_TOKEN"]
    match_link = f"{prefix}{match_id}"
    response = requests.get(match_link)
    return response.json()


if __name__ == "__main__":
    print(get_match_info(45117))
    # print(os.environ)
