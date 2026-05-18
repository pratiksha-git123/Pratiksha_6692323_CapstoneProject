"""Screenshot utility — saves screenshots to logs/ on failure."""
import os
from datetime import datetime

_SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(_SCREENSHOT_DIR, exist_ok=True)


def take_screenshot(driver, name: str = "screenshot") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = os.path.join(_SCREENSHOT_DIR, filename)
    driver.save_screenshot(filepath)
    return filepath
