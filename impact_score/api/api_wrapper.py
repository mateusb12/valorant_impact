import pathlib
import pandas as pd
import os

from impact_score.impact.match_analysis import RoundReplay
from flask import Flask, jsonify
from timeit import default_timer as timer
from pathlib import Path


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
    """
    Json format
    {
        "match_id": 44795,
        "round": 1,
        "side": "atk"
    }
    """
    match_id = input_match_id
    rr_instance = RoundReplay()
    rr_instance.set_match(match_id)
    total_rounds = rr_instance.analyser.round_amount
    proba_plot = []
    for i in range(1, total_rounds):
        rr_instance.choose_round(i)
        proba_plot.append(rr_instance.get_round_probability(side="atk"))
    round_impact_df = pd.concat(proba_plot, axis=0)
    dict_to_return = round_impact_df.to_dict('list')
    return jsonify(dict_to_return)


def webscrapping_fix():
    current_folder = Path(os.getcwd())
    webscrapping_folder = current_folder.parent
    root_folder = webscrapping_folder.parent
    return str(root_folder)


end = timer()
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
