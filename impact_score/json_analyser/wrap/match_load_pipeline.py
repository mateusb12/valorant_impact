import os

from impact_score.json_analyser.core.api_consumer import request_http_match_data
from impact_score.json_analyser.wrap.env_loader import load_environment_tokens
from impact_score.path_reference.folder_ref import existing_env_file, existing_env_keys
from webscrapping.json_checker import load_match_json


def load_match_info(input_match_id: int) -> dict:
    if existing_file := existing_env_file():
        load_environment_tokens()
    if existing_keys := existing_env_keys():
        return request_http_match_data(input_match_id)
    else:
        return load_match_json(input_match_id)

