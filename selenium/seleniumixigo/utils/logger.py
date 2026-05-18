"""Logging utility — writes to console and logs/automation.log."""
import logging
import os

_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, "automation.log")

_logger = logging.getLogger("ixigo")
_logger.setLevel(logging.DEBUG)

# File handler
_fh = logging.FileHandler(_LOG_FILE, mode="a", encoding="utf-8")
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

# Console handler
_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)
_ch.setFormatter(logging.Formatter("[ixigo] %(message)s"))

_logger.addHandler(_fh)
_logger.addHandler(_ch)


def get_logger() -> logging.Logger:
    return _logger
