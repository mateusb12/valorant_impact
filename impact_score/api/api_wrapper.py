import pathlib
import pandas as pd
import os

from impact_score.impact_consumer.impact_consumer import export_impact
from impact_score.impact.match_analysis import RoundReplay
from flask import Flask, jsonify, request
from timeit import default_timer as timer
from pathlib import Path

from impact_score.json_analyser.analyse_json import Analyser

start = timer()
app = Flask(__name__)


def get_webscrapping_path():
    current_folder = pathlib.Path(os.getcwd())
    return current_folder.parent


@app.route("/")
def homepage():
    raw_dict = {"a": "b", "b": "c"}
    return jsonify(raw_dict)


@app.route('/get_round_impact/<input_match_id>', methods=["GET"])
def get_round_impact(input_match_id):
    match_id = int(input_match_id)
    rr_instance = RoundReplay()
    rr_instance.set_match(match_id)
    total_rounds = rr_instance.analyser.round_amount
    proba_plot = []
    for i in range(1, total_rounds + 1):
        rr_instance.choose_round(i)
        proba_plot.append(rr_instance.get_round_probability(side="atk"))
    round_impact_df = pd.concat(proba_plot, axis=0)
    dict_to_return = round_impact_df.to_dict('list')
    return jsonify(dict_to_return)


@app.route('/get_match_impact/<input_match_id>', methods=["GET"])
def get_match_impact(input_match_id):
    details_dict = export_impact(input_match_id, Analyser())
    return jsonify(details_dict)


@app.route('/get_single_impact/', methods=["POST"])
def test_api():
    """
    Json format
    {
        "match_id": 45222,
        "round": 1,
    }
    """
    input_json = request.get_json(force=True)
    input_dict = dict(input_json)
    input_match_id = input_dict["match_id"]
    input_round = input_dict["round"]
    rr_instance_2 = RoundReplay()
    rr_instance_2.set_match(input_match_id)
    rr_instance_2.choose_round(input_round)
    proba_plot = [rr_instance_2.get_round_probability(side="atk")]
    round_impact_df = pd.concat(proba_plot, axis=0)
    dict_to_return = round_impact_df.to_dict('list')
    return jsonify(dict_to_return)


@app.route('/test_probability/', methods=["POST"])
def test_probability():
    """
    Json format
    {
        "RegularTime": 35,
        "SpikeTime": 0,
        "Loadout_diff": 500,
        "ATK_kills": 1,
        "ATK_Initiator": 1,
        "ATK_Duelist": 1,
        "ATK_Sentinel": 1,
        "ATK_Controller": 1,
        "DEF_Kills": 1,
        "DEF_Initiator": 0,
        "DEF_Duelist": 2,
        "DEF_Sentinel": 1,
        "DEF_Controller": 1,
        "DEF_operators": 1
    }
    """
    input_json = request.get_json(force=True)
    input_dict = dict(input_json)
    rr_instance = RoundReplay()
    test_model = rr_instance.model
    aux_df = pd.DataFrame([input_dict])
    raw_proba = test_model.predict_proba(aux_df)[0][1]
    rounded_proba = 100 * round(raw_proba, 2)
    return jsonify({"probability": f"{rounded_proba}%"})


def webscrapping_fix():
    current_folder = Path(os.getcwd())
    webscrapping_folder = current_folder.parent
    root_folder = webscrapping_folder.parent
    return str(root_folder)


end = timer()
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
