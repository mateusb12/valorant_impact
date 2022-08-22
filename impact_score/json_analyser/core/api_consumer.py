import os

import requests

from impact_score.json_analyser.wrap.env_loader import load_environment_tokens

load_environment_tokens()


def __generate_api_link(match_id: int):
    prefix = os.environ["API_TOKEN_A"]
    suffix = os.environ["API_TOKEN_B"]
    return f"{prefix}{match_id}{suffix}"


def request_http_match_data(match_id: int):
    match_link = __generate_api_link(match_id)
    print(f"Request link: {match_link}")
    response = requests.get(match_link)
    return response.json()


def get_impact_details(match_id: int):
    prefix = os.environ["IMPACT_TOKEN"]
    match_link = f"{prefix}{match_id}"
    response = requests.get(match_link)
    return response.json()


if __name__ == "__main__":
    print(request_http_match_data(45117))
    # print(os.environ)
