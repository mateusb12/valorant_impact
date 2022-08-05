from impact_score.path_reference.folder_ref import geckodriver_reference
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


def __main():
    rbs = RIBScrapper()


if __name__ == "__main__":
    __main()
