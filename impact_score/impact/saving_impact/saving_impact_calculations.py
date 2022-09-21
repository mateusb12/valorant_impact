import pandas as pd

from impact_score.impact.match_analysis import RoundReplay


class SavingImpact:
    def __init__(self, input_rr_instance: RoundReplay):
        self.rr = input_rr_instance
        self.all_features = self.rr.model.feature_name_
        self.saving_guys_side = None
        self.saving_guys = None
        self.round_number = self.rr.chosen_round
        self.player_contribution = {}
        self.team_contribution = {}

    def evaluate_saving_impact(self) -> dict:
        """ :return: dictionary of the saving impact for each player
            {'Melser': 0.012718,
            'Shyy': 0.012718}"""
        self.saving_guys = self.__search_players_who_are_saving()
        if not self.saving_guys:
            return {}
        probability_table = self.get_probabilities_without_saving()
        probabilities = probability_table["Probability"].tolist()
        impact = probabilities[1] - probabilities[0]
        loadout_key = f"{self.side}_loadoutValue"
        total_contribution = self.team_contribution[loadout_key]
        for key, value in self.player_contribution.items():
            loadout_value = value[loadout_key]
            ratio = loadout_value / total_contribution
            value["saving_impact"] = ratio * impact
        return {key: value["saving_impact"] for key, value in self.player_contribution.items()}

    def get_probabilities_without_saving(self) -> pd.DataFrame:
        """ :return: append model probabilities to dataframe without the saving contributions"""
        gamestate_table = self.get_gamestate_without_saving()
        probs = self.rr.model.predict_proba(gamestate_table)
        new_probs = [item[0] for item in probs] if self.saving_guys_side == "defending" else [item[1] for item in probs]
        gamestate_table["Probability"] = new_probs
        return gamestate_table

    def get_gamestate_without_saving(self) -> pd.DataFrame:
        """ :return: gamestate dataframe without the saving contributions"""
        next_economy = self.__get_next_economy()
        saving_team = {k: v for k, v in next_economy.items() if v["side"] == self.saving_guys_side}
        # current_round_gamestate_df = self.rr.get_round_dataframe(self.round_number)[self.all_features].copy()[:2]
        next_round_gamestate_df = self.rr.get_round_dataframe(self.round_number + 1)[self.all_features].copy()[:2]
        next_round_gamestate_df.iloc[1] = next_round_gamestate_df.iloc[0].copy()
        first_gamestate = next_round_gamestate_df.iloc[0]
        contributions = [item.get("savingContribution", None) for item in saving_team.values()]
        loadout_contribution = 0
        operator_contribution = 0
        for element in contributions:
            if isinstance(element, dict):
                for key, value in element.items():
                    if "loadoutValue" in key:
                        loadout_contribution += value
                    if "operators" in key:
                        operator_contribution += value
        self.team_contribution[f"{self.side}_loadoutValue"] = loadout_contribution
        self.team_contribution[f"{self.side}_operators"] = operator_contribution
        current_loadout_diff = int(first_gamestate["Loadout_diff"])
        saving_side = list(saving_team.values())[0]["side"]
        ld_diff_without_saving = int(current_loadout_diff - loadout_contribution) \
            if saving_side == "attacking" else int(current_loadout_diff + loadout_contribution)
        ld_diff_column = [ld_diff_without_saving, current_loadout_diff]
        next_round_gamestate_df["Loadout_diff"] = ld_diff_column
        return next_round_gamestate_df

    def __get_next_economy(self) -> dict:
        """ :return: dictionary of the next round economy with the saving contribution for each player
            {'Melser': {'savingContribution': {'ATK_loadoutValue': 650, 'ATK_operators': 0},
            'Shyy': 'savingContribution': {'ATK_loadoutValue': 650, 'ATK_operators': 0}},"""
        self.saving_guys_side = self.player_sides[self.saving_guys[0]]
        self.side = "ATK" if self.saving_guys_side == "attacking" else "DEF"
        current_economy = self.rr.tools.get_economy_dict(self.rr.chosen_round)
        next_economy = self.rr.tools.get_economy_dict(self.rr.chosen_round + 1) if \
            self.rr.chosen_round != self.rr.round_amount else None
        self.__calculate_saving_contribution_for_each_player(current_economy, next_economy, self.saving_guys)
        for key, value in next_economy.items():
            player_side = self.player_sides[key]
            value["side"] = player_side
        return next_economy

    def __calculate_saving_contribution_for_each_player(self, current_economy: dict, next_economy: dict,
                                                        saving_guys: list[str]) -> None:
        """ :param current_economy: economy dict of the current round
            :param next_economy: economy dict of the next round
            :param saving_guys: list of players who are saving in that round
            :return: None
            This function takes the gun price a given player is holding and calculates the saving contribution
             for each player who is saving in that round."""

        gun_shop = {800: "Sheriff", 950: "Stinger", 1600: "Spectre", 2050: "Bulldog", 2250: "Guardian",
                    2900: ("Phantom", "Vandal")}
        for key, value in current_economy.items():
            if key in saving_guys:
                gun_contribution_value = int(value["weapon"]["price"])
                operator_contribution = 1 if value["weapon"] == "operator" else 0
                side_contribution = "ATK" if self.saving_guys_side == "attacking" else "DEF"
                next_economy[key]["savedWeapon"] = value["weapon"]
                loss_bonus_table = self.rr.tools.get_round_loss_bonus_by_players(self.rr.chosen_round)
                current_loss_bonus = loss_bonus_table[key]
                next_economy[key]["currentLossBonus"] = current_loss_bonus
                current_creds = value["remainingCreds"]
                next_creds_without_saving = current_creds + current_loss_bonus
                most_expensive_available_weapon_price = max(k for k in gun_shop if k <= next_creds_without_saving)
                most_expensive_available_weapon_name = gun_shop[most_expensive_available_weapon_price]
                next_economy[key]["weaponPriceWithoutSaving"] = most_expensive_available_weapon_price
                next_economy[key]["weaponWithoutSaving"] = most_expensive_available_weapon_name
                loadout_diff = gun_contribution_value - most_expensive_available_weapon_price
                contribution = {f"{side_contribution}_loadoutValue": loadout_diff,
                                f"{side_contribution}_operators": operator_contribution,
                                "side": side_contribution,
                                "name": key}
                self.player_contribution[key] = contribution
                next_economy[key]["savingContribution"] = contribution

    def __search_players_who_are_saving(self) -> list[str]:
        """ :return: list of players who are saving in that round"""
        """ ['Melser', 'Adverso']"""
        player_details = self.rr.exporter.export_player_details()
        dead_player_ids = [x["referencePlayerId"] for x in self.rr.current_round_events
                           if x["eventType"] == "kill" and x["eventType"] != "revival"]
        alive_players = [value["player_name"] for key, value in player_details.items()
                         if key not in dead_player_ids]
        self.player_sides = self.rr.tools.get_player_name_sides(self.rr.chosen_round)
        round_outcome = [item for item in self.rr.round_outcomes if item["number"] == self.rr.chosen_round][0]
        win_condition = round_outcome["winCondition"]
        return [player for player in alive_players
                if win_condition in ("defuse", "time")
                and self.player_sides[player] == "attacking"
                or win_condition not in ("defuse", "time")
                and win_condition == "bomb" and self.player_sides[player] == "defending"]

    def evaluate_single_round_saving_impact(self, input_round: int) -> dict:
        """ :param input_round: round number
            :return: None
            This function evaluates the saving impact of a given round"""
        self.rr.choose_round(input_round)
        self.rr.get_round_probability(round_number=input_round, side="atk")
        self.__init__(self.rr)
        return self.evaluate_saving_impact()

    def __evaluate_all_rounds_saving_impact(self) -> dict:
        return {i: self.evaluate_single_round_saving_impact(i) for i in range(1, self.rr.round_amount + 1)}

    def saving_impact_rounds_df(self) -> pd.DataFrame:
        saving_impact_dicts = self.__evaluate_all_rounds_saving_impact()
        saving_impact_df = pd.DataFrame.from_dict(saving_impact_dicts, orient="index")
        saving_impact_df.reset_index(level=0, inplace=True)
        saving_impact_df.rename(columns={"index": "RoundNumber"}, inplace=True)
        return saving_impact_df

    def saving_impact_aggregation(self) -> pd.DataFrame:
        saving_impact_df = self.saving_impact_rounds_df()
        player_columns = [col for col in saving_impact_df.columns if col not in ["RoundNumber"]]
        sum_values = saving_impact_df[player_columns].sum()
        count_values = saving_impact_df[player_columns].count()
        round_amount = saving_impact_df["RoundNumber"].count()
        saving_amount = {player: 0 for player in player_columns}
        impact_values = list(sum_values.values)
        impact_value_percentage = [f"{round(x * 100, 2)}%" for x in impact_values]
        impact_df = pd.DataFrame({"Player": list(sum_values.index), "SavingImpact": list(sum_values.values),
                                  "Saved Rounds": list(count_values.values),
                                  "Total Saving Impact (%)": impact_value_percentage})
        impact_df.sort_values(by="SavingImpact", ascending=False, inplace=True)
        return impact_df


def __main():
    rr = RoundReplay()
    rr.set_match(78746)
    si = SavingImpact(rr)
    aux = si.saving_impact_aggregation()
    # aux = si.evaluate_single_round_saving_impact(10)
    # aux = si.evaluate_single_round_saving_impact(16)
    # rr.choose_round(16)
    # rr.get_round_probability(round_number=16, side="atk")
    # si = SavingImpact(rr)
    # aux = si.evaluate_saving_impact()
    print(aux)


if __name__ == "__main__":
    __main()
