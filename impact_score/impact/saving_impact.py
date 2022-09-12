from impact_score.impact.match_analysis import RoundReplay


class SavingImpact:
    def __init__(self, input_rr_instance: RoundReplay):
        self.rr = input_rr_instance
        self.all_features = self.rr.model.feature_name_
        self.saving_guys_side = None
        self.round_number = self.rr.chosen_round

    def evaluate_saving_impact(self):
        next_economy = self.__get_next_economy()
        for key, value in next_economy.items():
            player_side = self.player_sides[key]
            value["side"] = player_side
        saving_team = {k: v for k, v in next_economy.items() if v["side"] == self.saving_guys_side}
        next_table = self.rr.get_round_dataframe(self.round_number + 1)[self.all_features].copy()[:2]
        next_table.iloc[1] = next_table.iloc[0].copy()
        beginning = next_table.iloc[0]
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
        current_loadout_diff = beginning["Loadout_diff"]
        saving_side = list(saving_team.values())[0]["side"]
        ld_diff_without_saving = current_loadout_diff - loadout_contribution \
            if saving_side == "attacking" else +loadout_contribution
        next_table.iloc[1]["Loadout_diff"] = ld_diff_without_saving
        probs = self.rr.model.predict_proba(next_table)

    def __get_next_economy(self) -> dict:
        """ :return: dictionary of the next round economy with the saving contribution for each player
            {'Melser': {'savingContribution': {'ATK_loadoutValue': 650, 'ATK_operators': 0},
            'Shyy': 'savingContribution': {'ATK_loadoutValue': 650, 'ATK_operators': 0}},"""
        saving_guys = self.__search_players_who_are_saving()
        self.saving_guys_side = self.player_sides[saving_guys[0]]
        current_economy = self.rr.tools.get_economy_dict(self.rr.chosen_round)
        next_economy = self.rr.tools.get_economy_dict(self.rr.chosen_round + 1) if \
            self.rr.chosen_round != self.rr.round_amount else None
        gun_shop = {800: "Sheriff", 950: "Stinger", 1600: "Spectre", 2050: "Bulldog", 2250: "Guardian",
                    2900: ("Phantom", "Vandal")}
        self.__calculate_saving_contribution(current_economy, next_economy, gun_shop, saving_guys)
        return next_economy

    def __calculate_saving_contribution(self, current_economy: dict, next_economy: dict, gun_shop: dict,
                                        saving_guys: list[str]):
        """ :param current_economy: economy of the current round
            :param next_economy: economy of the next round
            :param gun_shop: dictionary of the gun shop and their prices
            :param saving_guys: list of players who are saving in that round
            :return: None

            This function calculates the saving contribution for each gun of each player who is saving in that round."""
        for key, value in current_economy.items():
            if key in saving_guys:
                gun_contribution_value = int(value["weapon"]["price"])
                operator_contribution = 1 if value["weapon"] == "operator" else 0
                side_contribution = "ATK" if self.saving_guys_side == "attacking" else "DEF"
                next_economy[key]["savedWeapon"] = value["weapon"]
                loss_bonus_table = self.rr.tools.get_round_loss_bonus_by_players(self.rr.chosen_round)
                current_loss_bonus = loss_bonus_table[key]
                current_creds = value["remainingCreds"]
                next_creds_without_saving = current_creds + current_loss_bonus
                most_expensive_available_weapon = max(k for k in gun_shop if k <= next_creds_without_saving)
                loadout_diff = gun_contribution_value - most_expensive_available_weapon
                contribution = {f"{side_contribution}_loadoutValue": loadout_diff,
                                f"{side_contribution}_operators": operator_contribution,
                                "side": side_contribution}
                next_economy[key]["savingContribution"] = contribution

    def __search_players_who_are_saving(self) -> list[str]:
        """ :return: list of players who are saving in that round"""
        """ ['Melser', 'Adverso']"""
        dead_player_ids = [x["referencePlayerId"] for x in self.rr.current_round_events
                           if x["eventType"] == "kill" and x["eventType"] != "revival"]
        player_details = self.rr.exporter.export_player_details()
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


def __main():
    rr = RoundReplay()
    rr.set_match(78746)
    rr.choose_round(16)
    rr.get_round_probability(round_number=16, side="atk")
    si = SavingImpact(rr)
    si.evaluate_saving_impact()
    print(si.all_features)


if __name__ == "__main__":
    __main()