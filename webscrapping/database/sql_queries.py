import json
from typing import Tuple, List
from itertools import combinations
from math import sqrt
from line_profiler_pycharm import profile

import pandas as pd

from webscrapping.database.sql_creator import ValorantCreator


class ValorantQueries:
    def __init__(self):
        self.db = ValorantCreator("valorant")
        self.match_id = 0
        self.round_locations, self.match_initial_states, self.match_events, self.map_sides, self.player_names, self.alive_dict = [None] * 6

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
        self.round_locations = self.query_all_round_locations()
        self.map_sides = self.query_player_sides()
        self.match_initial_states = self.get_initial_state()
        self.player_names = list(self.match_initial_states["Player Name"].unique())
        self.match_events = self.get_event_table()
        self.alive_dict = self.generate_match_alive_dict()

    def query_match_db(self):
        instruction = """
        SELECT match_id FROM Matches
        """
        self.db.cursor.execute(instruction)
        aux_df = pd.DataFrame(self.db.cursor.fetchall(), columns=['match_id'])
        return list(aux_df["match_id"])

    def get_all_rounds(self):
        instruction = f"""
        SELECT Rounds.round_number, Rounds.attacking_team, Rounds.winning_team
        FROM Rounds
        where Rounds.match_id = {self.match_id};
        """
        self.db.cursor.execute(instruction)
        return self.db.cursor.fetchall()

    def query_full_round(self):
        instruction = f"""
        SELECT *
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

        player_columns = [item for item in events.columns if item.startswith('Alive_')]
        void_list = []
        for j in range(len(events)):
            row = events.loc[j].copy()
            event_index = row['EventIndex']
            victim_name = f"Alive_{row['VictimName']}"
            event_type = row['EventType']
            if event_index == 1:
                for player in player_columns:
                    row[player] = 1
            else:
                #previous_row = events.loc[j - 1].copy()
                previous_row = void_list[j-1]
                for player in player_columns:
                    row[player] = previous_row[player]
            if event_type == "kill":
                row[victim_name] = 0
            elif event_type == "revival":
                row[victim_name] = 1
            void_list.append(row)
        events = pd.DataFrame(void_list)
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

    @profile
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
        side_pot = []
        for row_index in range(len(loadout_df)):
            row = loadout_df.iloc[row_index].copy()
            round_id = row["Round"]
            player_id = row["Player ID"]
            player_side = "defense" if player_id in nested_dict[round_id]["defenders"] else "attack"
            row["Player Side"] = player_side
            side_pot.append(row)

        loadout_df = pd.DataFrame(side_pot)
        loadout_df["Starting Side"] = loadout_df['Team ID'].map(side_dict)

        loadout_df["Player Name"] = loadout_df['Player ID'].map(self.get_player_names())
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
        match_data = self.query_current_match()[0]
        map_name = match_data[4]
        winning_team = match_data[9]
        round_df = round_df.assign(MapName=map_name)
        round_df["score_diff"] = round_df[f"{attacking_first}_scores"] - round_df[f"{defending_first}_scores"]
        round_df["economy_diff"] = round_df[f"{attacking_first}_economy"] - round_df[f"{defending_first}_economy"]
        round_df = round_df.assign(MatchWinner=winning_team)
        return round_df

    def get_current_round_basic_info(self, chosen_round: int) -> dict:
        states = self.match_initial_states
        events = self.match_events
        player_alive_dict = {item: True for item in states["Player ID"].unique()}
        current_round_states = states[states['Round'] == chosen_round]
        current_round_events = events[events['Round'] == chosen_round]
        self.reposition_column(current_round_states, "Starting Side", 3)
        current_round_states = current_round_states.sort_values(by=["Starting Side"])

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
        composite_features = ["Initiator", "Duelist", "Controller", "Sentinel", "has_OP"]
        features = simple_features + composite_features
        atk_data = {feature: 0 for feature in features}
        def_data = atk_data.copy()
        agent_role_dict = self.agent_roles
        def_data["has_OP"] = 0
        for index, item in round_state_table.iterrows():
            player_id = item["Player ID"]
            alive = alive_dict[player_id]
            if alive:
                player_name = item["Player Name"]
                agent_name = item["Agent Name"]
                player_role = agent_role_dict[agent_name]["name"]
                player_weapon = item["Weapon Name"]
                if player_id in attacking_players:
                    if player_weapon == "Operator":
                        atk_data["has_OP"] = 1
                    atk_data[player_role] += 1
                    for raw_feature in simple_features:
                        atk_data[raw_feature] += item[raw_feature]
                elif player_id in defending_players:
                    def_data[player_role] += 1
                    if player_weapon == "Operator":
                        def_data["has_OP"] = 1
                    for raw_feature in simple_features:
                        def_data[raw_feature] += item[raw_feature]
                else:
                    Exception("Player ID not in attacking or defending players")
        return {"atk_data": atk_data, "def_data": def_data}

    def get_event_impact_into_gamestate(self, victim_df: pd.DataFrame, event_type: str) -> dict:
        victim_dict = victim_df.to_dict(orient="Records")[0]
        simple_features = ["Loadout Value", "Shield", "Weapon Price"]
        composite_features = ["Initiator", "Duelist", "Controller", "Sentinel", "Operator"]
        features = simple_features + composite_features
        agent_role_dict = self.agent_roles
        feature_impact = {feature: 0 for feature in features}
        victim_role = agent_role_dict[victim_dict["Agent Name"]]["name"]
        victim_operator = 1 if victim_dict["Weapon Name"] == "Operator" else 0
        factor = 1 if event_type == "kill" else -1
        feature_impact[victim_role] = -1 * factor
        feature_impact["Operator"] = -1 * victim_operator * factor
        for simple in simple_features:
            feature_impact[simple] = -victim_dict[simple] * factor
        return feature_impact

    def get_gamestate_dataframe(self) -> pd.DataFrame:
        aux = self.get_initial_state()
        aux_a = aux[aux["Status"] == "alive"]
        aux_b = aux.groupby(["Round", "Team ID"])
        agg_columns = ("Remaining Creds", "Loadout Value", "Weapon Price", "Shield",
                       "Controller", "Duelist", "Initiator", "Sentinel")
        agg_dict = {col: 'sum' for col in agg_columns}
        agg_dict["Has Operator"] = "any"
        return aux_b.agg(agg_dict).reset_index()

    def generate_match_alive_dict(self) -> dict:
        states = self.match_initial_states
        events = self.match_events
        id_dict = dict(zip(states["Player ID"].unique(), states["Player Name"].unique()))
        event_amount_table = events.groupby(["Round"]).count().reset_index()
        event_amount_dict = dict(zip(event_amount_table["Round"], event_amount_table["EventIndex"]))
        match_alive_dict = {key: {v: 0 for v in range(1, item + 1)} for key, item in event_amount_dict.items()}
        players = list(states["Player Name"].unique())
        all_players = ["Alive_" + sub for sub in players]
        for row_index in range(len(events)):
            row = events.iloc[row_index]
            round_number = int(row["Round"])
            event_index = int(row["EventIndex"])
            players_alive = dict(row[all_players])
            trimmed = {key[6:]: value for key, value in players_alive.items()}
            match_alive_dict[round_number][event_index] = trimmed
        return match_alive_dict

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

        round_winner = self.did_attack_win_that_round(chosen_round)
        column_amount = gamestate_df.shape[1]
        gamestate_df.insert(column_amount, "FinalWinner", round_winner)
        return gamestate_df

    def aggregate_match_gamestate(self) -> pd.DataFrame:
        round_amount = self.get_round_amount()
        round_list = [self.aggregate_gamestate(i) for i in range(1, round_amount + 1)]
        return pd.concat(round_list)


if __name__ == "__main__":
    vq = ValorantQueries()
    vq.set_match(43621)
    vq.aggregate_match_gamestate()
