import os
import re
from datetime import datetime

import allure

from utils.logger import LogGen

logger = LogGen.loggen()


def _clean_screenshot_name(name):
    clean_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(name)).strip("_")
    return clean_name or "screenshot"


class take_screenshot:

    @staticmethod
    def capture_screenshot(driver, screenshot_name="screenshot", name=None):
        if name is not None:
            screenshot_name = name

        screenshot_dir = "reports/screenshots"

        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        clean_name = _clean_screenshot_name(screenshot_name)

        screenshot_path = (
            f"{screenshot_dir}/"
            f"{clean_name}_{timestamp}.png"
        )

        if not driver.save_screenshot(screenshot_path):
            raise RuntimeError(f"Screenshot was not saved: {screenshot_path}")

        logger.info(f"Screenshot saved at: {screenshot_path}")

        # attach screenshot to allure report
        allure.attach.file(
            screenshot_path,
            name=clean_name,
            attachment_type=allure.attachment_type.PNG
        )

        return screenshot_path
