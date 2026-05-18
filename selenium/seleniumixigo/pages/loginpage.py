"""
LoginPage — handles ixigo login dialog (phone + OTP).
"""
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.basepage import BasePage
from utils.logger import get_logger

log = get_logger()


class LoginPage(BasePage):
    """Handles the Log in / Sign up flow on ixigo."""

    # ── Locators ────────────────────────────────────────────────────
    LOGIN_BTN_XPATH = "//button[normalize-space()='Log in/Sign up']"
    MOBILE_INPUT_XPATH = "//input[@placeholder='Enter Mobile Number']"
    CONTINUE_BTN_XPATH = "//button[normalize-space()='Continue']"

    def click_login(self):
        """Click the 'Log in/Sign up' button in the navbar."""
        log.info("Clicking Log in/Sign up...")
        try:
            btn = self.find_clickable(By.XPATH, self.LOGIN_BTN_XPATH)
            self.safe_click(btn)
            log.info("Login dialog opened.")
        except TimeoutException:
            log.warning("Login button not found — skipping login.")

    def wait_for_login_complete(self, timeout: int = 300, poll: int = 2):
        """Poll until the 'Log in/Sign up' button disappears (user logged in)."""
        log.info(f"Waiting up to {timeout}s for manual OTP entry...")

        def _login_done(d):
            btns = d.find_elements(By.XPATH, self.LOGIN_BTN_XPATH)
            for btn in btns:
                if btn.is_displayed():
                    return False
            return True

        try:
            WebDriverWait(self.driver, timeout, poll_frequency=poll).until(_login_done)
            log.info("Login completed!")
            return True
        except TimeoutException:
            log.warning("Login timed out — continuing anyway.")
            return False

    def enter_mobile_and_continue(self, mobile: str):
        """Fill mobile number and click Continue to trigger OTP."""
        field = self.find_clickable(By.XPATH, self.MOBILE_INPUT_XPATH, timeout=10)
        self.clear_and_type(field, mobile)
        continue_btn = self.find_clickable(By.XPATH, self.CONTINUE_BTN_XPATH, timeout=10)
        self.safe_click(continue_btn)
        log.info("Mobile number submitted; waiting for OTP.")

    def login(self, mobile: str, timeout: int = 300):
        """Full login flow: open dialog, submit mobile, then wait for OTP only."""
        self.click_login()
        self.enter_mobile_and_continue(mobile)
        return self.wait_for_login_complete(timeout=timeout)
