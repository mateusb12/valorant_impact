import json
from typing import Tuple, List
from itertools import combinations
from math import sqrt
from line_profiler_pycharm import profile
from collections import Counter

import pandas as pd

from webscrapping.database.sql_creator import ValorantCreator


class ValorantQueries:
    def __init__(self):
        self.db = ValorantCreator("valorant")
        self.match_id = 0
        self.round_locations, self.match_initial_states, self.match_events, self.map_sides = [None] * 4
        self.player_names, self.alive_dict, self.round_states, self.round_events = [None] * 4
        self.chosen_round, self.round_winner_dict, self.match_state_dict = [None] * 3

        weapon_file = open('..\\matches\\model\\weapon_table.json')
        self.weapon_data = json.load(weapon_file)

        agent_file = open('..\\matches\\model\\agent_table.json')
        self.agent_data = json.load(agent_file)

        maps_file = open('..\\matches\\model\\map_table.json')
        self.maps_data = json.load(maps_file)

        agent_roles_file = open('..\\matches\\model\\agent_roles.json')
        self.agent_roles = json.load(agent_roles_file)

    @profile
    def set_match(self, input_match_id: int):
        self.match_id = input_match_id
        self.round_locations = self.query_all_round_locations()
        self.map_sides = self.query_player_sides()
        self.match_initial_states = self.get_initial_state()
        self.player_names = list(self.match_initial_states["Player Name"].unique())
        self.match_events = self.get_event_table()
        self.match_state_dict = self.generate_match_dict_table()

    def query_match_db(self):
        instruction = """
        SELECT match_id FROM Matches
        """
        self.db.cursor.execute(instruction)
        aux_df = pd.DataFrame(self.db.cursor.fetchall(), columns=['match_id'])
        return list(aux_df["match_id"])

    def query_all_rounds(self):
        instruction = f"""
        SELECT Rounds.round_number, Rounds.attacking_team, Rounds.winning_team
        FROM Rounds
        where Rounds.match_id = {self.match_id};
        """
        self.db.cursor.execute(instruction)
        return self.db.cursor.fetchall()

    def round_winner_dataframe(self) -> pd.DataFrame:
        aux = self.query_all_rounds()
        df_aux = pd.DataFrame(aux, columns=['round_number', 'attacking_team', 'winning_team'])
        df_aux["attackers_won"] = df_aux["winning_team"] == df_aux["attacking_team"]
        df_aux["attackers_won"] = df_aux["attackers_won"].astype(int)
        return df_aux

    def query_full_round(self):
        instruction = f"""
        SELECT *
        FROM Rounds
        where Rounds.match_id = {self.match_id};
        """
        self.db.cursor.execute(instruction)
        return self.db.cursor.fetchall()

    def query_all_rounds_old(self):
        query = f"""
                SELECT 'Round' as ta, Rounds.*, 'Match' as tb, Matches.*
                FROM Rounds
                JOIN Matches ON matches.match_id = rounds.match_id
                where Matches.match_id = {self.match_id};
            """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    def query_economies(self):
        query = f"""
            SELECT 'RoundEconomies' as ta, RoundEconomies.*, 'Rounds' as td, Rounds.*, 'Matches' as te, Matches.*
            FROM RoundEconomies
            INNER JOIN Rounds ON RoundEconomies.round_id = Rounds.round_id
            INNER JOIN Matches ON Rounds.match_id = Matches.match_id
            WHERE Matches.match_id = {self.match_id}
        """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    def query_current_match(self):
        query = f"""
        SELECT * FROM Matches WHERE match_id = {self.match_id}
        """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    def get_current_map_name(self):
        return self.query_current_match()[0][4]

    def query_loadouts(self):
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

    def query_full_loadouts(self):
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

    def query_events(self):
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
        aux_df_columns = ('Round', 'Round_time_millis', 'PlayerID', 'VictimID', 'EventType', 'DamageType',
                          'WeaponID', 'Ability')
        aux_df = pd.DataFrame(self.db.cursor.fetchall(), columns=aux_df_columns)
        player_names = self.get_player_names()
        aux_df["PlayerName"] = aux_df['PlayerID'].map(player_names)
        self.reposition_column(aux_df, 'PlayerName', 3)
        aux_df["VictimName"] = aux_df['VictimID'].map(player_names)
        self.reposition_column(aux_df, 'VictimName', 5)
        events = pd.concat([aux_df, pd.get_dummies(aux_df["PlayerName"], prefix="Alive")], axis=1)
        aux_occur = events.groupby(["Round"]).count().reset_index()
        aux_occur = aux_occur[["Round", "Round_time_millis"]]
        aux_occur = aux_occur.rename(columns={"Round_time_millis": "Events Amount"})
        aux_indexes = []
        events_amount_indexes = lambda x: [i for i in range(1, x + 1)]
        for item in aux_occur["Events Amount"]:
            aux_indexes.extend(events_amount_indexes(item))
        events["EventIndex"] = aux_indexes
        self.reposition_column(events, "EventIndex", 1)

        # player_columns = [item for item in events.columns if item.startswith('Alive_')]
        # void_list = []
        # for j in range(len(events)):
        #     row = events.loc[j].copy()
        #     event_index = row['EventIndex']
        #     victim_name = f"Alive_{row['VictimName']}"
        #     event_type = row['EventType']
        #     if event_index == 1:
        #         for player in player_columns:
        #             row[player] = 1
        #     else:
        #         # previous_row = events.loc[j - 1].copy()
        #         previous_row = void_list[j - 1]
        #         for player in player_columns:
        #             row[player] = previous_row[player]
        #     if event_type == "kill":
        #         row[victim_name] = 0
        #     elif event_type == "revival":
        #         row[victim_name] = 1
        #     void_list.append(row)
        # events = pd.DataFrame(void_list)
        return events

    def query_all_round_locations(self):
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

    def query_player_sides(self):
        query = f"""
            SELECT player_id, map_played, team_id, first_side, rounds_played
            FROM PLayerMapInstance WHERE PLayerMapInstance.map_played = {self.match_id}
        """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    def get_player_sides_table(self):
        side_table = pd.DataFrame(self.map_sides,
                                  columns=['player_id', 'map_played', 'team_id', 'first_side', 'rounds_played'])
        attacking_players = list(side_table[side_table['first_side'] == 'attacker']["player_id"])
        defending_players = list(side_table[side_table['first_side'] == 'defender']["player_id"])
        round_amount = int(side_table["rounds_played"].unique())
        side_pattern = ["normal"] * 12
        if round_amount > 24:
            side_pattern += ["inverse"] * 12
            ot_rounds = round_amount - 24
            for item in range(1, ot_rounds + 1):
                side_pattern += ["normal"] if item % 2 == 1 else ["inverse"]
        else:
            remaining = round_amount - 12
            side_pattern += ["inverse"] * remaining

        side_pattern_dict = {i: side for i, side in enumerate(side_pattern, 1)}
        return {"attackers": attacking_players, "defenders": defending_players, "side_pattern": side_pattern_dict}

    def get_player_sides_by_round(self, round_number: int, player_side_table: dict = None) -> dict:
        side_dict = self.get_player_sides_table() if player_side_table is None else player_side_table
        attacking_players = side_dict["attackers"]
        defending_players = side_dict["defenders"]
        side_pattern_dict = side_dict["side_pattern"]
        round_type = side_pattern_dict[round_number]
        if round_type == "normal":
            return {"attackers": attacking_players, "defenders": defending_players}
        elif round_type == "inverse":
            return {"attackers": defending_players, "defenders": attacking_players}

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

    def get_round_amount(self) -> int:
        query = f"""SELECT match_id, team_a_score, team_b_score FROM MATCHES WHERE match_id = {self.match_id}"""
        self.db.cursor.execute(query)
        aux = self.db.cursor.fetchall()[0]
        return aux[1] + aux[2]

    def did_attack_win_that_round(self, round_number: int) -> int:
        score_table = self.query_full_round()
        score_table_df = pd.DataFrame(score_table,
                                      columns=["RoundID", "MatchID", "RoundNumber", "Attacking_Team", "WinningTeam",
                                               "Team_A_Economy", "Team_B_Economy", "Win_condition", "Ceremony"])
        score_table_df = score_table_df[score_table_df["RoundNumber"] == round_number]
        attacking_team = int(score_table_df["Attacking_Team"])
        winning_team = int(score_table_df["WinningTeam"])
        return 1 if attacking_team == winning_team else 0

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
        locations = self.round_locations
        current_round_locations = locations[locations['Round'] == current_round]
        side_info = self.get_player_sides_by_round(current_round)
        attacking_players = side_info["attackers"]
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

    @profile
    def get_initial_state(self):
        """
        Returns a list of all players states for a given match
        :return: Round, Player ID, Team ID, Remaining Creds, Loadout Value, Agent ID, Weapon ID, Armor ID,
        Shield, Shield Price, Weapon Name, Weapon Price, Utility Value
        """
        loadouts = self.query_full_loadouts()
        agent_role_dict = {key: value["name"] for key, value in self.agent_roles.items()}
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
        agent_dict = {int(key): value["name"] for key, value in self.agent_data.items()}
        loadout_df["Agent Name"] = loadout_df['Agent ID'].map(agent_dict)
        loadout_df["Agent Role"] = loadout_df['Agent Name'].map(agent_role_dict)
        side_table = self.get_side_info()
        side_dict = {side_table["attacking_first"]: "attack", side_table["defending_first"]: "defense"}
        aux_side_table = self.get_player_sides_table()
        max_rounds = loadout_df["Round"].max()
        nested_dict = {item: self.get_player_sides_by_round(item, aux_side_table) for item in range(1, max_rounds + 1)}
        nested_player_dict = {item: {} for item in range(1, max_rounds+1)}
        prefix_round = list(loadout_df["Round"])
        prefix_ids = list(loadout_df["Player ID"])
        prefix_merged = [f"{item[0]}_{item[1]}" for item in zip(prefix_round, prefix_ids)]
        loadout_df["Tag"] = prefix_merged
        for key, nested_value in nested_dict.items():
            attacker_ids = nested_value["defenders"]
            defender_ids = nested_value["attackers"]
            merged_ids = attacker_ids + defender_ids
            merged_sides = {
                player_id: "attack" if player_id in attacker_ids else "defense"
                for player_id in merged_ids
            }
            nested_player_dict[key] = merged_sides
        loadout_df["Player Side"] = loadout_df["Tag"].map(
            lambda x: nested_player_dict[int(x.split("_")[0])][int(x.split("_")[1])]
        )
        loadout_df = loadout_df.drop("Tag", axis=1)
        loadout_df["Starting Side"] = loadout_df['Team ID'].map(side_dict)
        names = self.get_player_names()
        loadout_df["Player Name"] = loadout_df['Player ID'].map(names)
        self.reposition_column(loadout_df, "Player Side", 5)
        self.reposition_column(loadout_df, "Player Name", 4)
        loadout_df.insert(5, "Status", "alive")
        loadout_df = pd.concat([loadout_df.drop('Agent Role', axis=1), pd.get_dummies(loadout_df['Agent Role'])],
                               axis=1)
        loadout_df["Has Operator"] = loadout_df["Weapon Name"].apply(lambda x: "Operator" in x)
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
        round_df = pd.DataFrame(self.query_all_rounds(), columns=['round_number', 'attacking_team', 'winning_team'])
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
        match_data = self.query_current_match()[0]
        map_name = match_data[4]
        winning_team = match_data[9]
        round_df = round_df.assign(MapName=map_name)
        round_df["score_diff"] = round_df[f"{attacking_first}_scores"] - round_df[f"{defending_first}_scores"]
        round_df["economy_diff"] = round_df[f"{attacking_first}_economy"] - round_df[f"{defending_first}_economy"]
        round_df = round_df.assign(MatchWinner=winning_team)
        return round_df

    def generate_match_dict_table(self) -> dict:
        states = self.match_initial_states
        round_amount = states["Round"].max()
        round_dict = {r: {} for r in range(1, round_amount + 1)}
        aux = states.to_dict(orient="records")
        for element in aux:
            round_number = element["Round"]
            player_name = element["Player Name"]
            round_dict[round_number][player_name] = element
        return round_dict

    def get_match_gamestate_table(self) -> pd.DataFrame:
        round_winner_table = self.round_winner_dataframe()
        round_amount = round_winner_table["round_number"].max()
        self.round_winner_dict = dict(zip(round_winner_table["round_number"], round_winner_table["attackers_won"]))
        round_gamestates = [self.get_round_gamestates(i) for i in range(1, round_amount + 1)]
        flat_list = [item for sublist in round_gamestates for item in sublist]
        return pd.DataFrame(flat_list)

    def get_round_gamestates(self, chosen_round: int) -> List[dict]:
        self.chosen_round = chosen_round
        states = self.match_initial_states
        events = self.match_events
        self.round_states = states[(states["Round"] == chosen_round)]
        self.round_events = events[(events["Round"] == chosen_round)]
        self.alive_dict = {item: "alive" for item in self.round_states["Player Name"].unique()}
        zero_row = self.round_events.iloc[0]
        info_pot = [self.get_single_event_gamestate(zero_row, 0, 0)]
        for row_index in range(len(self.round_events)):
            row = self.round_events.iloc[row_index]
            remaining_info = self.get_single_event_gamestate(row)
            info_pot.append(remaining_info)
        return info_pot

    def get_single_event_gamestate(self, input_row: pd.Series,
                                   event_index: int = None, event_time: int = None) -> dict:
        event_index = int(input_row["EventIndex"]) if event_index is None else event_index
        event_time = int(input_row["Round_time_millis"]) if event_time is None else event_time
        victim = input_row["VictimName"]
        event_type = input_row["EventType"]
        if event_index != 0:
            if event_type == "kill":
                self.alive_dict[victim] = "dead"
            elif event_type == "revive":
                self.alive_dict[victim] = "alive"
        attack, defense = self.get_alive_only_gamestate()
        combined_info = {"Round": self.chosen_round, "EventIndex": event_index, "Time": event_time}
        combined_info.update(attack)
        combined_info.update(defense)
        combined_info["FinalWinner"] = self.round_winner_dict[self.chosen_round]
        return combined_info

    def get_alive_only_gamestate(self) -> Tuple[dict, dict]:
        default_variables = ["Sentinel", "Initiator", "Duelist", "Controller", "Has Operator", "Loadout Value",
                             "Remaining Creds", "Weapon Price", "Shield"]
        atk_pot = {item: 0 for item in default_variables}
        def_pot = {item: 0 for item in default_variables}
        state_dict = self.match_state_dict
        round_dict = state_dict[self.chosen_round]
        for name, info in round_dict.items():
            player_status = self.alive_dict[name]
            if player_status == "alive":
                player_contribution = {item: info[item] for item in default_variables}
                player_side = info["Player Side"]
                for variable in default_variables:
                    if player_side == "attack":
                        atk_pot[variable] += player_contribution[variable]
                    elif player_side == "defense":
                        def_pot[variable] += player_contribution[variable]
        atk_d = {f'ATK_{key}': value for key, value in atk_pot.items()}
        def_d = {f'ATK_{key}': value for key, value in def_pot.items()}
        return atk_d, def_d

    def get_efficient_alive_only_gamestate(self) -> Tuple[dict, dict]:
        default_variables = ["Sentinel", "Initiator", "Duelist", "Controller", "Has operator", "Loadout Value",
                             "Remaining Creds", "Weapon Price", "Shield"]

        atk_sentinel, atk_initiator, atk_duelist, atk_controller, atk_has_operator = [0] * 5
        atk_loadout, atk_creds, atk_weapon, atk_shield = [0] * 4

        def_sentinel, def_initiator, def_duelist, def_controller, def_has_operator = [0] * 5
        def_loadout, def_creds, def_weapon, def_shield = [0] * 4

        state_dict = self.match_state_dict
        round_dict = state_dict[self.chosen_round]
        for name, info in round_dict.items():
            player_status = self.alive_dict[name]
            if player_status == "alive":
                player_side = info["Player Side"]
                player_creds = info["Remaining Creds"]
                player_loadout = info["Loadout Value"]
                player_shield = info["Shield"]
                player_weapon_price = info["Weapon Price"]
                player_controller = info["Controller"]
                player_has_operator = info["Has Operator"]
                player_initiator = info["Initiator"]
                player_duelist = info["Duelist"]
                player_sentinel = info["Sentinel"]
                if player_side == "attack":
                    atk_sentinel += player_sentinel
                    atk_initiator += player_initiator
                    atk_duelist += player_duelist
                    atk_controller += player_controller
                    atk_has_operator += player_has_operator
                    atk_loadout += player_loadout
                    atk_creds += player_creds
                    atk_weapon += player_weapon_price
                    atk_shield += player_shield
                else:
                    def_sentinel += player_sentinel
                    def_initiator += player_initiator
                    def_duelist += player_duelist
                    def_controller += player_controller
                    def_has_operator += player_has_operator
                    def_loadout += player_loadout
                    def_creds += player_creds
                    def_weapon += player_weapon_price
                    def_shield += player_shield
        atk_d = {"ATK_Sentinel": atk_sentinel, "ATK_Initiator": atk_initiator, "ATK_Duelist": atk_duelist,
                 "ATK_Controller": atk_controller, "ATK_Has Operator": atk_has_operator,
                 "ATK_Loadout Value": atk_loadout, "ATK_Remaining Creds": atk_creds, "ATK_Weapon Price": atk_weapon,
                 "ATK_Shield": atk_shield}
        def_f = {"DEF_Sentinel": def_sentinel, "DEF_Initiator": def_initiator, "DEF_Duelist": def_duelist,
                 "DEF_Controller": def_controller, "DEF_Has Operator": def_has_operator,
                 "DEF_Loadout Value": def_loadout, "DEF_Remaining Creds": def_creds, "DEF_Weapon Price": def_weapon,
                 "DEF_Shield": def_shield}
        return atk_d, def_f

    def export_df(self, match_number: int) -> pd.DataFrame:
        self.set_match(match_number)
        return self.get_match_gamestate_table()


if __name__ == "__main__":
    vq = ValorantQueries()
    vq.export_df(43621)
    apple = 5 + 1
