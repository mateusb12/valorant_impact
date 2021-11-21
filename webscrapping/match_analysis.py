import os
from typing import List
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
import matplotlib.lines as mlines

from sklearn.model_selection import train_test_split, cross_val_score
import lightgbm

from webscrapping.analyse_json import Analyser
from webscrapping.wrapper.single_match_downloader import SingleMatchDownloader


class RoundReplay:
    def __init__(self, match_id: int, input_df: pd.DataFrame, input_model: lightgbm.LGBMClassifier):
        self.df = input_df
        self.match_id = match_id
        self.query = input_df.query("MatchID == {}".format(match_id))
        self.round_table = self.get_round_table()
        self.analyser = Analyser("{}.json".format(match_id))
        self.model = input_model
        self.chosen_round = None

    def choose_round(self, round_number: int):
        self.chosen_round = round_number

    def get_round_table(self) -> dict:
        g = self.query[["RoundNumber", "RoundID"]]
        g.drop_duplicates()
        return dict(zip(g.RoundNumber, g.RoundID))

    def get_round_winners(self) -> dict:
        g = self.query[["RoundNumber", "FinalWinner"]]
        g.drop_duplicates()
        return dict(zip(g.RoundNumber, g.FinalWinner))

    def get_round_id(self, round_index: int) -> int:
        return self.round_table[round_index]

    def get_round_dataframe(self, round_index: int):
        return self.df.query('RoundID == {}'.format(self.get_round_id(round_index)))

    def get_plant_stamp(self, round_number: int) -> int or None:
        rdf = self.get_round_dataframe(round_number)
        if max(rdf.SpikeTime) == 0:
            return None
        for i in rdf.iterrows():
            current_index = i[0]
            current_time = i[1].RegularTime
            next_time = tuple(rdf["RegularTime"].loc[[current_index + 1]])[0]
            if current_time != 0 and next_time == 0:
                return round(tuple(rdf["RoundTime"].loc[[current_index]])[0] / 1000, 0)
        return None

    def get_clutchy_rounds(self, chosen_side: str) -> dict:
        dtb = self.get_round_table()
        round_amount = max(dtb, key=dtb.get)
        minimum_probabilities_dict = {}
        original_round = self.chosen_round
        for i in range(1, round_amount + 1):
            self.chosen_round = i
            aux = self.get_round_probability(side=chosen_side)
            winner = list(aux["Final Winner"])[0]
            if winner == chosen_side:
                round_id = list(aux["Round"])[0]
                min_prob = min(list(aux["Win_probability"]))
                minimum_probabilities_dict[round_id] = min_prob

        self.chosen_round = original_round
        return {
            k: v
            for k, v in sorted(
                minimum_probabilities_dict.items(), key=lambda item: item[1]
            )
        }

    def get_round_probability(self, **kwargs):
        """
        :param kwargs: round_number: int
                       side: str, "atk" or "def"
                       add_events: boolean
        :return: pd.DataFrame table with the probabilities of each round
        """
        round_number = self.chosen_round
        old_table = self.get_round_dataframe(round_number)
        table = old_table[["ATK_wealth", "DEF_wealth", "ATK_alive", "DEF_alive",
                           "DEF_has_OP", "Def_has_Odin",
                           "RegularTime", "SpikeTime", "MapName"]]
        current_map = table.MapName.max()
        map_names = ["Ascent", "Bind", "Breeze", "Haven", "Icebox", "Split"]
        map_names.remove(current_map)
        table = pd.get_dummies(table, columns=['MapName'])
        for item in map_names:
            table['MapName_{}'.format(item)] = 0
        side = kwargs["side"]
        attack_pred = None
        if side == "atk":
            attack_pred = [round(i[1] * 100, 2) for i in self.model.predict_proba(table)]
        elif side == "def":
            attack_pred = [100 - round(i[1] * 100, 2) for i in self.model.predict_proba(table)]
        table["Win_probability"] = attack_pred
        raw_timings = [round(x / 1000, 2) for x in old_table.RoundTime]
        integer_timings = [int(round(x / 1000, 0)) for x in old_table.RoundTime]
        table["Round time"] = raw_timings
        margin_differences = [(x - attack_pred[i - 1]) for i, x in enumerate(attack_pred)][1:]
        margin_differences.insert(0, 0)
        table["Difference (%)"] = margin_differences
        winner = self.get_round_winners()[round_number]
        tag_dict = {0: "def", 1: "atk"}
        table["Final Winner"] = tag_dict[winner]
        table["Round"] = round_number
        table["Integer time"] = integer_timings
        # table["Stamp"] = [chr(x) for x in range(65, 65 + len(integer_timings))]
        table = table[["Round time", "Win_probability", "Difference (%)", "Final Winner", "Round",
                       "Integer time"]]
        if "add_events" in kwargs and kwargs["add_events"]:
            extra_df = self.round_events_dataframe()
            table.reset_index(drop=True, inplace=True)
            extra_df.reset_index(drop=True, inplace=True)
            table = pd.concat([table, extra_df], axis=1)
            wp = list(table["Win_probability"])
            new_diff = [x - wp[i - 1] for i, x in enumerate(wp)][1:]
            new_diff.insert(0, 0)
            table["Difference (%)"] = new_diff

            table = table[["Round", "Round time", "Stamps", "Difference (%)", "Actors", "Means", "Victims",
                           "Win_probability", "Final Winner"]]

        return table

    def round_events_dataframe(self) -> pd.DataFrame:
        stamps = ["A"]
        actors = ["None"]
        means = ["None"]
        victims = ["None"]
        story = self.get_round_story()
        for key, value in story.items():
            action_list = value.split(" ")
            # 'spike' not in action_list
            if 'Round' not in action_list and 'spike' not in action_list:
                stamps.append(key)
                actors.append(action_list[0])
                if "[" in action_list[1]:
                    means.append(action_list[1][1:-1])
                else:
                    means.append(action_list[1])
                victims.append(action_list[2])
            elif 'spike' in action_list:
                stamps.append(key)
                actors.append(action_list[0])
                means.append("spike")
                victims.append("spike")
        return pd.DataFrame({"Stamps": stamps, "Actors": actors, "Means": means, "Victims": victims})

    def get_round_story(self) -> dict:
        round_story = []
        for i in self.analyser.export_round_events():
            if i["roundNumber"] == self.chosen_round:
                output = "None"
                if i["eventType"] == "kill":
                    output = "{} [{}] {}".format(i["killer_name"], i["weapon"]["name"], i["victim_name"])
                elif i["eventType"] == "plant":
                    output = "{} {}".format(i["killer_name"], "planted the spike")
                elif i["eventType"] == "defuse":
                    output = "{} {}".format(i["killer_name"], "defused the spike")
                elif i["eventType"] == "revival":
                    output = "{} revived {}".format(i["killer_name"], i["victim_name"])
                else:
                    apple = 5
                    output = "{} {}".format(i["killer_name"], "exception")
                round_story.append(output)
        rs_dict = {"A": "Round start"}
        for i, x in enumerate(round_story):
            rs_dict[self.letterify(i + 1, displace=True)] = x
        return rs_dict

    @staticmethod
    def letterify(number: int, **kwargs):
        if "displace" in kwargs and kwargs["displace"]:
            return chr(ord("B") + number - 1)
        else:
            return chr(ord("A") + number - 1)

    def plot_round(self, **kwargs):
        round_number = self.chosen_round
        chosen_side = kwargs["side"]
        marker_margin = 0
        if "marker_margin" in kwargs:
            marker_margin = kwargs["marker_margin"]

        plt.figure(figsize=(12, 5))
        color_dict = {"atk": "red", "def": "blue"}
        marker_dict = {"atk": "#511C29", "def": "darkblue"}
        round_data = self.get_round_probability(side=chosen_side)

        sns.set_context(rc={'patch.linewidth': 2.0})
        sns.set(font_scale=1.3)
        ax = sns.lineplot(x="Round time", y="Win_probability", data=round_data,
                          linewidth=0, zorder=0, color=color_dict[chosen_side])
        ax.set(xlabel='Round time (s)', ylabel='Win probability (%)')
        ax.xaxis.labelpad = 10
        ax.yaxis.labelpad = 12
        ax.grid(linewidth=.4, color='gray', zorder=0)
        title_dict = {"atk": "Attack", "def": "Defense"}
        plt.title("{} win probability over time".format(title_dict[chosen_side]))
        ax.lines[0].set_marker("o")
        ax.lines[0].set_markersize(9)
        plt.axhline(y=0, color="black")
        plt.axhline(y=50, linestyle="-", color="grey", linewidth=1.5)
        plt.grid(True, which='both', linestyle='--', zorder=0, linewidth=0.9)

        x_data = list(round_data["Round time"])
        y_data = list(round_data["Win_probability"])
        marker_colors = [marker_dict[chosen_side]] * len(x_data)

        def annotation(content: str, x_coord: float, y_coord: float, orientation: str):
            font_size = 14
            down_table = {"atk": -7 + marker_margin, "def": -5 + marker_margin}
            down_orientation = down_table[chosen_side]
            if orientation == "up":
                plt.gca().annotate(content, xy=(18, 61), xytext=(x_coord - 0.5, y_coord + 2.95), fontsize=font_size,
                                   color='green', weight='bold')
            elif orientation == "down":
                plt.gca().annotate(content, xy=(18, 61), xytext=(x_coord - 0.35, y_coord + down_orientation),
                                   fontsize=font_size, color='green', weight='bold')

        prob_table = self.get_round_probability(side=chosen_side)[["Round time", "Win_probability"]]
        for index, item in enumerate(prob_table.iterrows()):
            fixed_index = index + 1
            aux = list(item[1])
            label = self.letterify(fixed_index)
            annotation(self.letterify(fixed_index), aux[0], aux[1], "down")

        plt.plot(x_data, y_data, linestyle="-", linewidth=1.7, color=color_dict[chosen_side], zorder=0)
        for point in zip(x_data, y_data, marker_colors):
            plt.scatter(point[0], point[1], color=point[2], s=60)

        plant = self.get_plant_stamp(round_number)
        if plant is not None:
            plt.axvline(x=plant)

        locs = ["upper left", "lower left", "center right"]
        blue_line = mlines.Line2D([], [], color='green', marker='o',
                                  markersize=7, label='Blue stars')
        label_list = [key + " → " + value for key, value in self.get_round_story().items()]
        plt.gca().legend(
            labels=label_list,
            handles=[blue_line] * len(label_list),
            loc=(1.1, 0.15))

        plt.show()

        # annotation(20, 39.70, "down")

        arrow = {'facecolor': 'tab:blue', 'shrink': 0.05, 'alpha': 0.75}
        # plt.gca().annotate('nzr 2 frenzy kills', xy=(5.5, 61), xytext=(-8, 70), arrowprops=arrow, fontsize=13, color='green', weight='bold')
        # plt.gca().annotate('khalil stinger kill', xy=(16.8, 91), xytext=(-1, 90), arrowprops=arrow, fontsize=13, color='green', weight='bold')
        # plt.gca().annotate('zaks deleta o xand, \nmas o round já estava encaminhado', xy=(24, 79), xytext=(16, 60), arrowprops=arrow, fontsize=13, color='red', weight='bold')
        # plt.gca().annotate('FURIA only has 20% chance \n of winning this round', xy=(0, 17), xytext=(10, 5), arrowprops=arrow, fontsize=13, color='red', weight='bold')


