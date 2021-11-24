from typing import List, Tuple

import psycopg2


class ValorantCore:
    def __init__(self, database_name: str = "postgres"):
        self.conn = psycopg2.connect(
            database=database_name, user='postgres', password='password', host='127.0.0.1', port='5432'
        )
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()


class ValorantPopulator(ValorantCore):

    def get_all_databases(self) -> List[Tuple[str]]:
        self.cursor.execute("SELECT datname FROM pg_database;")
        return self.cursor.fetchall()

    def change_current_database(self, database_to_connect: str):
        self.__init__(database_to_connect)

    def insert_map(self):
        self.cursor.execute("""
            INSERT INTO Cities(map_id, map_name) VALUES (4, 'Bind') 
            """)
        self.conn.commit()
        print("Map inserted")




vp = ValorantPopulator("valorant")
vp.insert_map()
