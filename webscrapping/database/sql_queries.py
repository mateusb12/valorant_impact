import json
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

    def get_kills(self) -> pd.DataFrame:
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
        loadout_df["Utility Value"] = \
            loadout_df["Loadout Value"] - loadout_df["Shield Price"] - loadout_df["Weapon Price"]
        loadout_df["Utility Value"] = loadout_df["Utility Value"].where(loadout_df["Utility Value"] > 0, 0)
        agent_dict = {int(key): value["name"] for key, value in self.agent_data.items()}
        loadout_df["Agent Name"] = loadout_df['Agent ID'].map(agent_dict)
        column_order = ["Match ID", "Round ID", "Round", "Player ID", "Team ID", "Agent Name", "Weapon Name",
                        "Weapon Price", "Shield", "Shield Price", "Utility Value", "Remaining Creds", "Agent ID",
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

    def generate_current_game_state(self):
        loadouts = self.get_loadouts()
        events = self.get_events()
        loadout_df = pd.DataFrame(loadouts, columns=['Match ID', 'Round ID', 'Round', 'Player ID',
                                                     'Team ID', 'Remaining Creds', 'Loadout Value'])
        loadout_df = loadout_df.sort_values(by=['Round'])
        round_amount = loadout_df["Round"].max()


if __name__ == "__main__":
    vq = ValorantQueries()
    vq.set_match(10597)
    vq.generate_current_game_state()
