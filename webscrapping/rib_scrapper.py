import ast
import json
from pathlib import Path

from impact_score.path_reference.folder_ref import geckodriver_reference, json_folder_reference
from selenium.webdriver.firefox.service import Service
from selenium import webdriver


class MissingGeckodriverException(Exception):
    pass


def __existing_geckodriver() -> bool:
    ref = geckodriver_reference()
    return ref.exists()


def check_geckodriver() -> None:
    existing = __existing_geckodriver()
    if not existing:
        raise MissingGeckodriverException(f"Error: could not find geckodriver.exe file at [{geckodriver_reference()}]")


class RIBScrapper:
    def __init__(self):
        check_geckodriver()
        s = Service(str(geckodriver_reference()))
        self.driver = webdriver.Firefox(service=s)
        self.match_id, self.series_id = None, None

    def set_config(self, match_id: int, series_id: int):
        self.match_id = match_id
        self.series_id = series_id

    def __load_website(self) -> None:
        url = f"https://rib.gg/series/{self.series_id}?match={self.match_id}"
        self.driver.get(url)

    def __scrap_data(self) -> dict:
        source_code = self.driver.page_source
        js_code: str = self.__code_trimmer(source_code)
        return json.loads(js_code)

    def json_pipeline(self):
        self.__load_website()
        data = self.__scrap_data()
        filename = f"{self.match_id}.json"
        output_ref = Path(json_folder_reference(), filename)
        with open(output_ref, "w") as f:
            json.dump(data, f)

    @staticmethod
    def __code_trimmer(code: str) -> str:
        first_split = code.split("window.__INITIAL_STATE__")
        first_trim = first_split[1][21:]
        second_split = first_trim.split("</script><script>!function(e)")
        second_trim = second_split[0]
        third_split = second_trim.split("?{}:")
        return third_split[0]

    def __existing_driver(self) -> bool:
        return self.driver.session_id is not None

    def __close_driver(self) -> None:
        if self.__existing_driver():
            self.driver.close()

    def __del__(self) -> None:
        self.__close_driver()


def get_json(match_id: int, series_id: int):
    """Webscrapping pipeline.
    Set match_id and series_id in order to download the match"""
    rbs = RIBScrapper()
    rbs.set_config(match_id=match_id, series_id=series_id)
    rbs.json_pipeline()


def __main():
    rbs = RIBScrapper()
    rbs.set_config(match_id=67207, series_id=30140)
    rbs.json_pipeline()


if __name__ == "__main__":
    __main()
