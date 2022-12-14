import pathlib
from json import dump

import pandas as pd
import os

import requests

from impact_score.impact_consumer.impact_consumer import export_impact
from impact_score.impact_consumer.probability_consumer import export_probabilities
from impact_score.impact.match_analysis import RoundReplay
from flask import Flask, jsonify, request
from timeit import default_timer as timer
from pathlib import Path

from impact_score.json_analyser.wrap.analyser_exporter import AnalyserExporter
from impact_score.json_analyser.wrap.analyser_loader import get_analyser

start = timer()
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
print("Starting API")


def get_webscrapping_path():
    current_folder = pathlib.Path(os.getcwd())
    return current_folder.parent


@app.route("/")
def homepage():
    raw_dict = {"a": "b", "b": "c"}
    return jsonify(raw_dict)


@app.route('/get_round_impact/<input_match_id>', methods=["GET"])
def get_round_impact(input_match_id):
    """
    Export a json with round details
    :param input_match_id:
    :return: json format example
    {
        "Round_1": {
            "ability": "null",
            "author": "keznit",
            "author_agent": "Jett",
            "damage_type": "weapon",
            "event": "kill",
            "impact": "0.112",
            "probability_before": "0.467",
            "probability_after": "0.355",
            "round_number": 1,
            "timing": 21510,
            "victim": "Jamppi",
            "victim_agent": "Killjoy",
            "weapon_id": 12,
            "weapon_name": "Ghost"
        }
    }
    """
    dict_to_return = export_probabilities(input_match_id)
    return jsonify(dict_to_return)


@app.route('/get_match_impact/<input_match_id>', methods=["GET"])
def get_match_impact(input_match_id):
    match_id = int(input_match_id)
    analyser = get_analyser(match_id)
    ae = AnalyserExporter(analyser)
    prob_df = pd.DataFrame(export_probabilities(match_id))
    details_df = export_impact(analyser, ae, prob_df)
    details_dict = details_df.to_dict(orient='records')
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


@app.route('/get_agent_table', methods=["GET"])
def get_agent_table():
    link = "https://backend-prod.rib.gg/v1/content"
    response = requests.get(link)
    updated_json = dict(response.json())
    updated_agents = updated_json["agents"]
    agent_dict = {agent["id"]: {"name": agent["name"], "role": agent["role"]} for agent in updated_agents}
    agent_dict = {k: agent_dict[k] for k in sorted(agent_dict)}
    agent_dict = {str(k): agent_dict[k] for k in agent_dict}
    return jsonify(agent_dict)


@app.route('/update_agent_table', methods=["POST"])
def update_agent_table():
    """
    This function updates the agent_table.json file in the valorant_model folder.
    It does this by making a GET request and then writing response to the agent_table.json file.
    """
    link = "https://impact-score.herokuapp.com/get_agent_table"
    response = requests.get(link)
    updated_json = dict(response.json())
    agent_path = Path(Path(os.getcwd()).parent, 'valorant_model', 'agent_table.json')
    with open(agent_path, "w") as outfile:
        dump(updated_json, outfile, indent=2)
    return jsonify({"status": "ok", "new_data": updated_json})


def webscrapping_fix():
    current_folder = Path(os.getcwd())
    webscrapping_folder = current_folder.parent
    root_folder = webscrapping_folder.parent
    return str(root_folder)


end = timer()
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
