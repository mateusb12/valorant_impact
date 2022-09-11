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
        self.analyser, self.exporter, self.wrapper, self.tools, self.round_outcomes = [None] * 5
        self.current_round_events, self.player_sides, self.previous_round_saving_guys = [None] * 3

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
        self.side_dict = self.tools.generate_side_outcomes_dict()
        self.round_outcomes = self.analyser.map_dict["rounds"]

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

    @staticmethod
    def __loc_index(input_df: pd.DataFrame, index: int):
        loc_index_list = [False] * len(input_df)
        loc_index_list[index] = True
        return input_df.loc[loc_index_list]

    @staticmethod
    def __insert_row(new_row: pd.DataFrame, original_df: pd.DataFrame, position: int):
        first_slice = original_df.iloc[:position]
        second_slice = original_df.iloc[position:]
        return pd.concat([first_slice, new_row, second_slice]).reset_index(drop=True)

    def __handle_special_situation(self, input_table: pd.DataFrame, **kwargs):
        """ Set hardcoded probabilities for end of the round situations """
        situation_type = kwargs["situation"]
        events = kwargs["events"]
        first_index = int(input_table.index[0])
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
            first_element = query_indexes[beginning_position] if situation_type != "after_explosion" \
                else query_indexes[beginning_position] - 1
            input_table.loc[first_element:last_element, 'Probability_before_event'] = new_proba
            input_table.loc[first_element:last_element, 'Probability_after_event'] = new_proba

            if situation_type == "after_defuse":
                defuse_index = events.index("defuse")
                input_table.loc[query_indexes[0], 'Probability_after_event'] = new_proba

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
        side = kwargs["side"]
        self.side = side
        displaced_dict = self.__get_displaced_preds(table)
        displaced_pred = displaced_dict["displaced"]
        default_pred = displaced_dict["default"]
        table["Probability_before_event"] = displaced_pred
        table["Probability_after_event"] = default_pred
        if side == "def":
            table['Probability_before_event'] = 1 - table['Probability_before_event']
            table['Probability_after_event'] = 1 - table['Probability_after_event']
        table["Round"] = round_number
        self.current_round_events = self.events_data[self.chosen_round]
        self.__analyse_special_situation(table)

        table["Impact"] = abs(table["Probability_after_event"] - table["Probability_before_event"])
        table = table[["Round", "EventID", "EventType", "Probability_before_event", "Probability_after_event",
                       "Impact"]]

        if "add_events" in kwargs and kwargs["add_events"]:
            self.__append_round_events_to_probability_dataframe(table)

        saving_guys = self.__search_players_who_are_saving()
        saving_guys_side = self.player_sides[saving_guys[0]]
        economy_pool = [self.tools.get_economy_dict(self.chosen_round),
                        self.tools.get_economy_dict(self.chosen_round + 1)
                        if self.chosen_round != self.round_amount else None]
        details = self.exporter.export_player_details()
        sides = self.player_sides
        current_economy = economy_pool[0]
        next_economy = economy_pool[1]
        gun_shop = {800: "Sheriff", 950: "Stinger", 1600: "Spectre", 2050: "Bulldog", 2250: "Guardian",
                    2900: ("Phantom", "Vandal")}
        saved_guns = []
        for key, value in current_economy.items():
            if key in saving_guys:
                gun_contribution_value = int(value["weapon"]["price"])
                saved_guns.append(value["weapon"])
                operator_contribution = 1 if value["weapon"] == "operator" else 0
                side_contribution = "ATK" if saving_guys_side == "attacking" else "DEF"
                next_economy[key]["savedWeapon"] = value["weapon"]
                loss_bonus_table = self.tools.get_round_loss_bonus_by_players(self.chosen_round)
                current_loss_bonus = loss_bonus_table[key]
                current_creds = value["remainingCreds"]
                next_creds_with_saving = next_economy[key]["remainingCreds"]
                next_creds_without_saving = current_creds + current_loss_bonus
                most_expensive_available_weapon = max(k for k in gun_shop if k <= next_creds_without_saving)
                loadout_diff = gun_contribution_value - most_expensive_available_weapon
                contribution = {f"{side_contribution}_loadoutValue": loadout_diff,
                                f"{side_contribution}_operators": operator_contribution,
                                "side": side_contribution}
                next_economy[key]["savingContribution"] = contribution
                print("Oi")
        self.previous_round_saving_guys = next_economy
        for key, value in next_economy.items():
            player_side = self.player_sides[key]
            value["side"] = player_side
        saving_team = {k: v for k, v in next_economy.items() if v["side"] == saving_guys_side}
        credits_per_player = [v["remainingCreds"] for k, v in saving_team.items()]
        saved_guns_pool = saved_guns.copy()
        affordable_saved_guns_per_player = [item//int(saved_guns_pool[0]["price"]) for item in credits_per_player]

        next_table = self.__get_round_dataframe(round_number + 1)[all_features].copy()[:2]
        next_table.iloc[1] = next_table.iloc[0].copy()
        beginning = next_table.iloc[0]
        probs = self.model.predict_proba(next_table)

        table = table.fillna(0)
        return table

    def __search_players_who_are_saving(self) -> list[str]:
        dead_player_ids = [x["referencePlayerId"] for x in self.current_round_events
                           if x["eventType"] == "kill" and x["eventType"] != "revival"]
        player_details = self.exporter.export_player_details()
        alive_players = [value["player_name"] for key, value in player_details.items()
                         if key not in dead_player_ids]
        self.player_sides = self.tools.get_player_name_sides(self.chosen_round)
        round_outcome = [item for item in self.round_outcomes if item["number"] == self.chosen_round][0]
        win_condition = round_outcome["winCondition"]
        return [player for player in alive_players
                if win_condition in ("defuse", "time")
                and self.player_sides[player] == "attacking"
                or win_condition not in ("defuse", "time")
                and win_condition == "bomb" and self.player_sides[player] == "defending"]

    def __analyse_special_situation(self, table: pd.DataFrame):
        """ This method is used to analyse which special situation the current round belongs
        (like defuse, clean kills, clean defuses, etc.) and then handle that situation accordingly. """
        round_millis = [x["roundTimeMillis"] for x in self.current_round_events]
        max_millis = max(round_millis)
        event_ids = self.generate_events_ids(self.current_round_events)
        table["EventID"] = event_ids
        event_types = [x["eventType"] for x in self.current_round_events]
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
        table["EventType"] = event_types
        self.__handle_special_situation(table, situation=situation_type, events=event_types)

    @staticmethod
    def generate_events_ids(current_round_events: list[dict]) -> list[int]:
        """ Generate a list of event ids for each event in the round """
        event_ids = []
        for x in current_round_events:
            raw_ids = [x["killId"], x["bombId"], x["resId"]]
            query_id = [x for x in raw_ids if x is not None]
            if len(query_id) != 1:
                event_ids.append(0)
                Exception("Error in query")
            else:
                event_ids.append(query_id[0])
        return event_ids

    def __append_round_events_to_probability_dataframe(self, table: pd.DataFrame):
        event_df = pd.DataFrame(self.current_round_events)
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


def inverse_prob(x: str) -> str:
    numerical = float(x[:-1]) / 100
    inverse = (1 - numerical) * 100
    return f"{inverse:.2f}%"


def __main():
    rr = RoundReplay()
    rr.set_match(78746)
    rr.choose_round(16)
    prob = rr.get_round_probability(side="def", add_events=True)
    # rr.get_overall_saving_impact()
    print(rr)

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


if __name__ == "__main__":
    __main()
