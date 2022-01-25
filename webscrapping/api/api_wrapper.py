import pathlib
import sys

from termcolor import colored
import fix_missing_webscrapping_folder
import os

from webscrapping.impact.match_analysis import RoundReplay
from webscrapping.model.analyse_json import Analyser
from flask import Flask, jsonify, request
from timeit import default_timer as timer
from pathlib import Path

from webscrapping.model.lgbm_model import get_trained_model

start = timer()
app = Flask(__name__)
analyser = Analyser()
vv = get_trained_model()
rr = RoundReplay(vv.model)


def get_webscrapping_path():
    current_folder = pathlib.Path(os.getcwd())
    return current_folder.parent


@app.route("/")
def homepage():
    raw_dict = {"a": "b", "b": "c"}
    return jsonify(raw_dict)


@app.route('/set_match', methods=["POST"])
def set_match():
    input_json = request.get_json(force=True)
    analyser.set_match(0, json=input_json)
    analyser.set_config(round=1)
    match = analyser.match_id
    print(f"match → {match}")
    rr.set_match(match)
    return f"Match {match} successfully set!", 201


@app.route('/set_round/<round_number>', methods=["POST"])
def set_round(round_number):
    print(f"round → {round_number}")
    rr.choose_round(round_number)
    return f"Round {round_number} successfully set!", 201


@app.route('/get_clutchy_rounds/<side>', methods=["GET"])
def get_clutchy_rounds(side):
    """
    :param side: "atk" or "def
    """
    clutchy_rounds = rr.get_clutchy_rounds(side)
    return jsonify(clutchy_rounds)


@app.route('/get_round_probability/<input_side>', methods=["GET"])
def get_round_probability(input_side):
    """
    :param input_side: "atk" or "def
    """
    round_probability_df = rr.get_round_probability(side=input_side, add_events=True)
    dict_to_return = round_probability_df.to_dict('list')
    return jsonify(dict_to_return)


@app.route('/get_round_impact/', methods=["POST"])
def get_round_impact():
    """
    Json format
    {
        "match_id": 44795,
        "round": 1,
        "side": "atk"
    }
    """
    input_json = request.get_json(force=True)
    print(input_json)
    match_id = input_json["match_id"]
    round_number = input_json["round"]
    side = input_json["side"]
    rr_instance = RoundReplay(vv.model)
    rr_instance.set_match(match_id)
    rr_instance.choose_round(round_number)
    round_impact_df = rr_instance.get_round_probability(side=side)
    dict_to_return = round_impact_df.to_dict('list')
    return jsonify(dict_to_return)


@app.route("/get_player_most_impactful_rounds/", methods=["POST"])
def get_player_most_impactful_rounds():
    input_json = request.get_json(force=True)
    player_name = input_json["Player"]
    try:
        player_most_impactful_rounds_df = rr.get_player_most_impactful_rounds(player_name)
        dict_to_return = player_most_impactful_rounds_df.to_dict('list')
        return jsonify(dict_to_return)
    except KeyError:
        return f"Could not find [{player_name}] in match #{analyser.match_id}", 404


@app.route('/get_match_gamestate', methods=["GET"])
def get_match_gamestate():
    gamestate_df = analyser.export_df()
    dict_to_return = gamestate_df.to_dict('list')
    return jsonify(dict_to_return)


@app.route('/get_map_impact', methods=["GET"])
def get_map_impact():
    map_impact_df = rr.get_map_impact_dataframe()
    dict_to_return = map_impact_df.to_dict('list')
    return jsonify(dict_to_return)


def webscrapping_fix():
    current_folder = Path(os.getcwd())
    webscrapping_folder = current_folder.parent
    root_folder = webscrapping_folder.parent
    return str(root_folder)


end = timer()
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
