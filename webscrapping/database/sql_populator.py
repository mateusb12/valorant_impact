from typing import List, Tuple
import os

from webscrapping.database.sql_json_consumer import ValorantConsumer


class ValorantPopulator:

    def __init__(self):
        current_folder = os.getcwd().split("\\")[-1]
        if current_folder == "database":
            os.chdir("..\\matches\\json")
        # Get all files in the current folder
        self.files = os.listdir()
        os.chdir("..\\..\\database")

    def populate(self):
        vc = ValorantConsumer()
        vc.db.rebuild_database()
        vc.setup_json(self.files[2])
        vc.extract_full_json()
        # for file in self.files[:5]:
        #     vc.setup_json(f'{file}')
        #     vc.extract_full_json()


vp = ValorantPopulator()
vp.populate()
