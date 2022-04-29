import requests


def generate_api_link(match_id: int):
    return f"https://backend-dev.rib.gg/v1/matches/{match_id}/ml-details"


def get_match_info(match_id: int):
    match_link = generate_api_link(match_id)
    response = requests.get(match_link)
    return response.json()


def get_impact_details(match_id: int):
    match_link = f"https://impact-score.herokuapp.com/get_match_impact/{match_id}"
    response = requests.get(match_link)
    return response.json()


if __name__ == "__main__":
    print(get_match_info(45117))
