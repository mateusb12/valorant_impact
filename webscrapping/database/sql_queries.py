import pandas as pd

from webscrapping.database.sql_creator import ValorantCreator


class ValorantQueries:
    def __init__(self):
        self.db = ValorantCreator("valorant")
        self.match_id = 0

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

    def get_economy_table(self) -> pd.DataFrame:
        loadout_query = self.get_loadouts()
        loadout_df = pd.DataFrame(loadout_query,
                                  columns=['Match ID', 'Round ID', 'Round', 'Player ID', 'Team ID', 'Remaining Creds',
                                           'Loadout Value'])
        loadout_df = loadout_df.sort_values(by=['Round'])
        round_amount = loadout_df["Round"].max()
        split_aux = {i: [] for i in range(1, round_amount + 1)}
        for row in loadout_df.iterrows():
            content = row[1]
            round_id = row[1].Round
            split_aux[round_id].append(content)

        group_aux = {}
        for key, value in split_aux.items():
            raw_group = pd.DataFrame(value)
            compact = raw_group.groupby(['Team ID']).agg({'Remaining Creds': 'sum', 'Loadout Value': 'sum'})
            compact["Round"] = [key] * 2
            compact["Team ID"] = compact.index
            clean_dict = {"Round": list(compact["Round"]),
                          "Team ID": list(compact["Team ID"]),
                          "Remaining Creds": list(compact["Remaining Creds"]),
                          "Loadout Value": list(compact["Loadout Value"])}
            compact = pd.DataFrame(clean_dict)
            group_aux[key] = compact

        final_df = pd.concat(list(group_aux.values()), axis=0, ignore_index=True)
        final_df["Economy"] = final_df["Remaining Creds"] + final_df["Loadout Value"]
        return final_df

    def get_score_table(self):
        round_df = pd.DataFrame(self.get_all_rounds(), columns=['round_number', 'attacking_team', 'winning_team'])
        teams = tuple(round_df['attacking_team'].unique())
        team_a: int = teams[0]
        team_b: int = teams[1]
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
        economy_table = self.get_economy_table()
        team_a_economies = {a: tuple(economy_table.query(f"Round == {a}").query(f"`Team ID` == {team_a}")["Economy"])[0]
                            for a in list(economy_table["Round"])}
        team_b_economies = {b: tuple(economy_table.query(f"Round == {b}").query(f"`Team ID` == {team_b}")["Economy"])[0]
                            for b in list(economy_table["Round"])}
        round_df[f"{team_a}_economy"] = list(team_a_economies.values())
        round_df[f"{team_b}_economy"] = list(team_b_economies.values())
        match_data = self.get_current_match()[0]
        map_name = match_data[4]
        winning_team = match_data[9]
        round_df = round_df.assign(MapName=map_name, WinningTeam=winning_team)
        apple = 5 + 1


if __name__ == "__main__":
    vq = ValorantQueries()
    vq.set_match(10597)
    apple = vq.get_current_match()
    vq.get_score_table()
