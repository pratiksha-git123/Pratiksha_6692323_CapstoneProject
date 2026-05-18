"""
ResultPage — handles the flight results page: wait for results, dismiss popups,
apply filters (Non-Stop), sort by price, extract flight data, and click Book.
"""

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.basepage import BasePage
from utils.logger import get_logger

log = get_logger()


class ResultPage(BasePage):
    """Page Object for the ixigo flight search results page."""

    # ── Locators ────────────────────────────────────────────────────
    BOOK_BTN_XPATH = "//button[normalize-space()='Book']"
    NONSTOP_CB_XPATH = (
        "(//p[normalize-space()='Stops']"
        "/following-sibling::div//input[@type='checkbox'])[1]"
    )
    PRICE_RADIO_XPATH = "(//input[@type='radio' and @name='oneWayType'])[1]"
    FLIGHT_COUNT_XPATH = (
        "//*[contains(text(),'Flights Available') or "
        "contains(text(),'flights available')]"
    )

    # ── Wait / navigation ───────────────────────────────────────────
    def wait_for_results(self, timeout: int = 30):
        log.info("Waiting for flight results...")
        self.wait_for_url_contains("search/result/flight", timeout=timeout)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.XPATH, self.BOOK_BTN_XPATH))
        )
        # Wait until at least one Book button is clickable (page fully interactive)
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, self.BOOK_BTN_XPATH))
        )
        log.info("Results loaded.")

    # ── Popup dismissal on results page ─────────────────────────────
    def dismiss_results_popup(self):
        log.info("Dismissing results-page popup...")
        try:
            width = self.driver.execute_script("return window.innerWidth;")
            height = self.driver.execute_script("return window.innerHeight;")
            body = self.driver.find_element(By.TAG_NAME, "body")
            ActionChains(self.driver).move_to_element_with_offset(
                body, 50 - width // 2, 50 - height // 2
            ).click().perform()
        except Exception:
            self.press_escape()

    # ── Filters ─────────────────────────────────────────────────────
    def apply_nonstop_filter(self):
        log.info("Applying Non-Stop filter...")
        xpaths = [
            self.NONSTOP_CB_XPATH,
            "(//p[text()='Stops']/following-sibling::*//input[@type='checkbox'])[1]",
        ]
        for xpath in xpaths:
            try:
                cb = self.find(By.XPATH, xpath, timeout=8)
                self.js_click(cb)
                log.info("Non-Stop filter applied.")
                # Wait for results to re-render after filter
                WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, self.BOOK_BTN_XPATH))
                )
                return
            except TimeoutException:
                continue

        # Fallback: click the text label
        try:
            label = self.driver.find_element(
                By.XPATH,
                "(//p[text()='Stops']/following::p[text()='Non-Stop'])[1]/ancestor::div[1]",
            )
            self.safe_click(label)
            log.info("Non-Stop filter applied (label click).")
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, self.BOOK_BTN_XPATH))
            )
        except Exception:
            log.warning("Non-Stop filter not found.")

    # ── Sort ────────────────────────────────────────────────────────
    def sort_by_price(self):
        log.info("Sorting by Price (Low to High)...")
        xpaths = [
            self.PRICE_RADIO_XPATH,
            "//p[normalize-space()='Price']/ancestor::div[1]//input[@type='radio']",
        ]
        for xpath in xpaths:
            try:
                radio = self.find(By.XPATH, xpath, timeout=8)
                self.js_click(radio)
                log.info("Sorted by Price.")
                # Wait for results to re-render after sort
                WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, self.BOOK_BTN_XPATH))
                )
                return
            except TimeoutException:
                continue

        try:
            label = self.driver.find_element(
                By.XPATH,
                "//p[normalize-space()='Price']/ancestor::div[contains(@class,'flex')][1]",
            )
            self.safe_click(label)
            log.info("Sorted by Price (label click).")
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, self.BOOK_BTN_XPATH))
            )
        except Exception:
            log.warning("Price sort not found.")

    # ── Extract results ─────────────────────────────────────────────
    def get_flight_count_text(self) -> str:
        for el in self.find_all(By.XPATH, self.FLIGHT_COUNT_XPATH):
            if el.is_displayed():
                return el.text.strip()
        return ""

    def get_flights(self, max_results: int = 5) -> list[dict]:
        """Return a list of dicts with basic flight info."""
        flights = []
        book_btns = self.find_all(By.XPATH, self.BOOK_BTN_XPATH)
        seen = set()
        for btn in book_btns:
            if len(flights) >= max_results:
                break
            try:
                card = btn.find_element(By.XPATH, "./ancestor::div[.//h6][1]")
                text = card.text.strip()
                sig = text[:100]
                if sig in seen or not text:
                    continue
                seen.add(sig)
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                flights.append({"raw_lines": lines, "card_text": text})
            except Exception:
                pass
        return flights

    def print_results(self):
        log.info("=" * 60)
        count = self.get_flight_count_text()
        if count:
            log.info(count)
        for i, flight in enumerate(self.get_flights(), 1):
            log.info(f"\n--- Flight {i} ---")
            for line in flight["raw_lines"][:8]:
                log.info(f"  {line}")
        log.info("=" * 60)

    # ── Book a flight ───────────────────────────────────────────────
    def click_book(self, index: int = 0):
        """Click the Book button for the nth visible flight (0-based)."""
        log.info(f"Clicking Book on flight #{index + 1}...")
        book_btns = self.find_all(By.XPATH, self.BOOK_BTN_XPATH)
        visible = [b for b in book_btns if b.is_displayed()]
        if index < len(visible):
            self.safe_click(visible[index])
            log.info("Book clicked — proceeding to traveller details.")
            # Wait for navigation to booking page
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.url_contains("/flight/booking/")
                )
            except TimeoutException:
                # May have opened a new tab — switch to it
                if len(self.driver.window_handles) > 1:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    WebDriverWait(self.driver, 10).until(
                        EC.url_contains("/flight/booking/")
                    )
                else:
                    # Wait for URL to change from results page
                    WebDriverWait(self.driver, 10).until_not(
                        EC.url_contains("search/result")
                    )
        else:
            log.error(f"Only {len(visible)} Book buttons visible; index {index} out of range.")
