from typing import Tuple, List

import psycopg2


class ValorantDB:
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

    def create_map_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS map (
                map_id SERIAL PRIMARY KEY,
                map_name VARCHAR(40) NOT NULL);""")


v = ValorantDB("valorant")
v.create_map_table()
print(v.get_all_tables())
# print(v.get_all_databases())
# print(v.existing_table("map"))
# print(v.drop_table("map"))

# v.create_map_table()
# print(v.get_all_tables())

# # Preparing query to create a database
# sql = '''CREATE database valorant'''
