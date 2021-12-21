import datetime
import os
from pathlib import Path
from typing import List
from timeit import default_timer as timer

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

    @staticmethod
    def convert_seconds_to_minutes(seconds: float):
        minutes = seconds // 60
        seconds %= 60
        return f"{round(minutes)}m {round(seconds)}s"

    def download_missing_matches(self):
        size = len(self.missing_matches)
        start = timer()
        for index, match in enumerate(self.missing_matches, 1):
            loop = timer()
            elapsed = round(loop - start, 2)
            time_per_match = elapsed / index
            remaining_matches = size - index
            remaining_seconds = round(time_per_match * remaining_matches, 2)
            remaining_minutes = self.convert_seconds_to_minutes(remaining_seconds)
            progress = f"{index}/{size}"
            ratio = f"{round((index / size)*100, 2)}%"
            progress_str = f"Inserting match #{match} in PostgresSQL, {progress} so far." \
                           f" Ratio → [{ratio}]"
            print(colored(progress_str, "green"))
            current_time = datetime.datetime.now()
            seconds_added = datetime.timedelta(seconds=remaining_seconds)
            future_date_and_time = current_time + seconds_added
            estimated_time = f"Estimated time → " \
                             f" {future_date_and_time.hour}:{future_date_and_time.minute}:{future_date_and_time.second}"
            details_str = f"Elapsed → {elapsed}s | Time per match → {round(time_per_match, 2)}s" \
                          f" | Remaining time → {remaining_minutes} | {estimated_time}"
            print(colored(details_str, "magenta"))
            self.vc.setup_json(f'{match}.json')
            self.vc.extract_full_json()
        self.vc.export_broken_jsons()

    def set_missing_matches(self):
        self.db_matches = self.sql.query_existing_matches()
        self.json_matches = self.get_jsons_in_folder()
        self.missing_matches = [match for match in self.json_matches if match not in self.db_matches]

    def get_jsons_in_folder(self) -> List[int]:
        aux = self.get_json_folder_reference()
        os.chdir(aux)
        raw_list = os.listdir()
        if "json_to_sql.py.pclprof" in raw_list:
            raw_list.remove("json_to_sql.py.pclprof")
        return [int(item.split(".")[0]) for item in raw_list]

    @staticmethod
    def get_json_folder_reference():
        model = Path.cwd()
        webscrapping = model.parent
        return Path(webscrapping, "matches", "json")

    @staticmethod
    def get_broken_json_folder_reference():
        model = Path.cwd()
        webscrapping = model.parent
        return Path(webscrapping, "matches", "broken_json")

    def delete_broken_jsons(self):
        json_folder = self.get_json_folder_reference()
        broken_json_folder = self.get_broken_json_folder_reference()
        broken_json_list = []
        with open(Path(broken_json_folder, "broken_json.txt"), "r") as f:
            for line in f:
                filename = f"{line.strip()}.json"
                os.remove(Path(json_folder, filename))
                print(colored(f"Deleting #{filename}", "red"))
                broken_json_list.append(line.strip())


if __name__ == "__main__":
    dc = DatabaseConverter()
    # dc.vc.delete_database()
    dc.start_missing_matches_pipeline()
    # dc.start_missing_matches_pipeline()
