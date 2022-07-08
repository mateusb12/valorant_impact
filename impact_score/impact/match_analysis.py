import copy

import pandas as pd
# from line_profiler_pycharm import profile

from sklearn.model_selection import train_test_split
import lightgbm
from termcolor import colored

# from impact_score.impact_consumer.impact_consumer import export_impact
from impact_score.imports.os_slash import get_slash_type
from impact_score.json_analyser.wrap.analyser_exporter import AnalyserExporter
from impact_score.json_analyser.wrap.analyser_loader import get_analyser
from impact_score.json_analyser.pool.analyser_pool import CoreAnalyser
from impact_score.json_analyser.core.analyser_tools import AnalyserTools
from impact_score.json_analyser.wrap.analyser_wrapper import AnalyserWrapper
from impact_score.model.lgbm_loader import load_lgbm
from impact_score.model.lgbm_model import ValorantLGBM

sl = get_slash_type()


class RoundReplay:
    def __init__(self):
        self.match_id = 0
        # self.analyser = Analyser()

        self.vm: ValorantLGBM = load_lgbm()
        self.model: lightgbm.LGBMClassifier = self.vm.model
        self.chosen_round, self.player_impact, self.round_amount, self.df, self.round_table, self.query = [None] * 6
        self.feature_df, self.events_data, self.side, self.side_dict, self.explosion_millis = [None] * 5
        self.analyser, self.exporter, self.wrapper, self.tools = [None] * 4

    def set_match(self, match_id: int):
        self.match_id = match_id
        self.analyser: CoreAnalyser = get_analyser(match_id)
        self.exporter: AnalyserExporter = AnalyserExporter(self.analyser)
        self.tools: AnalyserTools = AnalyserTools(self.analyser)
        self.wrapper: AnalyserWrapper = AnalyserWrapper(self.analyser)
        self.player_impact = self.exporter.export_player_names()
        self.round_amount = self.analyser.get_last_round()
        self.df = self.wrapper.export_df()
        self.feature_df = self.df[self.vm.get_model_features()]
        self.query = self.df.query(f"MatchID == {match_id}")
        self.round_table = self.tools.get_round_table()
        self.chosen_round = None
        event_list = self.analyser.data["matches"]["matchDetails"]["events"]
        aux_dict = {i: [] for i in range(1, self.round_amount + 1)}
        for item in self.analyser.data["matches"]["matchDetails"]["events"]:
            aux_dict[item["roundNumber"]].append(item)
        self.events_data = aux_dict
        self.side_dict = dict(zip(self.df.RoundNumber, self.df.FinalWinner))

    def choose_round(self, round_number: int):
        self.chosen_round = round_number
        print(colored(f"Round {round_number} selected", "yellow"))

    def is_player_in_this_match(self, player_name: str) -> bool:
        return player_name in self.player_impact

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
        return self.df.query(f'RoundID == {self.get_round_id(round_index)}')

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
        return dict(
            sorted(minimum_probabilities_dict.items(), key=lambda item: item[1])
        )

    @staticmethod
    def displace_column(input_df: pd.DataFrame, column_name: str):
        column = list(input_df[column_name])
        last = column[-1]
        displaced = column[1:]
        displaced.append(last)
        input_df[column_name] = displaced

    def get_displaced_preds(self, input_table: pd.DataFrame) -> dict:
        displaced_table = input_table.copy()
        self.displace_column(displaced_table, "RegularTime")
        self.displace_column(displaced_table, "SpikeTime")
        first_row = pd.DataFrame(input_table.iloc[0]).transpose()
        displaced_table = pd.concat([first_row, displaced_table]).reset_index(drop=True)
        displaced_table = displaced_table[:-1]
        raw_default_pred = self.model.predict_proba(input_table)
        default_pred = raw_default_pred[:, 1]
        raw_displaced_pred = self.model.predict_proba(displaced_table)
        displaced_pred = raw_displaced_pred[:, 1]
        return {"default": default_pred, "displaced": displaced_pred}

    def handle_special_situation(self, input_table: pd.DataFrame, **kwargs):
        situation_type = kwargs["situation"]
        events = kwargs["events"]
        last_index = input_table.index[-1]

        if situation_type == "clean_defuse":
            new_proba = 1 if self.side == "def" else 0
            input_table.loc[last_index, 'Probability_after_event'] = new_proba
        elif situation_type == "clean_kill":
            current_winner_number = self.side_dict[self.chosen_round]
            current_winner = "def" if current_winner_number == 0 else "atk"
            matching_winner = self.side == current_winner
            new_proba = 1 if matching_winner else 0
            input_table.loc[last_index, 'Probability_after_event'] = new_proba
        else:
            query = input_table.query("RegularTime == 0 and SpikeTime <= 0")
            query_indexes = list(query.index)
            beginning_position, new_proba = None, None
            if situation_type in ("after_defuse", "timeout"):
                beginning_position = 0 if situation_type == "timeout" else 1
                new_proba = 1 if self.side == "def" else 0
            elif situation_type == "after_explosion":
                beginning_position = 1 if len(query_indexes) > 1 else 0
                new_proba = 1 if self.side == "atk" else 0
            last_element = query_indexes[-1]
            first_element = query_indexes[beginning_position]
            input_table.loc[first_element:last_element, 'Probability_before_event'] = new_proba
            input_table.loc[first_element:last_element, 'Probability_after_event'] = new_proba

            if situation_type == "after_defuse":
                defuse_index = events.index("defuse")
                input_table.loc[defuse_index, 'Probability_after_event'] = new_proba

    # @profile
    def get_round_probability(self, **kwargs):
        """
        :param kwargs: round_number: int
                       side: str, "atk" or "def"
                       add_events: boolean
        :return: pd.DataFrame table with the probabilities of each round
        """
        round_number = self.chosen_round
        old_table = self.get_round_dataframe(round_number)
        all_features = self.model.feature_name_
        table = old_table[all_features].copy()
        displaced_dict = self.get_displaced_preds(table)
        displaced_pred = displaced_dict["displaced"]
        default_pred = displaced_dict["default"]
        table["Probability_before_event"] = displaced_pred
        table["Probability_after_event"] = default_pred
        side = kwargs["side"]
        self.side = side
        if side == "def":
            table['Probability_before_event'] = table['Probability_before_event'].apply(lambda y: 1 - y)
            table['Probability_after_event'] = table['Probability_after_event'].apply(lambda y: 1 - y)
        table["Round"] = round_number
        current_round_events = self.events_data[self.chosen_round]
        round_millis = [x["roundTimeMillis"] for x in current_round_events]
        max_millis = max(round_millis)
        event_ids = []
        for x in current_round_events:
            raw_ids = [x["killId"], x["bombId"], x["resId"]]
            query_id = [x for x in raw_ids if x is not None]
            if len(query_id) != 1:
                event_ids.append(0)
                Exception("Error in query")
            else:
                event_ids.append(query_id[0])
        table["EventID"] = event_ids
        event_types = [x["eventType"] for x in current_round_events]
        after_explosion = False
        if "plant" in event_types:
            plant_millis = round_millis[event_types.index("plant")]
            self.explosion_millis = plant_millis + 45000
            if max_millis >= self.explosion_millis:
                after_explosion = True

        if "defuse" in event_types:
            situation_type = "clean_defuse" if event_types[-1] == "defuse" else "after_defuse"
        elif after_explosion:
            situation_type = "after_explosion"
        else:
            situation_type = "timeout" if max_millis >= 100000 and "plant" not in event_types else "clean_kill"

        # event_types.insert(0, "start")
        table["EventType"] = event_types

        self.handle_special_situation(table, situation=situation_type, events=event_types)

        table["Impact"] = abs(table["Probability_after_event"] - table["Probability_before_event"])
        table = table[["Round", "EventID", "EventType", "Probability_before_event", "Probability_after_event",
                       "Impact"]]

        if "add_events" in kwargs and kwargs["add_events"]:
            event_df = pd.DataFrame(current_round_events)
            event_df = event_df.fillna(0)
            int_columns = ['killId', 'tradedByKillId', 'tradedForKillId', 'bombId', 'resId',
                           'playerId', 'referencePlayerId', 'weaponId']
            event_df[int_columns] = event_df[int_columns].astype(int)
            weapon_name_data = {int(key): value["name"] for key, value in self.analyser.weapon_data.items()}
            player_data = self.exporter.export_player_details()
            player_names = {key: value["player_name"] for key, value in player_data.items()}
            player_agents = {key: value["agent_name"] for key, value in player_data.items()}
            player_names[0], player_agents[0], weapon_name_data[0] = 0, 0, 0
            table["Killer"] = event_df["playerId"].map(player_names).values
            table["KillerAgent"] = event_df["playerId"].map(player_agents).values
            table["Weapon"] = event_df["weaponId"].map(weapon_name_data).values
            table["Ability"] = event_df["ability"].values
            table["Victim"] = event_df["referencePlayerId"].map(player_names).values
            table["VictimAgent"] = event_df["referencePlayerId"].map(player_agents).values

        table = table.fillna(0)
        return table

    def round_events_dataframe(self) -> pd.DataFrame:
        stamps = ["A"]
        actors = ["None"]
        means = ["None"]
        victims = ["None"]
        story = self.get_round_story()
        for key, value in story.items():
            action_list = value.split(" ")
            if 'Round' not in action_list and 'spike' not in action_list and '[None]' not in action_list:
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
            elif '[None]' in action_list:
                stamps.append(key)
                actors.append(action_list[0])
                means.append("spike")
                victims.append(action_list[0])
        return pd.DataFrame({"Stamps": stamps, "Actors": actors, "Means": means, "Victims": victims})

    def get_round_story(self) -> dict:
        round_story = []
        round_events = self.exporter.export_round_events()
        for i in round_events:
            if i["roundNumber"] == self.chosen_round:
                if i["eventType"] == "kill":
                    output = f'{i["killer_name"]} [{i["weapon"]["name"]}] {i["victim_name"]}'
                elif i["eventType"] == "plant":
                    output = f'{i["killer_name"]} planted the spike'
                elif i["eventType"] == "defuse":
                    output = f'{i["killer_name"]} defused the spike'
                elif i["eventType"] == "revival":
                    output = f'{i["killer_name"]} revived {i["victim_name"]}'
                else:
                    output = f'{i["killer_name"]} exception'
                round_story.append(output)
        rs_dict = {"A": "Round start"}
        for i, x in enumerate(round_story):
            rs_dict[self.letterify(i + 1, displace=True)] = x
        return rs_dict

    def get_round_impact(self) -> dict:
        prob_table = self.get_round_probability(side="def", add_events=True)
        player_impact_table = copy.deepcopy(self.player_impact)
        for index in range(len(prob_table)):
            row = prob_table.iloc[index]
            event_type = row["EventType"]
            if event_type != "start":
                actor = row["Killer"]
                victim = row["Victim"]
                impact_value = row["Impact"]
                player_impact_table[actor]["gained"] += impact_value
                if event_type == "kill":
                    player_impact_table[victim]["lost"] += impact_value

            # means = [row[x] for x in ["Weapon", "Ability"] if row[x] != 0]
            # means = means[0] if means else 0
            # stamp = row["Stamps"]
            # if stamp != "A" and means != "spike":
            #     actor_diff = row["Difference (%)"]
            #     actor = row["Actors"]
            #     victim = row["Victims"]
            #     victim_diff = 0 if means == "revived" else -actor_diff
            #     if actor_diff >= 0:
            #         player_impact_table[actor]["gained"] += actor_diff
            #     else:
            #         player_impact_table[actor]["gained"] += -actor_diff
            #     player_impact_table[victim]["lost"] += abs(victim_diff)
        for key, value in player_impact_table.items():
            value["delta"] = value["gained"] - value["lost"]
        return player_impact_table

    def get_round_impact_dataframe(self) -> pd.DataFrame:
        impact_dict = self.get_round_impact()
        impact_df = pd.DataFrame(impact_dict).T
        impact_df["delta"] = impact_df["gained"] - impact_df["lost"]
        impact_df = impact_df[["gained", "lost", "delta"]]
        return impact_df

    def get_player_most_impactful_rounds(self, player_name: str) -> pd.DataFrame:
        pot = []
        for i in range(1, self.round_amount + 1):
            self.choose_round(i)
            cr = self.get_round_impact_dataframe()
            name = cr.iloc[cr.index.get_loc(player_name)]
            aux["RoundNumber"] = i
            pot.append(name)
        res = pd.DataFrame(pot)
        res["RoundNumber"] = res["RoundNumber"].astype(int)
        res['Name'] = res.index
        res = res[["Name", "RoundNumber", "gained", "lost", "delta"]]
        res = res.sort_values("delta", ascending=False)
        res = res.reset_index(drop=True)
        return res

    def get_map_impact(self) -> dict:
        pi = copy.deepcopy(self.player_impact)
        impact_list = []
        for i in range(1, self.round_amount + 1):
            self.choose_round(i)
            round_impact = self.get_round_impact()
            impact_list.append(round_impact)

        for round_impact in impact_list:
            for key, value in round_impact.items():
                pi[key]["gained"] += value["gained"]
                pi[key]["lost"] += value["lost"]
                pi[key]["delta"] += value["delta"]

        return dict(sorted(pi.items(), key=lambda item: item[1]["delta"], reverse=True))

    def get_map_impact_dataframe(self, **kwargs) -> pd.DataFrame:
        igns = []
        gains = []
        losses = []
        deltas = []
        map_impact = self.get_map_impact()
        for key, value in map_impact.items():
            igns.append(key)
            gains.append(value["gained"])
            losses.append(value["lost"])
            deltas.append(value["delta"])
        match_id = [self.match_id] * len(igns)

        impact_table = {"Name": igns, "Gain": gains, "Lost": losses, "Delta": deltas, "MatchID": match_id}
        aux_impact = pd.DataFrame(impact_table)
        if "agents" in kwargs:
            agent_dict = self.exporter.export_player_agent_picks()
            aux_impact["Agent"] = aux_impact["Name"].map(agent_dict)
        return aux_impact

    @staticmethod
    def letterify(number: int, **kwargs):
        if "displace" in kwargs and kwargs["displace"]:
            return chr(ord("B") + number - 1)
        else:
            return chr(ord("A") + number - 1)


