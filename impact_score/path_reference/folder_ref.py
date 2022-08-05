# Get impact_score folder reference using Path
from pathlib import Path

ref = Path(__file__).parent.parent


def dynamic_reference(folder_name: str) -> Path:
    return Path(ref, folder_name)


def api_reference() -> Path:
    return Path(ref, 'api')


def datasets_reference() -> Path:
    return Path(ref, 'datasets')


def root_impact_reference() -> Path:
    return Path(ref, 'impact_score')


def root_project_folder_reference() -> Path:
    return ref


def impact_reference() -> Path:
    return Path(ref, 'impact')


def json_analyser_reference() -> Path:
    return Path(ref, 'json_analyser')


def valorant_model_reference() -> Path:
    return Path(ref, 'valorant_model')


def model_reference() -> Path:
    return Path(ref, 'model')


def wrapper_reference() -> Path:
    return Path(ref, 'json_analyser', 'wrap')


def geckodriver_reference() -> Path:
    return Path(Path(__file__).parent.parent.parent, 'webscrapping', 'geckodriver.exe')


def __main():
    print(geckodriver_reference())


if __name__ == "__main__":
    __main()
