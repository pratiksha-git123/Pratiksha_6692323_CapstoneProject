"""Read config.properties using configparser."""
import configparser
import os

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.properties")
_config = configparser.ConfigParser()
_config.read(_CONFIG_PATH)


def get(section: str, key: str, fallback: str = "") -> str:
    return _config.get(section, key, fallback=fallback)


def get_int(section: str, key: str, fallback: int = 0) -> int:
    return _config.getint(section, key, fallback=fallback)


def get_bool(section: str, key: str, fallback: bool = False) -> bool:
    return _config.getboolean(section, key, fallback=fallback)
