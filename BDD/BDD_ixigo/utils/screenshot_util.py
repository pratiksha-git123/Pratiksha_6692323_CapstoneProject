"""Screenshot utility - saves screenshots and attaches them to Allure when active."""
import os
from datetime import datetime

try:
    import allure
    from allure_commons.types import AttachmentType
except ImportError:
    allure = None
    AttachmentType = None

_SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(_SCREENSHOT_DIR, exist_ok=True)


def take_screenshot(driver, name: str = "screenshot") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = os.path.join(_SCREENSHOT_DIR, filename)
    driver.save_screenshot(filepath)

    if allure is not None:
        try:
            allure.attach.file(
                filepath,
                name=name,
                attachment_type=AttachmentType.PNG,
            )
        except Exception:
            pass

    return filepath
