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
