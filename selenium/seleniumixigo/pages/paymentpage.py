"""
PaymentPage — handles the Payment page (Step 4): verify we reached payment.
"""
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.basepage import BasePage
from utils.logger import get_logger

log = get_logger()


class PaymentPage(BasePage):
    """Page Object for the Payment step (Step 4)."""

    # ── Wait for payment page ────────────────────────────────────────
    def wait_for_payment_page(self, timeout: int = 30) -> bool:
        """Wait until the payment page loads.
        Returns True if payment page is detected."""
        log.info("Waiting for Payment page...")
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: "payment" in d.current_url.lower()
                or "Payments" in d.title
                or len(d.find_elements(
                    By.XPATH,
                    "//*[contains(text(),'Redirecting to payment')]"
                    " | //*[contains(text(),'Payment')]"
                )) > 0
            )
            log.info(f"Payment page reached. URL: {self.driver.current_url}")
            return True
        except TimeoutException:
            log.warning("Payment page did not load within timeout.")
            return False

    def is_on_payment_page(self) -> bool:
        """Check if currently on a payment page."""
        url = self.driver.current_url.lower()
        title = self.driver.title.lower()
        return "payment" in url or "payment" in title
