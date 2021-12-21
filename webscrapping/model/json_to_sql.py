import os
from pathlib import Path
from typing import List

from termcolor import colored

from webscrapping.database.sql_json_consumer import ValorantConsumer
from webscrapping.database.sql_queries import ValorantQueries


class DatabaseConverter:
    def __init__(self):
        self.sql = ValorantQueries()
        self.vc = ValorantConsumer()
        self.db_matches, self.json_matches, self.missing_matches = [None] * 3

    def start_missing_matches_pipeline(self):
        self.set_missing_matches()
        self.download_missing_matches()

    def download_missing_matches(self):
        size = len(self.missing_matches)
        for index, match in enumerate(self.missing_matches, 1):
            progress = f"{index}/{size}"
            ratio = f"{round((index / size)*100, 2)}%"
            progress_str = f"Downloading match #{match}, {progress} so far. Ratio → [{ratio}]"
            print(colored(progress_str, "magenta"))
            self.vc.setup_json(f'{match}.json')
            self.vc.extract_full_json()

    def set_missing_matches(self):
        self.db_matches = self.sql.query_existing_matches()
        self.json_matches = self.get_jsons_in_folder()
        self.missing_matches = [match for match in self.json_matches if match not in self.db_matches]

    def get_jsons_in_folder(self) -> List[int]:
        aux = self.get_json_folder_reference()
        os.chdir(aux)
        raw_list = os.listdir()
        return [int(item.split(".")[0]) for item in raw_list]

    @staticmethod
    def get_json_folder_reference():
        model = Path.cwd()
        webscrapping = model.parent
        return Path(webscrapping, "matches", "json")


if __name__ == "__main__":
    dc = DatabaseConverter()
    dc.start_missing_matches_pipeline()
