from typing import List, Tuple
import os

from termcolor import colored

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
        sample = self.files
        size = len(sample)
        for index, file in enumerate(sample):
            vc.setup_json(f'{file}')
            vc.extract_full_json()
            ratio = round((index + 1) / size, 3)
            print(colored(f'{file}.json was inserted!    [{index}/{size} ({ratio}%)]', 'green'))


vp = ValorantPopulator()
vp.populate()
