from typing import Tuple, List
from dateutil import parser
import psycopg2


class ValorantCreator:
    def __init__(self, database_name: str = "postgres"):
        self.conn = psycopg2.connect(
            database=database_name, user='postgres', password='password', host='127.0.0.1', port='5432'
        )
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()
        print(f"Connected to database {database_name} successfully")
        print(f"{self.get_all_tables()}")

    def close(self):
        self.conn.close()

    def get_all_databases(self) -> List[Tuple[str]]:
        self.cursor.execute("SELECT datname FROM pg_database;")
        return self.cursor.fetchall()

    def existing_database(self, database: str) -> bool:
        return (database,) in self.get_all_databases()

    def get_all_tables(self) -> List[Tuple[str]]:
        self.cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        )
        return self.cursor.fetchall()

    def rebuild_database(self):
        self.drop_all_tables()
        self.create_all_tables()

    def create_database(self, database_name: str):
        existing = self.existing_database(database_name)
        if not existing:
            self.cursor.execute(f"CREATE DATABASE {database_name};")
            print(f"Database [{database_name}] created successfully")
        else:
            print(f"Could not create it. Database [{database_name}] already exists.")

    def change_current_database(self, database_to_connect: str):
        self.__init__(database_to_connect)

    def drop_database(self, database_name: str):
        existing = self.existing_database(database_name)
        if existing:
            self.cursor.execute(f"DROP DATABASE {database_name};")
            print(f"Database [{database_name}] dropped successfully")
        else:
            print(f"Could not drop it. Database [{database_name}] does not exist.")

    def existing_table(self, table_name: str) -> bool:
        return (table_name,) in self.get_all_tables()

    def drop_table(self, table_name: str):
        existing = self.existing_table(table_name)
        if existing:
            self.cursor.execute(f"DROP TABLE {table_name};")
            print(f"Table [{table_name}] dropped")
        else:
            print(f"Could not drop it. Table [{table_name}] does not exist.")

    def select_from_table(self, table_name: str):
        existing = self.existing_table(table_name)
        if existing:
            self.cursor.execute(f"SELECT * FROM {table_name};")
            return self.cursor.fetchall()
        else:
            print(f"Could not select from it. Table [{table_name}] does not exist.")

    def drop_all_tables(self):
        self.drop_table("roundlocations")
        self.drop_table("roundevents")
        self.drop_table("roundeconomies")
        self.drop_table("rounds")
        self.drop_table("matches")
        self.drop_table("maps")
        self.drop_table("series")
        self.drop_table("events")
        self.drop_table("playermapinstance")
        self.drop_table("players")
        self.drop_table("teams")

    def create_all_tables(self):
        self.create_event_table()
        self.create_maps_table()
        self.create_teams_table()
        self.create_players_table()
        self.create_series_table()
        self.create_match_table()
        self.create_round_table()
        self.create_round_economy_table()
        self.create_round_event_table()
        self.create_round_location_table()
        self.create_player_map_instance_table()

    def create_maps_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Maps(
                map_id SERIAL PRIMARY KEY,
                map_name VARCHAR(40) NOT NULL);""")
        print("Map table created successfully")
        self.conn.commit()

    def create_player_map_instance_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS PlayerMapInstance(
                player_instance_id SERIAL PRIMARY KEY,
                player_id INTEGER NOT NULL,
                agent_id INTEGER NOT NULL,
                map_played INTEGER NOT NULL,
                score INTEGER NOT NULL,
                rounds_played INTEGER NOT NULL,
                kills INTEGER NOT NULL,
                deaths INTEGER NOT NULL,
                assists INTEGER NOT NULL,
                FOREIGN KEY (player_id) REFERENCES Players(player_id));""")
        print("Map instance table created successfully")
        self.conn.commit()

    def create_match_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Matches(
                match_id SERIAL PRIMARY KEY,
                series_id INTEGER NOT NULL,
                series_order INTEGER NOT NULL,
                map_id INTEGER NOT NULL,
                map_name VARCHAR(40) NOT NULL,
                start_date VARCHAR(40) NOT NULL,
                length_millis INTEGER NOT NULL,
                attacking_first_team INTEGER NOT NULL,
                red_team INTEGER NOT NULL,
                winning_team INTEGER NOT NULL,
                team_a_score INTEGER NOT NULL,
                team_b_score INTEGER NOT NULL,
                FOREIGN KEY (series_id) REFERENCES Series (series_id),
                FOREIGN KEY (map_id) REFERENCES Maps (map_id));""")
        print("Match table created successfully")
        self.conn.commit()

    def create_round_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Rounds(
                round_id SERIAL PRIMARY KEY,
                match_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                attacking_team INTEGER NOT NULL,
                winning_team INTEGER NOT NULL,
                team_a_economy INTEGER NOT NULL,
                team_b_economy INTEGER NOT NULL,
                win_condition VARCHAR(40) NOT NULL,
                ceremony VARCHAR(40) NOT NULL,
                FOREIGN KEY (match_id) REFERENCES matches (match_id));""")
        print("Round table created successfully")
        self.conn.commit()

    def create_round_event_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS RoundEvents(
                round_event_id SERIAL PRIMARY KEY,
                round_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                round_time_millis INTEGER NOT NULL,
                player_id INTEGER,
                victim_id INTEGER,
                event_type VARCHAR(40) NOT NULL,
                damage_type VARCHAR(40) NOT NULL,
                weapon_id INTEGER,
                ability VARCHAR(40),
                attacking_team_number INTEGER NOT NULL,
                FOREIGN KEY (round_id) REFERENCES Rounds (round_id), 
                FOREIGN KEY (player_id) REFERENCES Players(player_id),
                FOREIGN KEY (victim_id) REFERENCES Players(player_id));""")
        print("Round event table created successfully")
        self.conn.commit()

    def create_round_location_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS RoundLocations(
                round_location_id SERIAL PRIMARY KEY,
                round_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                round_time_millis INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                location_x FLOAT(30) NOT NULL,
                location_y FLOAT(30) NOT NULL,
                view_radians VARCHAR(40) NOT NULL,
                FOREIGN KEY (round_id) REFERENCES Rounds (round_id), 
                FOREIGN KEY (player_id) REFERENCES Players(player_id));""")
        print("Round location table created successfully")
        self.conn.commit()

    def create_round_economy_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS RoundEconomies(
                round_economy_id SERIAL PRIMARY KEY,
                round_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                agent_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                weapon_id INTEGER NOT NULL,
                armor_id INTEGER NOT NULL,
                remaining_creds INTEGER NOT NULL,
                spent_creds INTEGER NOT NULL,
                loadout_value INTEGER NOT NULL,
                FOREIGN KEY (round_id) REFERENCES Rounds (round_id),
                FOREIGN KEY (player_id) REFERENCES Players(player_id));""")
        print("Round location table created successfully")
        self.conn.commit()

    def create_series_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Series(
                series_id SERIAL PRIMARY KEY,
                event_id INTEGER NOT NULL,
                best_of INTEGER NOT NULL,
                team_a_id INTEGER NOT NULL,
                team_b_id INTEGER NOT NULL,
                FOREIGN KEY (event_id) REFERENCES Events(event_id),
                FOREIGN KEY (team_a_id) REFERENCES Teams(team_id),
                FOREIGN KEY (team_b_id) REFERENCES Teams(team_id));""")
        print("Series table created successfully")
        self.conn.commit()

    def create_event_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Events(
                event_id SERIAL PRIMARY KEY,
                event_name VARCHAR(300) NOT NULL,
                event_starting_date VARCHAR(300) NOT NULL,
                stage INTEGER NOT NULL,
                bracket VARCHAR(40) NOT NULL);""")
        print("Event table created successfully")
        self.conn.commit()

    def create_players_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Players(
                player_id SERIAL PRIMARY KEY,
                player_name VARCHAR(40) NOT NULL,
                team_id INTEGER NOT NULL,
                FOREIGN KEY (team_id) REFERENCES Teams(team_id),
                country_id INTEGER NOT NULL);""")
        print("Players table created successfully")
        self.conn.commit()

    def create_teams_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Teams(
                team_id SERIAL PRIMARY KEY,
                team_name VARCHAR(40),
                logo VARCHAR(40),
                country_id INTEGER,
                region_id INTEGER,
                rank INTEGER,
                region_rank INTEGER);""")
        print("Teams table created successfully")
        self.conn.commit()

    def delete_map(self, input_map_id: int):
        instruction = f"""
            DELETE FROM Maps WHERE map_id = {input_map_id}
            """
        self.cursor.execute(instruction)
        self.conn.commit()
        print("Map [#{}] was deleted successfully".format(input_map_id))

    def delete_match(self, input_match_id: int):
        instruction = f"""DELETE FROM Matches WHERE match_id = {input_match_id}"""
        self.cursor.execute(instruction)
        self.conn.commit()
        print("Match [#{}] was deleted successfully".format(input_match_id))

    def insert_map(self, input_map_id: int, input_map_name: str):
        instruction = f"""
            INSERT INTO Maps(map_id, map_name) VALUES ({input_map_id}, '{input_map_name}') 
            """
        self.cursor.execute(instruction)
        self.conn.commit()
        print("Map id = [{}], Map Name = [{}] inserted successfully".format(input_map_id, input_map_name))

    def insert_match(self, i_match_id: int, i_series_id: int, i_series_order: int, i_map_id: int, i_map_name: str,
                     i_start_date: str, i_length_millis: int, i_attacking_first_team: int, i_red_team: int,
                     i_winning_team: int, team_a_score: int, team_b_score: int):
        instruction = f"""
            INSERT INTO Matches(match_id, series_id, series_order, map_id, map_name, start_date, length_millis,
             attacking_first_team, red_team, winning_team, team_a_score, team_b_score)
             VALUES ({i_match_id}, {i_series_id}, {i_series_order}, {i_map_id}, '{i_map_name}', '{i_start_date}',
              {i_length_millis}, {i_attacking_first_team}, {i_red_team}, {i_winning_team}, {team_a_score},
               {team_b_score})"""
        self.cursor.execute(instruction)
        self.conn.commit()
        print(f"Match #{i_match_id} inserted successfully")

    def insert_round(self, i_round_id: int, i_match_id: int, i_round_number: int, i_attacking_team: int,
                     i_winning_team: int, i_team_a_economy: int, i_team_b_economy: int, i_win_condition: str, i_ceremony: str):
        instruction = f"""
        INSERT INTO Rounds(round_id, match_id, round_number, attacking_team, winning_team, team_a_economy,
         team_b_economy, win_condition, ceremony)
        VALUES({i_round_id}, {i_match_id}, {i_round_number}, {i_attacking_team}, {i_winning_team},
        {i_team_a_economy}, {i_team_b_economy}, '{i_win_condition}', '{i_ceremony}')"""
        self.cursor.execute(instruction)
        self.conn.commit()
        print(f"Round [#{i_round_id}] inserted successfully")

    def insert_player(self, i_player_id: int, i_player_name: str, i_team_id: int, i_country_id: int):
        instruction = f"""
        INSERT INTO Players(player_id, player_name, team_id, country_id)
         VALUES({i_player_id}, '{i_player_name}', {i_team_id}, {i_country_id})"""
        self.cursor.execute(instruction)
        self.conn.commit()
        print(f"Player [#{i_player_name}] inserted successfully")

    def insert_event(self, i_event_id: int, i_event_name: str, i_event_date: str, i_event_stage: int,
                     i_event_bracket: str):
        instruction = f"""
        INSERT INTO Events(event_id, event_name, event_starting_date, stage, bracket)
        VALUES({i_event_id}, '{i_event_name}', '{i_event_date}', '{i_event_stage}', '{i_event_bracket}')"""
        self.cursor.execute(instruction)
        self.conn.commit()
        print(f"Event [#{i_event_name}] inserted successfully")

    def insert_team(self, i_team_id: int, i_team_name: str, i_logo: str, i_country_id: int, i_region_id: int,
                    i_rank: int, i_region_rank: int):
        instruction = f"""
        INSERT INTO Teams(team_id, team_name, logo, country_id, region_id, rank, region_rank)
        VALUES({i_team_id}, '{i_team_name}', '{i_logo}', {i_country_id}, {i_region_id}, {i_rank}, {i_region_rank})"""
        self.cursor.execute(instruction)
        self.conn.commit()
        print(f"Team [#{i_team_name}] inserted successfully")

    def insert_series(self, i_series_id: int, i_event_id: int, i_best_of: int, i_team_a_id: int, i_team_b_id: int):
        instruction = f"""
        INSERT INTO Series(series_id, event_id, best_of, team_a_id, team_b_id)
        VALUES({i_series_id}, {i_event_id}, {i_best_of}, {i_team_a_id}, {i_team_b_id})"""
        self.cursor.execute(instruction)
        self.conn.commit()
        print(f"Series [#{i_series_id}] inserted successfully")

    def insert_round_event(self, i_round_id: int, i_round_number: int, i_round_time_millis: int,
                           i_actor_id: int, i_victim_id: int, i_event_type: str, i_damage_type: str, i_weapon_id: int,
                           i_ability: str, i_attacking_team_number: int):
        instruction = f"""
        INSERT INTO RoundEvents(round_id, round_number, round_time_millis, player_id, victim_id,
        event_type, damage_type, weapon_id, ability, attacking_team_number)
        VALUES({i_round_id}, {i_round_number}, {i_round_time_millis}, {i_actor_id}, {i_victim_id},
        '{i_event_type}', '{i_damage_type}', {i_weapon_id}, '{i_ability}', {i_attacking_team_number})"""
        self.cursor.execute(instruction)
        self.conn.commit()
        print(f"Round Event [#{i_round_time_millis}] inserted successfully")

    def insert_round_location(self, i_round_id: int, i_round_number: int, i_round_time_millis: int, i_actor_id: int,
                              i_location_x: float, i_location_y: float, i_view_radians: str):
        instruction = f"""
        INSERT INTO RoundLocations(round_id, round_number, round_time_millis, player_id, location_x, location_y,
        view_radians)
        VALUES({i_round_id}, {i_round_number}, {i_round_time_millis}, {i_actor_id}, {i_location_x}, {i_location_y}, 
        '{i_view_radians}')"""
        self.cursor.execute(instruction)
        self.conn.commit()
        print(f"Round Location [#{i_round_time_millis}] inserted successfully")

    def insert_round_economy(self, i_round_id: int, i_round_number: int, i_actor_id: int,
                             i_agent_id: int, i_score: int, i_weapon_id: int, i_armor_id: int, i_remaining_creds: int,
                             i_spent_creds: int, i_loadout_value: int):
        instruction = f"""
        INSERT INTO RoundEconomies(round_id, round_number, player_id, agent_id, score,
        weapon_id, armor_id, remaining_creds, spent_creds, loadout_value)
        VALUES({i_round_id}, {i_round_number}, {i_actor_id}, {i_agent_id}, {i_score},
        {i_weapon_id}, {i_armor_id}, {i_remaining_creds}, {i_spent_creds}, {i_loadout_value})"""
        self.cursor.execute(instruction)
        self.conn.commit()
        print(f"Round Economy [#{i_round_number}] inserted successfully")


if __name__ == "__main__":
    vc = ValorantCreator("valorant")
    print(vc.select_from_table("players"))
    # vc.drop_all_tables()
    # vc.create_all_tables()

# v.insert_event(779, "VCT North America 2021 - Last Chance Qualifier", "2020-06-01", 4, "losers")
# v.drop_all_tables()
# v.create_all_tables()
# v.drop_table("roundeconomies")
# v.drop_table("roundevents")
# v.drop_table("roundlocations")
# v.drop_table("rounds")
# v.drop_table("matches")
# v.drop_table("maps")

# v.create_round_event_table()
# v.create_round_location_table()
# v.create_round_economy_table()
# v.insert_match(4575, 2, 4)
# v.delete_match(4575)
# v.create_round_table()
# v.insert_match(4575, 2, 4)
# v.create_maps_table()
# v.create_match_table()
# v.create_cities()
# print(v.get_all_tables())
# v.insert_map(4, "Bind")
# v.delete_map(4)
# v.drop_table("matches")
# v.drop_table("roundevents")
# print(v.get_all_databases())
# print(v.existing_table("map"))


# v.insert_round(642220, 4575, 1, 1, 4, 4, "kills", "default")
