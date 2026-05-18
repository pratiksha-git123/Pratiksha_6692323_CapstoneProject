"""
AddonsPage — handles the Add-ons page (Step 3): seat selection and skip to payment.
"""
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.basepage import BasePage
from utils.logger import get_logger

log = get_logger()


class AddonsPage(BasePage):
    """Page Object for the Add-ons step (Seat, Meal, Insurance)."""

    # ── Locators ─────────────────────────────────────────────────────
    SKIP_TO_PAYMENT_XPATH = "//button[contains(text(),'Skip to Payment')]"
    SEAT_TAB_XPATH = "//div[text()='Seat']/ancestor::button[1] | //div[text()='Seat']/parent::*"
    MEAL_TAB_XPATH = "//div[text()='Meal']/ancestor::button[1] | //div[text()='Meal']/parent::*"
    SEAT_ICON_XPATH = "//img[contains(@class,'seat-icon') and contains(@alt,'seat-icon')]"
    SEAT_ICON_CLICKABLE_XPATH = "//img[contains(@class,'seat-icon')]"
    MEAL_SELECTION_BTN_XPATH = "//button[contains(text(),'Meal Selection')]"

    # ── Wait for add-ons page ────────────────────────────────────────
    def wait_for_addons_page(self, timeout: int = 15):
        """Wait until the seat map / add-ons page loads."""
        log.info("Waiting for Add-ons page to load...")

        # Check if already on payment (some providers skip addons)
        if "payment" in self.driver.current_url.lower():
            log.info("Skipped directly to payment — no addons page.")
            return

        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    self.SKIP_TO_PAYMENT_XPATH
                    + " | //button[normalize-space()='Continue']"
                    + " | " + self.SEAT_ICON_CLICKABLE_XPATH
                ))
            )
            log.info("Add-ons page loaded.")
        except TimeoutException:
            # Maybe we went to payment already
            if "payment" in self.driver.current_url.lower():
                log.info("Redirected to payment — no addons page.")
            else:
                log.warning("Add-ons page did not load — no action button found.")

    # ── Seat selection ───────────────────────────────────────────────
    def select_random_seat(self) -> bool:
        """Click the first available seat icon on the seat map.
        Returns True if a seat was selected, False otherwise."""
        log.info("Attempting to select a seat...")
        try:
            # Wait for seat icons to appear
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, self.SEAT_ICON_CLICKABLE_XPATH)
                )
            )

            seats = self.driver.find_elements(By.XPATH, self.SEAT_ICON_CLICKABLE_XPATH)
            log.info(f"Found {len(seats)} seat icons on the map.")

            # Try to click seats from the middle of the plane (better seats)
            start_index = min(len(seats) // 3, 60)
            for i in range(start_index, len(seats)):
                seat = seats[i]
                try:
                    if not seat.is_displayed():
                        continue
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", seat
                    )
                    seat.click()

                    # Check if seat was actually selected (look for seat info panel)
                    try:
                        WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//*[contains(text(),'Window') or "
                                 "contains(text(),'Middle') or "
                                 "contains(text(),'Aisle')]")
                            )
                        )
                        log.info(f"Seat selected (icon index {i}).")
                        return True
                    except TimeoutException:
                        continue
                except Exception:
                    continue

            log.warning("No available seat found after trying.")
            return False

        except TimeoutException:
            log.warning("Seat map did not load.")
            return False

    # ── Skip to Payment ──────────────────────────────────────────────
    def skip_to_payment(self):
        """Click the 'Skip to Payment' button — scroll into view first."""
        log.info("Clicking Skip to Payment...")

        # Check if already on payment page (some providers skip addons)
        if "payment" in self.driver.current_url.lower():
            log.info("Already on payment page — skipping.")
            return

        try:
            btn = self.find(By.XPATH, self.SKIP_TO_PAYMENT_XPATH, timeout=8)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", btn
            )
            try:
                btn.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", btn)
            # Wait for navigation to payment
            WebDriverWait(self.driver, 15).until(
                lambda d: "payment" in d.current_url.lower() or
                "payment" in d.title.lower()
            )
            log.info("Skipped to payment.")
        except TimeoutException:
            # Fallback: some providers show "Continue" instead
            alt_xpaths = [
                "//button[contains(text(),'Proceed to Payment')]",
                "//button[contains(text(),'Continue to Payment')]",
                "//button[normalize-space()='Continue']",
                "//button[contains(text(),'Payment')]",
            ]
            for xpath in alt_xpaths:
                try:
                    btn = self.find(By.XPATH, xpath, timeout=3)
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", btn
                    )
                    self.driver.execute_script("arguments[0].click();", btn)
                    WebDriverWait(self.driver, 15).until(
                        lambda d: "payment" in d.current_url.lower() or
                        "payment" in d.title.lower()
                    )
                    log.info("Proceeded to payment (alt button).")
                    return
                except TimeoutException:
                    continue

            # Final check: maybe we already reached payment during the waits
            if "payment" in self.driver.current_url.lower():
                log.info("Already on payment page.")
                return

            log.error("Skip to Payment button not found.")
            raise

    # ── Combined flow: try seat, then proceed ────────────────────────
    def select_seat_or_skip(self):
        """Try to select a seat. If unavailable, skip to payment."""
        seat_selected = self.select_random_seat()
        if seat_selected:
            log.info("Seat selected — now skipping to payment.")
            self.skip_to_payment()
        else:
            log.info("No seat selected — skipping to payment.")
            self.skip_to_payment()
