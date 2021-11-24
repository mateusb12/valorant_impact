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

    def change_current_database(self, database_to_connect: str):
        self.__init__(database_to_connect)


v = ValorantDB("auth_app_dev")
print(v.get_all_databases())
print(v.get_all_tables())
v.change_current_database("phoenix_bank_dev")
print(v.get_all_tables())
# # Preparing query to create a database
# sql = '''CREATE database valorant'''