class MatchReplay:
    def __init__(self, match_id: int, input_df: pd.DataFrame):
        self.df: pd.DataFrame = input_df
        self.match_id: int = match_id
        self.query: pd.DataFrame = input_df.query('MatchID == {}'.format(match_id))

    def get_round_table(self) -> dict:
        g = self.query[["RoundNumber", "RoundID"]]
        g.drop_duplicates()
        return dict(zip(g.RoundNumber, g.RoundID))

    def get_atk_scores(self) -> List[int]:
        dfm = list(self.get_round_winners().values())
        score_dict = {'atk': 0, 'def': 0}
        atk_scores = []

        for i in dfm[:12]:
            if i == 1:
                score_dict['atk'] += 1
            atk_scores.append(score_dict['atk'])
        for j in dfm[12:24]:
            if j == 0:
                score_dict['atk'] += 1
            atk_scores.append(score_dict['atk'])

        return atk_scores

    def get_round_winners(self) -> dict:
        g = self.query[["RoundNumber", "FinalWinner"]]
        g.drop_duplicates()
        return dict(zip(g.RoundNumber, g.FinalWinner))

    def get_def_scores(self) -> List[int]:
        dfm = list(self.get_round_winners().values())
        score_dict = {'atk': 0, 'def': 0}
        def_scores = []

        for i in dfm[:12]:
            if i == 0:
                score_dict['def'] += 1
            def_scores.append(score_dict['def'])
        for j in dfm[12:24]:
            if j == 1:
                score_dict['def'] += 1
            def_scores.append(score_dict['def'])

        return def_scores

    def get_match_winner(self) -> int:
        atks = self.get_atk_scores()
        defs = self.get_def_scores()

        winner = 0
        if atks[-1] == 12 and defs[-1] == 12:
            winner = 2
        elif atks[-1] == 13:
            winner = 1
        elif defs[-1] == 13:
            winner = 0
        return winner

    def generate_match_dataframe(self) -> pd.DataFrame:
        r_number = pd.Series(self.get_round_table().keys())
        r_atk = pd.Series(self.get_atk_scores())
        r_def = pd.Series(self.get_def_scores())
        r_winner = pd.Series([self.get_match_winner()] * len(r_number))
        r_ids = pd.Series([self.match_id] * len(r_number))
        r_atk_bank = pd.Series(self.get_atk_bank())
        r_def_bank = pd.Series(self.get_def_bank())

        frame = {'MatchID': r_ids, 'RoundNumber': r_number, 'AtkScore': r_atk, 'DefScore': r_def,
                 'ATK_Bank': r_atk_bank, 'DEF_Bank': r_def_bank,
                 'FinalWinner': r_winner}

        d_frame = pd.DataFrame(frame)
        d_frame.dropna()

        return d_frame

    def get_all_matches(self) -> set:
        return set(self.df.MatchID)

    def get_atk_bank(self) -> List[int]:
        return [
            max(self.query.query('RoundNumber == {}'.format(r)).ATK_bank)
            for r in self.get_round_table().keys()
        ]

    def get_def_bank(self) -> List[int]:
        return [
            max(self.query.query('RoundNumber == {}'.format(r)).DEF_bank)
            for r in self.get_round_table().keys()
        ]

    def get_big_dataframe(self):
        df_list = []
        match_indexes = list(self.get_all_matches())

        for i in match_indexes:
            self.match_id = i
            print(i)
            self.query: pd.DataFrame = self.df.query('MatchID == {}'.format(i))
            df_list.append(self.generate_match_dataframe())

        merged = pd.concat(df_list)
        merged.dropna(inplace=True)
        merged["AtkScore"] = merged["AtkScore"].astype(int)
        merged["DefScore"] = merged["DefScore"].astype(int)

        return merged

    def export_big_dataframe(self):
        big_df = self.get_big_dataframe()
        big_df.to_csv(r'matches\rounds\matches_csv.csv', index=False)
        print('SUCCESS!')


