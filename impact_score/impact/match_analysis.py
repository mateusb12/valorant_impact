import copy

import pandas as pd
# from line_profiler_pycharm import profile

import lightgbm
from termcolor import colored

from impact_score.imports.os_slash import get_slash_type
from impact_score.json_analyser.wrap.analyser_exporter import AnalyserExporter
from impact_score.json_analyser.wrap.analyser_loader import get_analyser
from impact_score.json_analyser.pool.analyser_pool import CoreAnalyser
from impact_score.json_analyser.core.analyser_tools import AnalyserTools
from impact_score.json_analyser.wrap.analyser_wrapper import AnalyserWrapper
from impact_score.model.lgbm_loader import load_lgbm
from impact_score.model.lgbm_model import ValorantLGBM, get_trained_model_from_pkl


class PlayerNotFoundException(Exception):
    pass


class RoundReplay:
    def __init__(self):
        self.match_id = 0

        # self.vm: ValorantLGBM = load_lgbm()
        self.vm: ValorantLGBM = get_trained_model_from_pkl()
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
        self.exporter.a.choose_round(1)
        self.player_impact = self.exporter.export_player_names()
        self.round_amount = self.analyser.get_last_round()
        self.df = self.wrapper.export_df()
        self.query = self.df.query(f"MatchID == {match_id}")
        self.round_table = self.tools.get_round_table()
        self.chosen_round = None
        event_list = self.analyser.data["matches"]["matchDetails"]["events"]
        aux_dict = {i: [] for i in range(1, self.round_amount + 1)}
        for item in self.analyser.data["matches"]["matchDetails"]["events"]:
            aux_dict[item["roundNumber"]].append(item)
        self.events_data = aux_dict
        # self.side_dict = dict(zip(self.df.RoundNumber, self.df.FinalWinner))
        self.side_dict = self.tools.generate_side_dict()

    def choose_round(self, round_number: int):
        self.chosen_round = round_number
        print(colored(f"Round {round_number} selected", "yellow"))

    def __is_player_in_this_match(self, player_name: str) -> bool:
        return player_name in self.player_impact

    def __get_round_table(self) -> dict:
        g = self.query[["RoundNumber", "RoundID"]]
        g.drop_duplicates()
        return dict(zip(g.RoundNumber, g.RoundID))

    def __get_round_id(self, round_index: int) -> int:
        return self.round_table[round_index]

    def __get_round_dataframe(self, round_index: int):
        return self.df.query(f'RoundID == {self.__get_round_id(round_index)}')

    def get_round_winners(self) -> dict:
        g = self.query[["RoundNumber", "FinalWinner"]]
        g.drop_duplicates()
        return dict(zip(g.RoundNumber, g.FinalWinner))

    @staticmethod
    def __displace_column(input_df: pd.DataFrame, column_name: str):
        column = list(input_df[column_name])
        last = column[-1]
        displaced = column[1:]
        displaced.append(last)
        input_df[column_name] = displaced

    def __get_displaced_preds(self, input_table: pd.DataFrame) -> dict:
        displaced_table = input_table.copy()
        self.__displace_column(displaced_table, "RegularTime")
        self.__displace_column(displaced_table, "SpikeTime")
        first_row = pd.DataFrame(input_table.iloc[0]).transpose()
        displaced_table = pd.concat([first_row, displaced_table]).reset_index(drop=True)
        displaced_table = displaced_table[:-1]
        raw_default_pred = self.model.predict_proba(input_table)
        default_pred = raw_default_pred[:, 1]
        raw_displaced_pred = self.model.predict_proba(displaced_table)
        displaced_pred = raw_displaced_pred[:, 1]
        return {"default": default_pred, "displaced": displaced_pred}

    def __handle_special_situation(self, input_table: pd.DataFrame, **kwargs):
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
                beginning_position = 1 if len(query_indexes) > 2 else 0
                new_proba = 1 if self.side == "atk" else 0
            last_element = query_indexes[-1]
            first_element = query_indexes[beginning_position]
            input_table.loc[first_element:last_element, 'Probability_before_event'] = new_proba
            input_table.loc[first_element:last_element, 'Probability_after_event'] = new_proba

            if situation_type == "after_defuse":
                defuse_index = events.index("defuse")
                input_table.loc[query_indexes[0], 'Probability_after_event'] = new_proba

    def get_clutchy_rounds(self, chosen_side: str) -> dict:
        dtb = self.tools.generate_round_info()
        winner_dict = {0: "def", 1: "atk"}
        round_amount = max(dtb.keys())
        minimum_probabilities_dict = {}
        original_round = self.chosen_round
        for i in range(1, round_amount + 1):
            self.chosen_round = i
            prob = self.get_round_probability(side=chosen_side, add_events=True)
            winner = winner_dict[dtb[i]["finalWinner"]]
            if winner == chosen_side:
                round_id = dtb[i]["number"]
                min_prob = min(list(prob["Probability_before_event"]))
                minimum_probabilities_dict[round_id] = round(100 * min_prob, 2)

        self.chosen_round = original_round
        sorted_d = dict(
            sorted(minimum_probabilities_dict.items(), key=lambda item: item[1])
        )
        return {key: f"{value}%" for key, value in sorted_d.items()}

    def get_biggest_throws(self, team_name: str) -> dict:
        original_round = self.chosen_round
        team_sides = self.tools.get_side_dict()
        dtb = self.tools.generate_round_info()
        round_amount = max(dtb.keys())
        maximum_probabilities_dict = {}
        for i in range(1, round_amount + 1):
            self.chosen_round = i
            side_info = team_sides[i][team_name]
            current_side = side_info["side"]
            formatted_side = {"defense": "def", "attack": "atk"}
            prob = self.get_round_probability(side=formatted_side[current_side], add_events=True)
            if side_info["outcome"] == "loss":
                round_id = dtb[i]["number"]
                max_prob = max(list(prob["Probability_before_event"]))
                maximum_probabilities_dict[round_id] = round(100 * max_prob, 2)
        self.chosen_round = original_round
        sorted_dict = dict(sorted(maximum_probabilities_dict.items(), key=lambda item: item[1], reverse=True))
        return {key: f"{value}%" for key, value in sorted_dict.items()}

    def get_biggest_clutches(self, team_name: str) -> dict:
        biggest_throws = self.get_biggest_throws(team_name)
        without_percentage = {key: float(value[:-1]) for key, value in biggest_throws.items()}
        inverse_prob_dict = {key: round(100 - value, 2) for key, value in without_percentage.items()}
        sorted_dict = dict(sorted(inverse_prob_dict.items(), key=lambda item: item[1], reverse=False))
        return {key: f"{value}%" for key, value in sorted_dict.items()}

    # @profile
    def get_round_probability(self, **kwargs):
        """
        :param kwargs: round_number: int
                       side: str, "atk" or "def"
                       add_events: boolean
        :return: pd.DataFrame table with the probabilities of each round
        """
        round_number = self.chosen_round
        old_table = self.__get_round_dataframe(round_number)
        all_features = self.model.feature_name_
        table = old_table[all_features].copy()
        displaced_dict = self.__get_displaced_preds(table)
        displaced_pred = displaced_dict["displaced"]
        default_pred = displaced_dict["default"]
        table["Probability_before_event"] = displaced_pred
        table["Probability_after_event"] = default_pred
        side = kwargs["side"]
        self.side = side
        if side == "def":
            table['Probability_before_event'] = 1 - table['Probability_before_event']
            table['Probability_after_event'] = 1 - table['Probability_after_event']
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

        self.__handle_special_situation(table, situation=situation_type, events=event_types)

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
            killers = event_df["playerId"].tolist()
            killer_names = [player_names[x] for x in killers]
            # table["Killer"] = event_df["playerId"].map(player_names).values
            table["Killer"] = [player_names[x] for x in killers]
            table["KillerAgent"] = event_df["playerId"].map(player_agents).values
            table["Weapon"] = event_df["weaponId"].map(weapon_name_data).values
            table["Ability"] = event_df["ability"].values
            table["Victim"] = event_df["referencePlayerId"].map(player_names).values
            table["VictimAgent"] = event_df["referencePlayerId"].map(player_agents).values

        table = table.fillna(0)
        return table

    def __get_round_impact(self) -> dict:
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
        for key, value in player_impact_table.items():
            value["delta"] = value["gained"] - value["lost"]
        return player_impact_table

    def get_player_most_impactful_rounds(self, input_player_name: str) -> pd.DataFrame:
        if not self.__is_player_in_this_match(input_player_name):
            raise PlayerNotFoundException(f"Player {input_player_name} not in this match")
        pot = []
        columns = ["Name", "Round", "Gained", "Lost", "Delta"]
        player_name = input_player_name.lower()
        for i in range(1, self.round_amount + 1):
            self.choose_round(i)
            impact_dict = self.__get_round_impact()
            impact_dict_lower = {k.lower(): v for k, v in impact_dict.items()}
            player_impact = impact_dict_lower[player_name]
            pot.append((player_name, i, player_impact["gained"], player_impact["lost"], player_impact["delta"]))
        res = pd.DataFrame(pot, columns=columns)
        res = res.sort_values("Gained", ascending=False)
        return res

    def __get_map_impact(self) -> dict:
        pi = copy.deepcopy(self.player_impact)
        impact_list = []
        for i in range(1, self.round_amount + 1):
            self.choose_round(i)
            round_impact = self.__get_round_impact()
            impact_list.append(round_impact)

        for round_impact in impact_list:
            for key, value in round_impact.items():
                pi[key]["gained"] += value["gained"]
                pi[key]["lost"] += value["lost"]
                pi[key]["delta"] += value["delta"]

        return dict(sorted(pi.items(), key=lambda item: item[1]["delta"], reverse=True))

    def get_map_impact_dataframe(self) -> pd.DataFrame:
        igns = []
        gains = []
        losses = []
        deltas = []
        map_impact = self.__get_map_impact()
        for key, value in map_impact.items():
            igns.append(key)
            gains.append(value["gained"])
            losses.append(value["lost"])
            deltas.append(value["delta"])
        match_id = [self.match_id] * len(igns)

        impact_table = {"Name": igns, "Gain": gains, "Lost": losses, "Delta": deltas, "MatchID": match_id}
        aux_impact = pd.DataFrame(impact_table)
        agent_dict = self.exporter.export_player_agent_picks()
        aux_impact["Agent"] = aux_impact["Name"].map(agent_dict)
        return aux_impact


