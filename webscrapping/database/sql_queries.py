import json
from typing import Tuple, List
from itertools import combinations
from math import sqrt

import pandas as pd

from webscrapping.database.sql_creator import ValorantCreator


class ValorantQueries:
    def __init__(self):
        self.db = ValorantCreator("valorant")
        self.match_id = 0

        weapon_file = open('..\\matches\\model\\weapon_table.json')
        self.weapon_data = json.load(weapon_file)

        agent_file = open('..\\matches\\model\\agent_table.json')
        self.agent_data = json.load(agent_file)

        maps_file = open('..\\matches\\model\\map_table.json')
        self.maps_data = json.load(maps_file)

        agent_roles_file = open('..\\matches\\model\\agent_roles.json')
        self.agent_roles = json.load(agent_roles_file)

    def set_match(self, input_match_id: int):
        self.match_id = input_match_id

    def get_all_rounds(self):
        instruction = f"""
        SELECT Rounds.round_number, Rounds.attacking_team, Rounds.winning_team
        FROM Rounds
        where Rounds.match_id = {self.match_id};
        """
        self.db.cursor.execute(instruction)
        return self.db.cursor.fetchall()

    def query_all_rounds(self):
        query = f"""
                SELECT 'Round' as ta, Rounds.*, 'Match' as tb, Matches.*
                FROM Rounds
                JOIN Matches ON matches.match_id = rounds.match_id
                where Matches.match_id = {self.match_id};
            """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    def get_economies(self):
        query = f"""
            SELECT 'RoundEconomies' as ta, RoundEconomies.*, 'Rounds' as td, Rounds.*, 'Matches' as te, Matches.*
            FROM RoundEconomies
            INNER JOIN Rounds ON RoundEconomies.round_id = Rounds.round_id
            INNER JOIN Matches ON Rounds.match_id = Matches.match_id
            WHERE Matches.match_id = {self.match_id}
        """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    def get_current_match(self):
        query = f"""
        SELECT * FROM Matches WHERE match_id = {self.match_id}
        """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    def get_current_map_name(self):
        return self.get_current_match()[0][4]

    def get_loadouts(self):
        query = f"""
            SELECT Rounds.match_id, RoundEconomies.round_id, RoundEconomies.Round_number, RoundEconomies.Player_id,
            PlayerMapInstance.team_id, RoundEconomies.remaining_creds, RoundEconomies.loadout_value
            FROM RoundEconomies
            INNER JOIN Rounds ON RoundEconomies.round_id = Rounds.round_id
            INNER JOIN PlayerMapInstance ON PlayerMapInstance.player_id = RoundEconomies.player_id
            where Match_id = {self.match_id} 
            AND PlayerMapInstance.map_played = {self.match_id}
        """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    def get_full_loadouts(self):
        query = f"""
        SELECT Rounds.match_id, RoundEconomies.round_id, RoundEconomies.Round_number, RoundEconomies.Player_id,
        PlayerMapInstance.team_id, RoundEconomies.remaining_creds, RoundEconomies.loadout_value, RoundEconomies.agent_id,
        weapon_id, armor_id
        FROM RoundEconomies
        INNER JOIN Rounds ON RoundEconomies.round_id = Rounds.round_id
        INNER JOIN PlayerMapInstance ON PlayerMapInstance.player_id = RoundEconomies.player_id
        where Match_id = {self.match_id}
        AND PlayerMapInstance.map_played = {self.match_id}
        """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    def get_events(self):
        query = f"""
            SELECT 'RoundEvents' as ta, RoundEvents.*, 'Rounds' as td, Rounds.*, 'Matches' as te, Matches.*
            FROM RoundEvents
            INNER JOIN Rounds ON RoundEvents.round_id = Rounds.round_id
            INNER JOIN Matches ON Rounds.match_id = Matches.match_id
            WHERE Matches.match_id = {self.match_id}
        """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    def get_event_table(self) -> pd.DataFrame:
        query = f"""
            SELECT RoundEvents.round_number, round_time_millis, player_id, victim_id, event_type, damage_type, weapon_id, ability
            FROM RoundEvents
            INNER JOIN Rounds ON RoundEvents.round_id = Rounds.round_id
            INNER JOIN Matches ON Rounds.match_id = Matches.match_id
            WHERE Matches.match_id = {self.match_id}
        """
        self.db.cursor.execute(query)
        return pd.DataFrame(self.db.cursor.fetchall(), columns=['Round', 'Round_time_millis', 'PlayerID',
                                                                'VictimID', 'EventType', 'DamageType', 'WeaponID',
                                                                'Ability'])

    def get_round_locations(self):
        query = f"""
                SELECT RoundLocations.Round_number, round_time_millis, player_id, location_x, location_y, view_radians
                FROM RoundLocations
                INNER JOIN Rounds ON RoundLocations.round_id = Rounds.round_id
                INNER JOIN Matches ON Rounds.match_id = Matches.match_id
                WHERE Matches.match_id = {self.match_id}
                """
        self.db.cursor.execute(query)
        return pd.DataFrame(self.db.cursor.fetchall(), columns=['Round', 'Round_time_millis', 'PlayerID',
                                                                'LocationX', 'LocationY', 'ViewRadians'])

    def get_player_names(self) -> dict:
        query = f"""
            SELECT PlayerMapInstance.Player_id, Player_name, map_played
            FROM Players
            JOIN PlayerMapInstance
            ON Players.player_id = PlayerMapInstance.player_id
            WHERE map_played = {self.match_id}
        """
        self.db.cursor.execute(query)
        player_name_df = pd.DataFrame(self.db.cursor.fetchall(), columns=['Player_id', 'Player_name', 'Map_played'])
        return dict(zip(player_name_df['Player_id'], player_name_df['Player_name']))

    def get_locations(self):
        query = f"""
            SELECT 'RoundLocations' as ta, RoundLocations.*, 'Rounds' as td, Rounds.*, 'Matches' as te, Matches.*
            FROM RoundLocations
            INNER JOIN Rounds ON RoundLocations.round_id = Rounds.round_id
            INNER JOIN Matches ON Rounds.match_id = Matches.match_id
            WHERE Matches.match_id = {self.match_id}
        """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    def get_instances(self):
        query = f"""
            SELECT 'PlayerMapInstance' as ta, PlayerMapInstance.*
            FROM PlayerMapInstance
            WHERE map_played = {self.match_id}
        """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    def get_player_instances(self):
        query = f"""
        SELECT PlayerMapInstance.player_id, player_name, agent_id, first_side, map_played, PlayerMapInstance.team_id
        FROM PlayerMapInstance
        INNER JOIN Players
        ON PlayerMapinstance.player_id = Players.player_id
        WHERE Map_played = {self.match_id}
        ORDER BY first_side
        """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    @staticmethod
    def get_average_distance_between_multiple_points(point_list: List):
        distance_list = []
        for combo in combinations(point_list, 2):
            distance = sqrt((combo[0][0] - combo[1][0]) ** 2 + (combo[0][1] - combo[1][1]) ** 2)
            distance_list.append(distance)
        return sum(distance_list) / len(distance_list)

    def get_compaction_from_timestamp(self, timestamp: int, current_round_locations_df: pd.DataFrame,
                                      attacking_player_ids: List[int]) -> dict:
        """
        Get attack and defense compactions on a given timestamp
        :param timestamp: in milliseconds
        :param current_round_locations_df: dataframe of locations for the current round
        :param attacking_player_ids: list containing the player ids of the attacking players
        :return: dict with float values for attack and defense compaction
        """
        current_timestamp_locations = current_round_locations_df[
            current_round_locations_df['Round_time_millis'] == timestamp]
        atk_locations = []
        def_locations = []
        for row in current_timestamp_locations.itertuples():
            aux = (row.LocationX, row.LocationY)
            if row.PlayerID in attacking_player_ids:
                atk_locations.append(aux)
            else:
                def_locations.append(aux)

        atk_compact = (
            self.get_average_distance_between_multiple_points(atk_locations)
            if len(atk_locations) > 1
            else 0
        )
        def_compact = (
            self.get_average_distance_between_multiple_points(def_locations)
            if len(def_locations) > 1
            else 0
        )
        return {"atk_compaction": atk_compact,
                "def_compaction": def_compact}

    def get_compaction_from_round(self, current_round: int) -> pd.DataFrame:
        """
        Get attack and defense compactions for each timestamp in a given round
        :param current_round: int
        :return: Columns → Round_time_millis, atk_compaction, def_compaction
        """
        locations = self.get_round_locations()
        current_round_locations = locations[locations['Round'] == current_round]
        round_dict = self.get_current_round_basic_info(5)
        attacking_players = round_dict["attacking_players"]
        time_millis_unique = tuple(current_round_locations["Round_time_millis"].unique())
        time_millis_list = []
        for time_millis in time_millis_unique:
            aux = self.get_compaction_from_timestamp(time_millis, current_round_locations, attacking_players)
            new_row = (time_millis, aux["atk_compaction"], aux["def_compaction"])
            time_millis_list.append(new_row)

        time_millis_list.insert(0, (0, 0, 0))
        time_millis_columns = ("Round_time_millis", "atk_spread", "def_spread")
        return pd.DataFrame(time_millis_list, columns=time_millis_columns)

    def get_team_compositions(self) -> pd.DataFrame:
        """
        Returns a list of all player compositions for that map
        :return: PlayerID, Player Name, Agent Name, First Side, Map ID, Agent ID, Team ID
        """
        raw_instances = self.get_player_instances()
        raw_instance_df = pd.DataFrame(raw_instances, columns=['PlayerID', 'PlayerName', 'AgentID', 'FirstSide',
                                                               'MapID', 'TeamID'])
        agent_dict = {int(key): value["name"] for key, value in vq.agent_data.items()}
        raw_instance_df['AgentName'] = raw_instance_df['AgentID'].map(agent_dict)
        raw_instance_df = raw_instance_df[["PlayerID", "PlayerName", "AgentName", "FirstSide", "MapID",
                                           "AgentID", "TeamID"]]
        return raw_instance_df

    @staticmethod
    def reposition_column(input_dataframe: pd.DataFrame, column_name: str, new_position: int):
        old_column = input_dataframe.pop(column_name)
        input_dataframe.insert(new_position, old_column.name, old_column)

    def get_initial_state(self):
        """
        Returns a list of all players states for a given match
        :return: Round, Player ID, Team ID, Remaining Creds, Loadout Value, Agent ID, Weapon ID, Armor ID,
        Shield, Shield Price, Weapon Name, Weapon Price, Utility Value
        """
        loadouts = self.get_full_loadouts()
        shield_table = {0: 0, 1: 25, 2: 50}
        shield_price = {0: 0, 1: 400, 2: 1000}
        gun_table = self.weapon_data
        gun_names = {int(key): value["name"] for key, value in gun_table.items()}
        gun_prices = {int(key): int(value["price"]) for key, value in gun_table.items()}
        loadout_df = pd.DataFrame(loadouts, columns=['Match ID', 'Round ID', 'Round', 'Player ID', 'Team ID',
                                                     'Remaining Creds', 'Loadout Value', 'Agent ID', 'Weapon ID',
                                                     'Armor ID'])
        loadout_df["Shield"] = loadout_df["Armor ID"].map(shield_table)
        loadout_df["Shield Price"] = loadout_df["Armor ID"].map(shield_price)
        loadout_df["Weapon Name"] = loadout_df["Weapon ID"].map(gun_names)
        loadout_df["Weapon Price"] = loadout_df["Weapon ID"].map(gun_prices)
        loadout_df["Utility Value"] = loadout_df["Loadout Value"]
        # loadout_df["Utility Value"] = loadout_df["Utility Value"].where(loadout_df["Utility Value"] > 0, 0)
        agent_dict = {int(key): value["name"] for key, value in self.agent_data.items()}
        loadout_df["Agent Name"] = loadout_df['Agent ID'].map(agent_dict)
        column_order = ["Match ID", "Round ID", "Round", "Player ID", "Team ID", "Agent Name", "Weapon Name",
                        "Weapon Price", "Shield", "Shield Price", "Loadout Value", "Remaining Creds", "Agent ID",
                        "Weapon ID", "Armor ID"]
        loadout_df = loadout_df[column_order]
        side_table = self.get_side_info()
        side_dict = {side_table["attacking_first"]: "attack", side_table["defending_first"]: "defense"}
        loadout_df["Starting Side"] = loadout_df['Team ID'].map(side_dict)
        self.reposition_column(loadout_df, "Starting Side", 5)
        loadout_df["Player Name"] = loadout_df['Player ID'].map(self.get_player_names())
        self.reposition_column(loadout_df, "Player Name", 4)
        return loadout_df

    def get_team_economy(self) -> pd.DataFrame:
        """
        Returns a dataframe of the economy table for each team as a whole
        :return: Round, Team ID, Team Remaining Creds, Team Loadout Value, Team Economy
         Shield Total Amount, Shield Total Price, Weapon Total Price
        """
        loadout_df = self.get_initial_state()
        round_amount = loadout_df["Round"].max()
        split_aux = {i: [] for i in range(1, round_amount + 1)}
        for row in loadout_df.iterrows():
            content = row[1]
            round_id = row[1].Round
            split_aux[round_id].append(content)

        group_aux = {}
        for key, value in split_aux.items():
            raw_group = pd.DataFrame(value)
            compact = raw_group.groupby(['Team ID']).agg({'Remaining Creds': 'sum', 'Loadout Value': 'sum',
                                                          'Shield': 'sum', 'Shield Price': 'sum',
                                                          'Weapon Price': 'sum'})
            compact["Round"] = [key] * 2
            compact["Team ID"] = compact.index
            clean_dict = {"Round": list(compact["Round"]),
                          "Team ID": list(compact["Team ID"]),
                          "Remaining Creds": list(compact["Remaining Creds"]),
                          "Loadout Value": list(compact["Loadout Value"]),
                          "Shield Amount": list(compact["Shield"]),
                          "Shield Price": list(compact["Shield Price"]),
                          "Weapon Price": list(compact["Weapon Price"])}
            compact = pd.DataFrame(clean_dict)
            group_aux[key] = compact

        final_df = pd.concat(list(group_aux.values()), axis=0, ignore_index=True)
        final_df["Economy"] = final_df["Remaining Creds"] + final_df["Loadout Value"]
        return final_df

    def get_side_info(self) -> dict:
        """
        Returns a dictionary of the side information for team sides
        :return: team_a: id, team_b: id
                 attacking_first: id, defending_first: id,
                 round_df: DataFrame
        """
        round_df = pd.DataFrame(self.get_all_rounds(), columns=['round_number', 'attacking_team', 'winning_team'])
        teams = tuple(round_df['attacking_team'].unique())
        team_a: int = teams[0]
        team_b: int = teams[1]
        attacking_first = round_df.iloc[0]['attacking_team']
        mirror_dict = {team_a: team_b, team_b: team_a}
        defending_first = mirror_dict[attacking_first]
        return {"team_a": team_a, "team_b": team_b,
                "attacking_first": attacking_first, "defending_first": defending_first,
                "round_df": round_df}

    def get_score_table(self) -> pd.DataFrame:
        """
        Returns a dataframe of the current score table for each round
        :return: Attacking team, Round Winner, Team A Score, Team B Score, Team A Economy, Team B Economy,
                 Map Name, Score Diff, Economy Diff, Match Winner
        """
        side_info = self.get_side_info()
        team_a: int = side_info["team_a"]
        team_b: int = side_info["team_b"]
        attacking_first = side_info["attacking_first"]
        defending_first = side_info["defending_first"]
        round_df = side_info["round_df"]
        team_dict = {team_a: 0, team_b: 0}
        team_scores = {team_a: [], team_b: []}
        for team in round_df['winning_team']:
            if team == team_a:
                team_dict[team_a] += 1
            else:
                team_dict[team_b] += 1
            team_scores[team_a].append(team_dict[team_a])
            team_scores[team_b].append(team_dict[team_b])
        round_df[f"{team_a}_scores"] = team_scores[team_a]
        round_df[f"{team_b}_scores"] = team_scores[team_b]
        economy_table = self.get_team_economy()
        team_a_economies = {a: tuple(economy_table.query(f"Round == {a}").query(f"`Team ID` == {team_a}")["Economy"])[0]
                            for a in list(economy_table["Round"])}
        team_b_economies = {b: tuple(economy_table.query(f"Round == {b}").query(f"`Team ID` == {team_b}")["Economy"])[0]
                            for b in list(economy_table["Round"])}
        round_df[f"{team_a}_economy"] = list(team_a_economies.values())
        round_df[f"{team_b}_economy"] = list(team_b_economies.values())
        match_data = self.get_current_match()[0]
        map_name = match_data[4]
        winning_team = match_data[9]
        round_df = round_df.assign(MapName=map_name)
        round_df["score_diff"] = round_df[f"{attacking_first}_scores"] - round_df[f"{defending_first}_scores"]
        round_df["economy_diff"] = round_df[f"{attacking_first}_economy"] - round_df[f"{defending_first}_economy"]
        round_df = round_df.assign(MatchWinner=winning_team)
        return round_df

    def get_current_round_basic_info(self, chosen_round: int) -> dict:
        states = self.get_initial_state()
        events = self.get_event_table()
        player_alive_dict = {item: True for item in states["Player ID"].unique()}
        current_round_states = states[states['Round'] == chosen_round]
        current_round_events = events[events['Round'] == chosen_round]
        attacking_players = tuple(current_round_states[current_round_states['Starting Side'] == 'attack'][
                                      'Player ID'].unique()) if chosen_round <= 12 else tuple(
            current_round_states[current_round_states['Starting Side'] == 'defense']['Player ID'].unique())
        defending_players = tuple(current_round_states[current_round_states['Starting Side'] == 'defense'][
                                      'Player ID'].unique()) if chosen_round <= 12 else tuple(
            current_round_states[current_round_states['Starting Side'] == 'attack']['Player ID'].unique())
        return {"current_round_alive_dict": player_alive_dict.copy(), "current_round_states": current_round_states,
                "current_round_events": current_round_events, "attacking_players": attacking_players,
                "defending_players": defending_players}

    def get_current_gamestate(self, round_state_table: pd.DataFrame, alive_dict: dict,
                              attacking_players: Tuple[int], defending_players: Tuple[int]) -> dict:
        """
        Returns a dictionary of the current gamestate
        Parameters pulled from self.get_initial_state()

        :param round_state_table: dataframe containing the initial state of the chosen round
        :param alive_dict: dictionary of alive players
        :param attacking_players: list of attacking players IDs from that round
        :param defending_players: list of defending players IDs from that round
        :return: dict of gamestate for both attack and defense
        """
        simple_features = ["Loadout Value", "Shield", "Weapon Price"]
        composite_features = ["Initiator", "Duelist", "Controller", "Sentinel", "Def_has_OP"]
        features = simple_features + composite_features
        atk_data = {feature: 0 for feature in features}
        def_data = atk_data.copy()
        agent_role_dict = self.agent_roles
        def_data["Def_has_OP"] = 0
        for index, item in round_state_table.iterrows():
            player_id = item["Player ID"]
            alive = alive_dict[player_id]
            if alive:
                player_name = item["Player Name"]
                agent_name = item["Agent Name"]
                player_role = agent_role_dict[agent_name]["name"]
                if player_id in attacking_players:
                    atk_data[player_role] += 1
                    for raw_feature in simple_features:
                        atk_data[raw_feature] += item[raw_feature]
                elif player_id in defending_players:
                    player_weapon = item["Weapon Name"]
                    if player_weapon == "Operator":
                        def_data["Def_has_OP"] = 1
                    def_data[player_role] += 1
                    for raw_feature in simple_features:
                        def_data[raw_feature] += item[raw_feature]
                else:
                    Exception("Player ID not in attacking or defending players")
        return {"atk_data": atk_data, "def_data": def_data}

    def aggregate_gamestate(self, chosen_round: int) -> pd.DataFrame:
        """
        Create a dataframe of the current gamestate for a given round
        Variables are set within get_current_gamestate function
        :param chosen_round:
        :return:
        """
        basic_info = self.get_current_round_basic_info(chosen_round)
        current_round_alive_dict = basic_info["current_round_alive_dict"]
        current_round_states = basic_info["current_round_states"]
        current_round_events = basic_info["current_round_events"]
        attacking_players = basic_info["attacking_players"]
        defending_players = basic_info["defending_players"]

        current_gamestate_list = []

        first_state = self.get_current_gamestate(current_round_states, current_round_alive_dict, attacking_players,
                                                 defending_players)
        current_gamestate_list.append(first_state)
        for event in current_round_events.iterrows():
            event_type = event[1]["EventType"]
            victim_id = event[1]["VictimID"]
            if event_type == "kill":
                current_round_alive_dict[victim_id] = False
            elif event_type == "revival":
                current_round_alive_dict[victim_id] = True
            gs = self.get_current_gamestate(current_round_states, current_round_alive_dict, attacking_players,
                                            defending_players)
            current_gamestate_list.append(gs)

        dummy_gamestate_list = []
        for gamestate in current_gamestate_list:
            atk_gamestate = {f"ATK {key}".replace(" ", "_"): value for key, value in gamestate["atk_data"].items()}
            def_gamestate = {f"DEF {key}".replace(" ", "_"): value for key, value in gamestate["def_data"].items()}
            merged_gamestate = {**atk_gamestate, **def_gamestate}
            dummy_gamestate_list.append(merged_gamestate)
        gamestate_df = pd.DataFrame(dummy_gamestate_list)
        timestamps = list(current_round_events["Round_time_millis"])
        timestamps.insert(0, 0)
        gamestate_df.insert(0, "Timestamp", timestamps)
        event_type_column = list(current_round_events["EventType"])
        event_type_column.insert(0, "start")
        gamestate_df.insert(1, "EventType", event_type_column)

        positional_spread = self.get_compaction_from_round(chosen_round)
        gamestate_df.insert(3, "ATK_Spread", positional_spread["atk_spread"])
        gamestate_df.insert(11, "DEF_Spread", positional_spread["def_spread"])
        map_name = self.get_current_map_name()
        gamestate_df.insert(len(gamestate_df), "Map_Name", map_name)
        return gamestate_df


if __name__ == "__main__":
    vq = ValorantQueries()
    vq.set_match(43621)
    vq.aggregate_gamestate(5)
