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
                series_order INTEGER NOT NULL,
                map_id INTEGER NOT NULL,
                FOREIGN KEY (map_id) REFERENCES maps (map_id));""")
        print("Match table created successfully")
        self.conn.commit()

    def create_cities(self):
        self.cursor.execute("""
        CREATE TABLE Cities(id bigint, cityname varchar(128), latitude numeric, longitude numeric);""")
        self.conn.commit()

    def insert_map(self, input_map_id: int, input_map_name: str):
        instruction = f"""
            INSERT INTO Maps(map_id, map_name) VALUES ({input_map_id}, '{input_map_name}') 
            """
        self.cursor.execute(instruction)
        self.conn.commit()
        print("Map id = [{}], Map Name = [{}] inserted successfully".format(input_map_id, input_map_name))

    def delete_map(self, input_map_id: int):
        instruction = f"""
            DELETE FROM Maps WHERE map_id = {input_map_id}
            """
        self.cursor.execute(instruction)
        self.conn.commit()
        print("Map [#{}] was deleted successfully".format(input_map_id))


v = ValorantCreator("valorant")
# v.create_maps_table()
# v.create_match_table()
# v.create_cities()
print(v.get_all_tables())
v.insert_map(4, "Bind")
# v.delete_map(4)
# v.drop_table("matches")
# v.drop_table("maps")
# print(v.get_all_databases())
# print(v.existing_table("map"))


# v.create_map_table()
# print(v.get_all_tables())

# # Preparing query to create a database
# sql = '''CREATE database valorant'''
