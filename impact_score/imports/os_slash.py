import platform


def get_slash_type() -> str:
    operational_system = platform.system()
    return "\\" if operational_system == "Windows" else "/"
