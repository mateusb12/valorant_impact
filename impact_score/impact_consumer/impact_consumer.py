import time

from matplotlib import ticker
from matplotlib.lines import Line2D

from impact_score.json_analyser.wrap.analyser_exporter import AnalyserExporter
from impact_score.json_analyser.pool.analyser_pool import CoreAnalyser
from impact_score.json_analyser.core.api_consumer import get_impact_details
import matplotlib.pyplot as plt

import pandas as pd


def export_impact(core_analyser: CoreAnalyser, exporter: AnalyserExporter, prob_df: pd.DataFrame) -> dict:
    """
    Export the impact of each player in a match.
    :param prob_df:
    :param core_analyser:
    :param exporter:
    :param match_id: The match id. (60206)
    :param input_analyser: Analyser object instance.
    :return: Dictionary containing event details. For example:
    {
        "round_1": [
            {
                "author": "Crashies",
                "victim": "Nivera",
                "event": "kill",
                "impact": "0.039",
                "probability_before": "0.2318",
                "probability_after": "0.2709"
                "timing": "26185",
    """
    analyser = core_analyser
    details = exporter.export_player_details()
    max_round = analyser.round_amount
    # random_ids = [int(round(3500 + (7000 - 3500) * random())) for _ in range(2000)]
    # prob_df = pd.DataFrame(export_probabilities(match_id))
    # prob_before = pd.Series(prob_df["Probability_before_event"].values, index=prob_df["EventID"]).to_dict()
    prob_before = prob_df["Probability_before_event"].to_list()
    prob_after = prob_df["Probability_after_event"].to_list()
    impact = prob_df["Impact"].to_list()
    match_impact_dict = {f"Round_{i}": [] for i in range(1, max_round + 1)}
    for item in range(1, max_round + 1):
        analyser.choose_round(item)
        for index, event in enumerate(analyser.round_events):
            id_pool = [event['kill_id'], event['bomb_id'], event['res_id']]
            event_id = next(filter(None, id_pool), None)
            # if event_id is None:
            # event_id = random_ids.pop()
            print(index)
            event["event_id"] = event_id
            event["probability_before"] = prob_before[index]
            event["probability_after"] = prob_after[index]
            event["impact"] = impact[index]
            author_id = event["author"]
            victim_id = event["victim"]
            weapon_id = event["weapon_id"]
            if author_id is not None:
                event["author"] = details[author_id]["player_name"]
                event["author_agent"] = details[author_id]["agent_name"]
            if victim_id is not None:
                event["victim"] = details[victim_id]["player_name"]
                event["victim_agent"] = details[victim_id]["agent_name"]
            if weapon_id is not None:
                event["weapon_name"] = analyser.weapon_data[f"{weapon_id}"]["name"]
            match_impact_dict[f"Round_{item}"].append(event)
    return match_impact_dict


# def export_players_impact(match_id: int, input_analyser: Analyser, **kwargs) -> Union[int, dict[Any, int]]:
#     """
#     Export the impact of each player in a match.
#     :param match_id: The match id. (60206)
#     :param input_analyser: Analyser object instance.
#     :param kwargs: player_name="crashies"
#     :return: Dictionary with impact for each player, unless kwargs player_name is set. Example:
#     {
#         "keznit": 0.9838,
#         "Nivera": 1.141,
#         "Jamppi": 3.176,
#         "Mazino": 1.852,
#         "ScreaM": 0.988
#     }
#     """
#     match_data = export_impact(match_id, input_analyser)
#     player_impact_dict = {}
#
#     for round_n in match_data.values():
#         for event in round_n:
#             author = event['author']
#             if author not in player_impact_dict and author is not None:
#                 player_impact_dict[author] = 0
#             if author is not None:
#                 impact = float(event['impact'])
#                 player_impact_dict[author] += impact
#
#     if "player_name" in kwargs:
#         return player_impact_dict[kwargs["player_name"]]
#     else:
#         return player_impact_dict


