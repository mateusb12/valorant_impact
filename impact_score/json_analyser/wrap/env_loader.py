import os
from pathlib import Path
from typing import Optional

from dotenv import dotenv_values

from impact_score.path_reference.folder_ref import wrapper_reference


class TokenLoadErrorException(Exception):
    """Error when loading tokens from a file."""
    pass


def __get_token_reference() -> Path:
    return Path(wrapper_reference(), ".env")


def __load_env_file() -> dict[str, Optional[str]]:
    file = __get_token_reference()
    file_content = dotenv_values(file)
    if len(file_content) != 0:
        return file_content
    else:
        raise TokenLoadErrorException(f"Error: could not find .env file in {__get_token_reference()}")


def load_environment_tokens() -> None:
    env_config = __load_env_file()
    for tag, token in env_config.items():
        os.environ[tag] = token


def __main():
    load_environment_tokens()


if __name__ == "__main__":
    __main()