def generate_prediction_model(input_dataset: pd.DataFrame) -> lightgbm.LGBMClassifier:
    params = pd.read_csv('model_params.csv', index_col=False)
    params = params.to_dict('records')[0]
    df = input_dataset[["ATK_wealth", "DEF_wealth", "ATK_alive", "DEF_alive",
                        "ATK_Shields", "DEF_Shields",
                        "DEF_has_OP", "Def_has_Odin",
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


def train_model() -> lightgbm.LGBMClassifier:
    vm = ValorantLGBM("500.csv")
    vm.train_model()
    return vm.model


def test_single_round(match_id: int, round_number: int):
    rr = RoundReplay()
    rr.set_match(match_id)
    rr.choose_round(round_number)
    return rr.get_round_probability(side="atk")


if __name__ == "__main__":
    rr_instance = RoundReplay()
    rr_instance.set_match(69549)
    rr_instance.choose_round(3)
    impact = rr_instance.get_map_impact_dataframe()
    rounded_columns = ["Gain", "Lost", "Delta"]
    # Change rounded_columns to % format
    for col in rounded_columns:
        impact[col] = impact[col].round(2) * 100
        impact[col] = impact[col].astype(int)
    aux = rr_instance.get_round_probability(side="atk", add_events=True)
    print(aux)
    # rr_instance.plot_round(side="atk", marker_margin=0.15)
    # aux = rr_instance.get_round_probability(side="atk")
    # apple = 5 + 1
    # total_rounds = rr_instance.analyser.round_amount + 1
    # proba_plot = []
    # for i in range(1, total_rounds):
    #     rr_instance.choose_round(i)
    #     proba_plot.append(rr_instance.get_round_probability(side="atk"))
    # aux = rr_instance.get_round_probability(side="def")
