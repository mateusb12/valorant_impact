import os
from pathlib import Path


class ValorantModel:
    def __init__(self):
        self.model = None
        print(os.getcwd())

    @staticmethod
    def get_json_folder_reference():
        model = Path.cwd()
        webscrapping = model.parent
        return Path(webscrapping, "matches", "json")


if __name__ == "__main__":
    vm = ValorantModel()