def test_single_round(match_id: int, round_number: int):
    rr = RoundReplay()
    rr.set_match(match_id)
    rr.choose_round(round_number)
    return rr.get_round_probability(side="atk")


def inverse_prob(x: str) -> str:
    numerical = float(x[:-1]) / 100
    inverse = (1 - numerical) * 100
    return f"{inverse:.2f}%"


if __name__ == "__main__":
    rr_instance = RoundReplay()
    rr_instance.set_match(78745)
    rr_instance.choose_round(21)
    q = rr_instance.get_clutchy_rounds("atk")
    # q = rr_instance.get_biggest_clutches("Team Liquid")
    print(q)

    # Convert '8.04%' to 0.0804 and store it on lambda
    # inverse_q = {key: inverse_prob(value) for key, value in q.items()}
    # print(inverse_q)
    # impact = rr_instance.get_map_impact_dataframe()
    # rounded_columns = ["Gain", "Lost", "Delta"]
    # # Change rounded_columns to % format
    # for col in rounded_columns:
    #     impact[col] = impact[col].round(2) * 100
    #     impact[col] = impact[col].astype(int)
    # aux = rr_instance.get_round_probability(side="atk", add_events=True)
    # print(aux)
    # rr_instance.plot_round(side="atk", marker_margin=0.15)
    # aux = rr_instance.get_round_probability(side="atk")
    # apple = 5 + 1
    # total_rounds = rr_instance.analyser.round_amount + 1
    # proba_plot = []
    # for i in range(1, total_rounds):
    #     rr_instance.choose_round(i)
    #     proba_plot.append(rr_instance.get_round_probability(side="atk"))
    # aux = rr_instance.get_round_probability(side="def")
