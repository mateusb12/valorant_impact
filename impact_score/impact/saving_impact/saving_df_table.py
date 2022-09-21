import pandas as pd


def convert_economy_to_df(input_economy: dict):
    contributions = ("DEF_LoadoutValue", "DEF_Operators", "ATK_LoadoutValue", "ATK_Operators")
    useless = ["agent", "armorId", "playerId", "agentId", "score", "weaponId", "roundId"]
    atk_guys = []
    def_guys = []
    saving_details = {"side": None, "loss_bonus": None}
    shield_dict = {None: "no shields", 1: "light shields", 2: "heavy shields"}
    for value in input_economy.values():
        value["agentName"] = value["agent"]["name"]
        value["agentRole"] = value["agent"]["role"]
        value["weaponName"] = value["weapon"]["name"]
        value["weaponPrice"] = value["weapon"]["price"]
        if value["side"] == "attacking":
            atk_guys.append(value["playerName"])
        else:
            def_guys.append(value["playerName"])
        if "currentLossBonus" in value.keys():
            saving_details["side"] = value["side"]
            saving_details["loss_bonus"] = value["currentLossBonus"]
        value["armor"] = shield_dict[value["armorId"]]
        if "savedWeapon" in value.keys():
            weapon = value["savedWeapon"]
            value["savedWeapon"] = weapon["name"]
            value["savedWeaponPrice"] = weapon["price"]
            contribution_dict = value["savingContribution"]
            for contribution in contributions:
                value[contribution] = contribution_dict[contribution] \
                    if contribution in contribution_dict.keys() else 0
        else:
            value.pop("weapon")
            value["savedWeapon"] = ""
            value["savedWeaponPrice"] = 0
            value["weaponWithoutSaving"] = ""
            value["weaponPriceWithoutSaving"] = 0
            for contribution in contributions:
                value[contribution] = 0
        for key in useless:
            value.pop(key)
    streak_dict = {"attacking": atk_guys, "defending": def_guys}
    mirror_side = {"attacking": "defending", "defending": "attacking"}
    for key in streak_dict[saving_details["side"]]:
        input_economy[key]["lastRoundLossBonus"] = int(saving_details["loss_bonus"])
    for key in streak_dict[mirror_side[saving_details["side"]]]:
        input_economy[key]["lastRoundLossBonus"] = 0
    df = pd.DataFrame.from_dict(input_economy, orient="index")
    first_columns = ["roundNumber", "playerName", "remainingCreds", "lastRoundLossBonus",
                     "savedWeapon", "savedWeaponPrice", "weaponWithoutSaving", "weaponPriceWithoutSaving",
                     "weaponName", "weaponPrice", "armor"]
    df = df[first_columns + [col for col in df.columns if col not in first_columns]]
    df.sort_values(by="side", inplace=True)
    return df