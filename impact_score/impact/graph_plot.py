from impact_score.impact.match_analysis import RoundReplay
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker as mpl_ticker
import time

from impact_score.impact_consumer.impact_consumer import export_impact
from impact_score.impact_consumer.probability_consumer import export_probabilities
from impact_score.json_analyser.pool.analyser_pool import CoreAnalyser
from impact_score.json_analyser.wrap.analyser_exporter import AnalyserExporter
from impact_score.json_analyser.wrap.analyser_loader import get_analyser


class GraphPlotter:
    def __init__(self, input_match_id: int):
        self.match_id: int = input_match_id
        self.analyser: CoreAnalyser = get_analyser(self.match_id)
        self.prob_df = pd.DataFrame(export_probabilities(self.match_id))
        self.ae = AnalyserExporter(self.analyser)
        self.details_dict = export_impact(self.analyser, self.ae, self.prob_df)
        self.plot_data: dict = {}
        self.kills_data_df: pd.DataFrame = pd.DataFrame()
        self.ax = None

    def get_kill_dataframe(self) -> pd.DataFrame:
        round_number = 3
        content = self.details_dict[f"Round_{round_number}"]
        kills_data_df = pd.DataFrame(content)
        kills_data_df = kills_data_df.fillna(0)
        integer_columns = ["weapon_id", "kill_id", "bomb_id", "event_id", "res_id", "RoundTime"]
        kills_data_df["RoundTime"] = round(kills_data_df["timing"] / 1000)
        for column in integer_columns:
            kills_data_df[column] = kills_data_df[column].astype(int)
        size = len(kills_data_df)
        kills_data_df["stamp"] = [chr(i) for i in range(65, 65 + size)]
        color_mapping = {"start": "green",
                         "kill": "yellow",
                         "plant": "purple",
                         "defuse": "purple",
                         "revival": "brown"}
        kills_data_df["color"] = kills_data_df["event"].map(color_mapping)
        return kills_data_df

    @staticmethod
    def get_probability_points(input_data_df: pd.DataFrame) -> dict:
        single_stamps = input_data_df["timing"].tolist()
        duplicated_stamps = [int(ele) for index, ele in enumerate(single_stamps) for i in range(2)]
        color_list = input_data_df["color"].tolist()
        for index in range(len(color_list)):
            color_list.insert(index * 2, None)
        la = input_data_df["probability_before"].tolist()
        lb = input_data_df["probability_after"].tolist()
        interpolated_probs = []
        for index in range(len(la)):
            interpolated_probs.extend((float(la[index]), float(lb[index])))
        return {"Round time": duplicated_stamps,
                "Win_probability": [100*round(elem, 2) for elem in interpolated_probs],
                "Colors": color_list}

    def setup_graph_data(self):
        self.kills_data_df = self.get_kill_dataframe()
        self.plot_data = self.get_probability_points(self.kills_data_df)

    def base_plot(self):
        self.setup_graph_data()
        chosen_side = "atk"
        color_dict = {"atk": "red", "def": "blue"}
        title_dict = {"atk": "Attack", "def": "Defense"}

        fig = plt.figure(figsize=(14, 7))
        fig.tight_layout()
        plt.rcParams.update({'font.size': 13})

        plt.plot(gp.plot_data["Round time"], gp.plot_data["Win_probability"], color=color_dict[chosen_side])
        self.ax = plt.gca()
        self.ax.spines["left"].set_position(("data", -2))
        self.ax.set_xlabel('Round time (s)', rotation=0, labelpad=10)
        self.ax.set_ylabel('Win probability (%)', rotation=90, labelpad=20)
        self.ax.grid(b=True, which="major", color="orange", linestyle="-", zorder=0, linewidth=.1, alpha=0.5)

        self.apply_time_formatter()
        self.apply_markers()

        plt.title(f"{title_dict[chosen_side]} win probability over time")
        plt.show()

    def apply_time_formatter(self):
        formatter = mpl_ticker.FuncFormatter(lambda ms, x: time.strftime('%M:%S', time.gmtime(ms // 1000)))
        self.ax.xaxis.set_major_formatter(formatter)

    def apply_markers(self):
        x_data = self.plot_data["Round time"]
        y_data = self.plot_data["Win_probability"]
        color_data = self.plot_data["Colors"]
        for round_time, win_probability, color in zip(x_data, y_data, color_data):
            if color is not None:
                self.ax.scatter(x=round_time, y=win_probability, color=color, edgecolor="w", marker="o", s=70)

    def get_round_events(self):
        authors = self.kills_data_df["author"].tolist()
        victims = self.kills_data_df["victim"].tolist()
        events = self.kills_data_df["event"].tolist()

    # def plot_round_old(self, **kwargs):
    #     round_number = self.rr.chosen_round
    #     chosen_side = kwargs["side"]
    #     marker_margin = 0
    #     if "marker_margin" in kwargs:
    #         marker_margin = kwargs["marker_margin"]
    #
    #     plt.figure(figsize=(12, 5))
    #     color_dict = {"atk": "red", "def": "blue"}
    #     marker_dict = {"atk": "#511C29", "def": "darkblue"}
    #     round_data = self.rr.get_round_probability(side=chosen_side)
    #     details_dict = export_impact(self.rr.analyser, self.ae, round_data)
    #     content = details_dict[f"Round_{round_number}"]
    #     # content = export_impact(self.rr.match_id, self.rr.analyser)[f"Round_{round_number}"]
    #     kills_data_df = pd.DataFrame(content)
    #     kills_data_df["RoundTime"] = kills_data_df["timing"] / 1000
    #     single_stamps = kills_data_df["timing"].tolist()
    #     duplicated_stamps = [int(ele) for index, ele in enumerate(single_stamps) for i in range(2)]
    #     la = kills_data_df["probability_before"].tolist()
    #     lb = kills_data_df["probability_after"].tolist()
    #     interpolated_probs = []
    #     for index in range(len(la)):
    #         interpolated_probs.append(float(la[index]))
    #         interpolated_probs.append(float(lb[index]))
    #
    #     plot_data = {"Round time": duplicated_stamps,
    #     "Win_probability": ['%.2f' % elem for elem in interpolated_probs]}
    #
    #     sns.set_context(rc={'patch.linewidth': 2.0})
    #     sns.set(font_scale=1.3)
    #     ax = sns.lineplot(x="Round time", y="Win_probability", data=plot_data,
    #                       linewidth=0, zorder=0, color=color_dict[chosen_side])
    #     ax.set(xlabel='Round time (s)', ylabel='Win probability (%)')
    #     ax.xaxis.labelpad = 10
    #     ax.yaxis.labelpad = 12
    #     ax.grid(linewidth=.4, color='gray', zorder=0)
    #     title_dict = {"atk": "Attack", "def": "Defense"}
    #     plt.title("{} win probability over time".format(title_dict[chosen_side]))
    #     ax.lines[0].set_marker("o")
    #     ax.lines[0].set_markersize(9)
    #     plt.axhline(y=0, color="black")
    #     plt.axhline(y=50, linestyle="-", color="grey", linewidth=1.5)
    #     plt.grid(True, which='both', linestyle='--', zorder=0, linewidth=0.9)
    #     plt.show()
    #
    #     # x_data = list(round_data["Round time"])
    #     # y_data = list(round_data["Win_probability"])
    #     x_data = plot_data["Round time"]
    #     y_data = plot_data["Win_probability"]
    #     marker_colors = [marker_dict[chosen_side]] * len(x_data)
    #
    #     def annotation(content: str, x_coord: float, y_coord: float, orientation: str):
    #         font_size = 14
    #         down_table = {"atk": -7 + marker_margin, "def": -5 + marker_margin}
    #         down_orientation = down_table[chosen_side]
    #         if orientation == "down":
    #             plt.gca().annotate(content, xy=(18, 61), xytext=(x_coord - 0.35, y_coord + down_orientation),
    #                                fontsize=font_size, color='green', weight='bold')
    #         elif orientation == "up":
    #             plt.gca().annotate(content, xy=(18, 61), xytext=(x_coord - 0.5, y_coord + 2.95), fontsize=font_size,
    #                                color='green', weight='bold')
    #
    #     prob_table = self.rr.get_round_probability(side=chosen_side)[["Round time", "Win_probability"]]
    #     for index, item in enumerate(prob_table.iterrows()):
    #         fixed_index = index + 1
    #         aux = list(item[1])
    #         label = self.rr.letterify(fixed_index)
    #         annotation(self.rr.letterify(fixed_index), aux[0], aux[1], "down")
    #
    #     plt.plot(x_data, y_data, linestyle="-", linewidth=1.7, color=color_dict[chosen_side], zorder=0)
    #     for point in zip(x_data, y_data, marker_colors):
    #         plt.scatter(point[0], point[1], color=point[2], s=60)
    #
    #     plant = self.rr.get_plant_stamp(round_number)
    #     if plant is not None:
    #         plt.axvline(x=plant)
    #
    #     locs = ["upper left", "lower left", "center right"]
    #     blue_line = mlines.Line2D([], [], color='green', marker='o',
    #                               markersize=7, label='Blue stars')
    #     label_list = [key + " → " + value for key, value in self.rr.get_round_story().items()]
    #     plt.gca().legend(
    #         labels=label_list,
    #         handles=[blue_line] * len(label_list),
    #         loc=(1.1, 0.15))
    #
    #     plt.show()
    #
    #     # annotation(20, 39.70, "down")
    #
    #     arrow = {'facecolor': 'tab:blue', 'shrink': 0.05, 'alpha': 0.75}
    #     # plt.gca().annotate('nzr 2 frenzy kills', xy=(5.5, 61), xytext=(-8, 70), arrowprops=arrow, fontsize=13,
    #     # color='green', weight='bold')
    #     # plt.gca().annotate('khalil stinger kill', xy=(16.8, 91), xytext=(-1, 90), arrowprops=arrow, fontsize=13,
    #     # color='green', weight='bold')
    #     # plt.gca().annotate('zaks deleta o xand, \nmas o round já estava encaminhado', xy=(24, 79), xytext=(16, 60),
    #     # arrowprops=arrow, fontsize=13, color='red', weight='bold')
    #     # plt.gca().annotate('FURIA only has 20% chance \n of winning this round', xy=(0, 17), xytext=(10, 5),
    #     # arrowprops=arrow, fontsize=13, color='red', weight='bold')


if __name__ == "__main__":
    match_id = 60206
    gp = GraphPlotter(match_id)
    gp.setup_graph_data()
    gp.base_plot()
