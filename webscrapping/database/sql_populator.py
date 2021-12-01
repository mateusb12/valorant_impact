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

    @staticmethod
    def delete_broken_files():
        matches_to_delete = []
        with open("broken_matches.txt", "r") as file:
            broken_files = file.readlines()
            for line in broken_files:
                stripped_line = line.strip()
                line_list = stripped_line.split()[0]
                matches_to_delete.append(f"{line_list}.json")
            folder_name = os.getcwd().split("\\")[-1]
            if folder_name == "database":
                os.chdir("..\\matches\\json")
                print(matches_to_delete)
            for f in matches_to_delete:
                print(f"Deleting {f}")
                os.remove(f)

    def populate(self):
        vc = ValorantConsumer()
        # vc.db.rebuild_database()
        sample = self.files
        size = len(sample)
        for index, file in enumerate(sample):
            vc.setup_json(f'{file}')
            vc.extract_full_json()
            ratio = round(100 * index / size, 3)
            print(colored(f'{file}.json was inserted!    [{index}/{size} ({ratio}%)]', 'green'))
        vc.export_broken_matches()


if __name__ == "__main__":
    vp = ValorantPopulator()
    # vp.populate()
    vp.delete_broken_files()
