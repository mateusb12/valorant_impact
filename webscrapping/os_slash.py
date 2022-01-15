import platform

def get_slash_type() -> str:
    operational_system = platform.system()
    if operational_system == "Windows":
        return "\\"
    else:
        return "/"