import pandas as pd

from impact_score.impact.match_analysis import RoundReplay


def export_probabilities(input_match_id):
    match_id = int(input_match_id)
    rr_instance = RoundReplay()
    rr_instance.set_match(match_id)
    total_rounds = rr_instance.analyser.round_amount
    proba_plot = []
    for i in range(1, total_rounds + 1):
        rr_instance.choose_round(i)
        proba_plot.append(rr_instance.get_round_probability(side="atk"))
    round_impact_df = pd.concat(proba_plot, axis=0)
    return round_impact_df.to_dict('list')


if __name__ == "__main__":
    export_probabilities(64606)
