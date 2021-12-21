from typing import List, Tuple
import os

from termcolor import colored

from webscrapping.database.sql_json_consumer import ValorantConsumer


class ValorantPopulator:

    def __init__(self, **kwargs):
        self.vc = ValorantConsumer()
        current_folder = os.getcwd().split("\\")[-1]
        if current_folder == "database":
            os.chdir("..\\matches\\json")
        # Get all files in the current folder
        self.files = os.listdir() if "match_list" not in kwargs else kwargs["match_list"]
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

    def rebuild(self):
        self.vc.db.rebuild_database()

    def populate(self, **kwargs):
        """
        Populate the database with the json files in the match folder
        :param kwargs: size: int, number of matches to be populated
                       rebuild: bool, rebuild the database?
                       start: int, start index of the matches to be populated
                       end: int, end index of the matches to be populated
        :return: populated postgres database
        """
        size = kwargs["size"] if "size" in kwargs else 0
        rebuild = kwargs["rebuild"] if "rebuild" in kwargs else False
        start = kwargs["start"] if "start" in kwargs else None
        end = kwargs["end"] if "end" in kwargs else None
        if rebuild:
            self.rebuild()
        sample = self.files
        if size:
            sample = self.files[:size]
        if start and end:
            sample = self.files[start:end]
        size = len(sample)
        for index, file in enumerate(sample):
            self.vc.setup_json(f'{file}')
            self.vc.extract_full_json()
            ratio = round(100 * index / size, 3)
            print(colored(f'{file} was inserted!    [{index}/{size} ({ratio}%)]', 'green'))
        self.vc.export_broken_matches()

    def populate_single_match(self, filename: str):
        self.vc.setup_json(f'{filename}')
        self.vc.extract_full_json()
        print(colored(f'{filename} was inserted!', 'green'))


if __name__ == "__main__":
    # 42038.json
    vp = ValorantPopulator()
    vp.populate_single_match("6177.json")
    # vp.populate(start=7000, end=8000, rebuild=False)
    # vp.delete_broken_files()