def export_probability_points(match_id: int) -> dict:
    """
    Export the probability points of each player in a match.
    :param match_id:
    :return: Dict with the following format
    {
        "Round_1": {
            "probability_points": [0.4976, 0.4672, 0.3551, 0.2318, 0.2709, 0.4709],
            "timestamp_points": [0, 8299, 42780, 44737, 56215, 63842, 64286, 92686]
            "kill_feed_points": ['keznit Ghost ScreaM', 'keznit Ghost soulcas', 'Nivera headhunter NagZ',
             'Jamppi Classic keznit', 'Mazino Classic Nivera', 'Delz1k Frenzy L1NK'],
        }
    }
    """
    data = get_impact_details(match_id)
    round_amount = max(int(key[6:]) for key in data.keys())
    map_probability_points = {f"Round_{i}": None for i in range(1, round_amount + 1)}

    def get_single_round_plots(round_n: int) -> dict:
        probability_points = []
        kill_feed_points = []
        timestamp_points = []
        for event in data[f"Round_{round_n}"]:
            probability_points.extend((float(event["probability_before"]), float(event["probability_after"])))
            # timing = event["timing"] / 1000
            timing = event["timing"]
            timestamp_points.extend((timing, timing))

            if event['author'] is not None:
                kill_feed_string = ""
                if event['event'] == 'kill':
                    means = "b"
                    if event['damage_type'] == 'weapon':
                        try:
                            means = event['weapon_name']
                        except KeyError:
                            means = "Overdrive"
                    elif event['damage_type'] == 'ability':
                        means = event['ability']
                    kill_feed_string = f"{event['author']} {means} {event['victim']}"
                elif event['event'] == 'plant':
                    kill_feed_string = f"{event['author']} planted the bomb"
                elif event['event'] == 'defuse':
                    kill_feed_string = f"{event['author']} defused the bomb"
                elif event['event'] == 'revival':
                    kill_feed_string = f"{event['author']} revived {event['victim']}"
                kill_feed_points.append(kill_feed_string)

        return {"probability_points": probability_points, "timestamp_points": timestamp_points,
                "kill_feed_points": kill_feed_points}

    for j in range(1, round_amount + 1):
        map_probability_points[f"Round_{j}"] = get_single_round_plots(j)

    return map_probability_points


def generate_probability_dataframe(data: dict) -> pd.DataFrame:
    """
    Generate a dataframe with the probability points of each player in a match.
    :param data: output from export_probability_points()
    :return: timestamp: [0, 8.299, 42.780, 44.737, 56.215, 63.842, 64.286, 92.686]
             probability_points: [0.4976, 0.4672, 0.3551, 0.2318, 0.2709, 0.4709],
            kill_feed_points: ['keznit Ghost ScreaM', 'keznit Ghost soulcas', 'Nivera headhunter NagZ', etc]
            labels: [A, B, C, D, E, F, G]
    """

    # data = export_probability_points(match_id)[f"Round_{round_number}"]

    def intersperse(lst, item):
        result = [item] * (len(lst) * 2 - 1)
        result[0::2] = lst
        return result

    labels = [chr(i) for i in range(65, 74)]
    labels = intersperse(labels, None)[:-1]

    kill_feed = intersperse(data["kill_feed_points"], None)
    kill_feed.insert(0, "Round Start")
    kill_feed.insert(1, None)
    kill_feed.insert(len(kill_feed), None)

    return pd.DataFrame({"timestamp": data["timestamp_points"], "probability": data["probability_points"],
                         "label": labels, "kill_feed": kill_feed})


def generate_probability_graph(match_id: int, round_number: int) -> None:
    data = export_probability_points(match_id)[f"Round_{round_number}"]
    y_values = data["probability_points"]
    x_values = data["timestamp_points"]
    df = generate_probability_dataframe(data)
    plt.figure(figsize=(12, 5))
    plt.title('Attackers probability over time')
    plt.xlabel('Time (s)')
    plt.ylabel('Probability (%)')
    markers_on = list(range(1, len(x_values), 2))
    ax = plt.gca()
    n = list(df["label"])

    for i, txt in enumerate(n):
        if txt is None:
            plt.text(x_values[i], y_values[i] + 0.007, n[i - 1], horizontalalignment='center',
                     verticalalignment='bottom',
                     fontsize=12)

    legend_elements = []

    for event in df["kill_feed"]:
        if event is not None:
            label_index = chr(65 + len(legend_elements))
            new_label = f"{label_index} → {event}"
            new_element = Line2D([0], [0], marker='o', color='w', label=new_label, markerfacecolor='r', markersize=10)
            legend_elements.append(new_element)
    plt.legend(handles=legend_elements, loc=(1.04, 0.45))
    plt.grid(linewidth=0.4)

    plt.plot(df["timestamp"], df["probability"], color="red", linewidth=1.0,
             marker='o', markersize=6, markerfacecolor="black", markevery=markers_on)

    plt.axhline(y=0, color='white', linestyle='-')

    bomb_query = df[df['kill_feed'].str.contains("bomb") == True]
    if len(bomb_query) == 1:
        bomb_stamp = bomb_query["timestamp"].to_list()[0]
        plt.axvline(x=bomb_stamp, color='pink', linestyle='-', linewidth=2.0)

    formatter = ticker.FuncFormatter(lambda ms, x: time.strftime('%M:%S', time.gmtime(ms // 1000)))
    ax.xaxis.set_major_formatter(formatter)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
    plt.show()


if __name__ == "__main__":
    # test = export_impact(match_id=60206, input_analyser=Analyser())
    # test2 = export_players_impact(match_id=60206, input_analyser=Analyser())
    # test3 = export_probability_points(match_id=65588)
    aux = 5 + 1
    # test4 = export_impact(match_id=65588, input_analyser=a)
    print("hey")