def generate_prediction_model(input_dataset: pd.DataFrame) -> lightgbm.LGBMClassifier:
    params = pd.read_csv('model_params.csv', index_col=False)
    params = params.to_dict('records')[0]
    df = input_dataset[["ATK_wealth", "DEF_wealth", "ATK_alive", "DEF_alive", "DEF_has_OP", "Def_has_Odin",
                        "RegularTime", "SpikeTime", "MapName", "FinalWinner"]]
    df = pd.get_dummies(df, columns=['MapName'])
    X = df.drop(['FinalWinner'], axis='columns')
    Y = df.FinalWinner
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, train_size=0.8, test_size=0.2, random_state=15)

    model = lightgbm.LGBMClassifier(bagging_freq=params["bagging_freq"], min_data_in_leaf=params["min_data_in_leaf"],
                                    max_depth=params["max_depth"],
                                    learning_rate=params["learning_rate"], num_leaves=params["num_leaves"],
                                    num_threads=params["num_threads"],
                                    min_sum_hessian_in_leaf=params["min_sum_hessian_in_leaf"])
    model.fit(X_train, Y_train)
    return model


def generate_round_replay_example(match_id: int, series_id: int) -> RoundReplay:
    print("match → {} series → {}".format(match_id, series_id))
    smd = SingleMatchDownloader(series_id)
    smd.download_full_series()

    raw_df = pd.read_csv('matches\\rounds\\na_merged.csv', index_col=False)
    analysis_df = pd.read_csv('matches\\exports\\{}.csv'.format(match_id), index_col=False)
    model = generate_prediction_model(raw_df)

    return RoundReplay(match_id, analysis_df, model)


if __name__ == "__main__":
    # https://rib.gg/series/4103 Sentinels BO5 score 3-2
    # https://rib.gg/series/18716 Liquid BO5 score 3-1
    # https://rib.gg/series/18718 Furia BO5 score 3-0
    # https://rib.gg/series/3173 Sentinels BO1
    match = 42039
    series = 19728
    rr = generate_round_replay_example(match, series)
    rr.choose_round(2)
    rr.get_round_probability(side="atk", add_events=True)
    #rr.plot_round(side="atk")

    # q = rr.get_round_probability(4, side="atk")
    # apple = 5 + 1

    # rr.plot_round(4, side="atk")

    # path2 = 'D:\\Documents\\GitHub\\Classification_datascience\\webscrapping\\matches\\rounds\\combined_csv.csv'
    # data = pd.read_csv('{}'.format(path2))
    #
    # mr = MatchReplay(match, data)
    # mr.export_big_dataframe()
