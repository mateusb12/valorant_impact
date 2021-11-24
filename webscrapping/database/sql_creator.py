from typing import Tuple, List

import psycopg2


class ValorantCreator:
    def __init__(self, database_name: str = "postgres"):
        self.conn = psycopg2.connect(
            database=database_name, user='postgres', password='password', host='127.0.0.1', port='5432'
        )
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

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
            print(f"Table [{table_name}] dropped successfully")
        else:
            print(f"Could not drop it. Table [{table_name}] does not exist.")

    def drop_all_tables(self):
        self.drop_table("roundlocations")
        self.drop_table("roundevents")
        self.drop_table("roundeconomies")
        self.drop_table("rounds")
        self.drop_table("matches")
        self.drop_table("maps")
        self.drop_table("series")
        self.drop_table("events")
        self.drop_table("teams")
        self.drop_table("players")

    def create_all_tables(self):
        self.create_players_table()
        self.create_event_table()
        self.create_maps_table()
        self.create_teams_table()
        self.create_series_table()
        self.create_match_table()
        self.create_round_table()
        self.create_round_economy_table()
        self.create_round_event_table()
        self.create_round_location_table()

    def create_maps_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Maps(
                map_id SERIAL PRIMARY KEY,
                map_name VARCHAR(40) NOT NULL);""")
        print("Map table created successfully")
        self.conn.commit()

    def create_match_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Matches(
                match_id SERIAL PRIMARY KEY,
                series_id INTEGER NOT NULL,
                series_order INTEGER NOT NULL,
                map_id INTEGER NOT NULL,
                start_date DATE NOT NULL,
                length_milis INTEGER NOT NULL,
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
                round_time_milis INTEGER NOT NULL,
                actor_id INTEGER,
                victim_id INTEGER,
                event_type VARCHAR(40) NOT NULL,
                damage_type VARCHAR(40) NOT NULL,
                weapon_id INTEGER,
                ability VARCHAR(40),
                attacking_team_number INTEGER NOT NULL,
                FOREIGN KEY (round_id) REFERENCES Rounds (round_id));""")
        print("Round event table created successfully")
        self.conn.commit()

    def create_round_location_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS RoundLocations(
                round_location_id SERIAL PRIMARY KEY,
                round_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                round_time_milis INTEGER NOT NULL,
                actor_id INTEGER NOT NULL,
                location_x FLOAT(30) NOT NULL,
                location_y FLOAT(30) NOT NULL,
                view_radians VARCHAR(40) NOT NULL,
                FOREIGN KEY (round_id) REFERENCES Rounds (round_id));""")
        print("Round location table created successfully")
        self.conn.commit()

    def create_round_economy_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS RoundEconomies(
                round_economy_id SERIAL PRIMARY KEY,
                round_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                actor_id INTEGER NOT NULL,
                agent_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                weapon_id INTEGER NOT NULL,
                armor_id INTEGER NOT NULL,
                remaining_creds INTEGER NOT NULL,
                spent_creds INTEGER NOT NULL,
                loadout_value INTEGER NOT NULL,
                FOREIGN KEY (round_id) REFERENCES Rounds (round_id));""")
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
                FOREIGN KEY (event_id) REFERENCES Events (event_id));""")
        print("Series table created successfully")
        self.conn.commit()

    def create_event_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Events(
                event_id SERIAL PRIMARY KEY,
                event_name VARCHAR(40) NOT NULL,
                event_starting_date DATE NOT NULL,
                stage INTEGER NOT NULL,
                bracket VARCHAR(40) NOT NULL);""")
        print("Event table created successfully")
        self.conn.commit()

    def create_players_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Players(
                player_id SERIAL PRIMARY KEY,
                player_name VARCHAR(40) NOT NULL,
                country_id INTEGER NOT NULL);""")
        print("Players table created successfully")
        self.conn.commit()

    def create_teams_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Teams(
                team_id SERIAL PRIMARY KEY,
                team_name VARCHAR(40),
                short_name VARCHAR(40),
                website VARCHAR(40),
                logo VARCHAR(40),
                country_id INTEGER,
                region_id INTEGER,
                rank INTEGER,
                region_rank INTEGER,
                player_A INTEGER NOT NULL,
                player_B INTEGER NOT NULL,
                player_C INTEGER NOT NULL,
                player_D INTEGER NOT NULL,
                player_E INTEGER NOT NULL,
                FOREIGN KEY (player_A) REFERENCES Players(player_id),
                FOREIGN KEY (player_B) REFERENCES Players(player_id),
                FOREIGN KEY (player_C) REFERENCES Players(player_id),
                FOREIGN KEY (player_D) REFERENCES Players(player_id),
                FOREIGN KEY (player_E) REFERENCES Players(player_id));""")
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

    def insert_match(self, input_match_id: int, input_series_order: int, input_map_id: int):
        instruction = f"""
            INSERT INTO Matches(match_id, series_order, map_id)
             VALUES ({input_match_id}, {input_series_order}, {input_map_id})"""
        self.cursor.execute(instruction)
        self.conn.commit()
        print("Match id = [{}], Series Order = [{}], Map id = [{}] inserted successfully"
              .format(input_match_id, input_series_order, input_map_id))

    def insert_round(self, i_round_id: int, i_match_id: int, i_round_number: int, i_winning_team: int,
                     i_team_a_economy: int, i_team_b_economy: int, i_win_condition: str, i_ceremony: str):
        instruction = f"""
        INSERT INTO Rounds(round_id, match_id, round_number, winning_team, team_a_economy, team_b_economy,
        win_condition, ceremony) VALUES({i_round_id}, {i_match_id}, {i_round_number}, {i_winning_team},
        {i_team_a_economy}, {i_team_b_economy}, '{i_win_condition}', '{i_ceremony}')"""
        self.cursor.execute(instruction)
        self.conn.commit()
        print(f"Round id = [{i_round_id}], Match id = [{i_match_id}], Round number = [{i_round_number}],"
              f" Winning team = [{i_winning_team}], Team A Economy = [{i_team_a_economy}], "
              f"Team B Economy = [{i_team_b_economy}], Win condition = [{i_win_condition}], Ceremony = [{i_ceremony}],"
              f" inserted successfully.")


v = ValorantCreator("valorant")
v.drop_all_tables()
v.create_all_tables()
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
