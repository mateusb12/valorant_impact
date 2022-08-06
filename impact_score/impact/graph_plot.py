from line_profiler_pycharm import profile

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
    def __init__(self):
        self.match_id, self.analyser, self.prob_df, self.ae, self.details_df = None, None, None, None, None
        self.plot_data, self.kills_data_df, self.ability_data, self.round_number, self.ax = None, None, None, None, None
        self.chosen_side = None

    def set_match(self, input_match_id: int):
        self.match_id: int = input_match_id
        self.analyser: CoreAnalyser = get_analyser(self.match_id)
        self.prob_df = pd.DataFrame(export_probabilities(self.match_id))
        self.ae = AnalyserExporter(self.analyser)
        self.details_df = export_impact(self.analyser, self.ae, self.prob_df)
        self.plot_data: dict = {}
        self.kills_data_df: pd.DataFrame = pd.DataFrame()
        self.ability_data: dict = self.analyser.ability_data
        self.ability_data["-1"] = 0
        self.round_number = None
        self.ax = None

    def choose_round(self, round_number: int):
        self.round_number = round_number

    def choose_side(self, input_side: str):
        self.chosen_side = input_side

    def get_kill_dataframe(self) -> pd.DataFrame:
        kills_data_df = self.details_df[self.details_df["round_number"] == self.round_number].copy()
        tag_pot = []
        zip_tag = zip(kills_data_df["author"], kills_data_df["means"], kills_data_df["victim"], kills_data_df["event"])
        for author, means, victim, event in zip_tag:
            if event == "kill":
                tag_pot.append(f"{author} {means} {victim}")
            elif event == "plant":
                tag_pot.append(f"{author} planted the spike")
            elif event == "defuse":
                tag_pot.append(f"{author} defused the spike")
            elif event == "revival":
                tag_pot.append(f"{author} revived {victim}")
            elif event == "start":
                tag_pot.append("Round started")
        size = len(kills_data_df)
        kills_data_df["stamp"] = [chr(i) for i in range(65, 65 + size)]
        color_mapping = {"start": "green",
                         "kill": "lightseagreen",
                         "plant": "mediumvioletred",
                         "defuse": "mediumvioletred",
                         "revival": "brown"}
        kills_data_df["color"] = kills_data_df["event"].map(color_mapping)
        kills_data_df["tag"] = tag_pot
        return kills_data_df

    def get_probability_points(self, input_data_df: pd.DataFrame) -> dict:
        single_stamps = input_data_df["timing"].tolist()
        duplicated_stamps = [int(ele) for index, ele in enumerate(single_stamps) for i in range(2)]
        color_list = input_data_df["color"].tolist()
        tag_list = input_data_df["tag"].tolist()
        stamp_list = input_data_df["stamp"].tolist()
        for index in range(len(color_list)):
            color_list.insert(index * 2, None)
            tag_list.insert(index * 2, None)
            stamp_list.insert(index * 2, None)
        full_tag = [f"{stamp} → {tag}" for stamp, tag in zip(stamp_list, tag_list)]
        la = input_data_df["Probability_before_event"].tolist()
        lb = input_data_df["Probability_after_event"].tolist()
        if self.chosen_side == "def":
            la = [1-item for item in la]
            lb = [1-item for item in lb]
        interpolated_probs = []
        for index in range(len(la)):
            interpolated_probs.extend((float(la[index]), float(lb[index])))
        return {"Round time": duplicated_stamps,
                "Win_probability": [100 * round(elem, 2) for elem in interpolated_probs],
                "Colors": color_list,
                "Tags": full_tag,
                "Stamps": stamp_list}

    def setup_graph_data(self):
        self.kills_data_df = self.get_kill_dataframe()
        self.plot_data = self.get_probability_points(self.kills_data_df)

    @staticmethod
    def get_color_pattern(chosen_side: str) -> tuple[str, str]:
        line_color_dict = {"atk": "red", "def": "midnightblue"}
        title_dict = {"atk": "Attack", "def": "Defense"}
        return line_color_dict[chosen_side], title_dict[chosen_side]

    def plot_round(self, **kwargs):
        desired_round_number = kwargs.get("round_number", None)
        self.chosen_side = kwargs.get("side", "atk")
        self.choose_round(desired_round_number)
        self.setup_graph_data()

        fig = plt.figure(figsize=(16, 7))
        fig.tight_layout()
        plt.rcParams.update({'font.size': 13})

        line_color, title = self.get_color_pattern(self.chosen_side)
        grid_color = "black"

        plt.plot(self.plot_data["Round time"], self.plot_data["Win_probability"],
                 color=line_color, zorder=0)

        self.ax = plt.gca()
        # self.ax.set_facecolor('grey')
        self.ax.set_facecolor("#dbd9d9a6")
        self.ax.spines["left"].set_position(("data", -2))
        self.ax.set_xlabel('Round time (s)', rotation=0, labelpad=10)
        self.ax.set_ylabel('Win probability (%)', rotation=90, labelpad=20)
        self.ax.grid(b=True, which="major", color=grid_color,
                     linestyle="-", zorder=0, linewidth=.2, alpha=.75)

        self.apply_time_formatter()
        self.apply_markers()
        self.plot_round_events()

        plt.title(f"{title} win probability over time")
        plt.show()

    def apply_time_formatter(self):
        formatter = mpl_ticker.FuncFormatter(lambda ms, x: time.strftime('%M:%S', time.gmtime(ms // 1000)))
        self.ax.xaxis.set_major_formatter(formatter)

    def apply_markers(self):
        x_data = self.plot_data["Round time"]
        y_data = self.plot_data["Win_probability"]
        color_data = self.plot_data["Colors"]
        stamp_data = self.plot_data["Stamps"]
        y_offset = 1.5
        x_offset = -.3
        for round_time, win_probability, color, stamp in zip(x_data, y_data, color_data, stamp_data):
            if color is not None:
                self.ax.scatter(x=round_time, y=win_probability, color=color,
                                edgecolor="white", marker="o", s=70, zorder=2, linewidth=3)
                coords = (round_time-x_offset, win_probability+y_offset)
                self.ax.annotate(text=stamp, xy=(round_time, win_probability),
                                 xytext=coords)

    def plot_round_events(self):
        x_data = self.plot_data["Round time"]
        y_data = self.plot_data["Win_probability"]
        color_data = self.plot_data["Colors"]
        label_data = self.plot_data["Tags"]
        for round_time, win_probability, color, label in zip(x_data, y_data, color_data, label_data):
            if color is not None:
                self.ax.scatter(x=round_time, y=win_probability,
                                color=color, edgecolor="w", marker="o", s=70, label=label, zorder=2)
        plt.legend(framealpha=1, frameon=True, facecolor="#c9c9c9", bbox_to_anchor=(1.31, 0.82))


if __name__ == "__main__":
    match_id = 74680
    gp = GraphPlotter()
    gp.set_match(match_id)
    gp.plot_round(round_number=21, side="def")
