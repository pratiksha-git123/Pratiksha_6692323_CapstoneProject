"""
ResultPage — handles the flight results page: wait for results, dismiss popups,
apply filters (Non-Stop), sort by price, extract flight data, and click Book.
"""

import re

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.basepage import BasePage
from utils.logger import LogGen

logger =LogGen.loggen()

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
        "//*[contains("
        "translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
        "'flights available'"
        ")]"
    )

    # ── Wait / navigation ───────────────────────────────────────────
    def wait_for_results(self, timeout: int = 30):
        logger.info("Waiting for flight results...")
        self.wait_for_url_contains("search/result/flight", timeout=timeout)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.XPATH, self.BOOK_BTN_XPATH))
        )
        # Wait until at least one Book button is clickable (page fully interactive)
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, self.BOOK_BTN_XPATH))
        )
        logger.info("Results loaded.")

    # ── Popup dismissal on results page ─────────────────────────────
    def dismiss_results_popup(self):
        logger.info("Dismissing results-page popup...")
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
        logger.info("Applying Non-Stop filter...")
        xpaths = [
            self.NONSTOP_CB_XPATH,
            "(//p[text()='Stops']/following-sibling::*//input[@type='checkbox'])[1]",
        ]
        for xpath in xpaths:
            try:
                cb = self.find(By.XPATH, xpath, timeout=8)
                self.js_click(cb)
                logger.info("Non-Stop filter applied.")
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
            logger.info("Non-Stop filter applied (label click).")
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, self.BOOK_BTN_XPATH))
            )
        except Exception:
            logger.warning("Non-Stop filter not found.")

    # ── Sort ────────────────────────────────────────────────────────
    def sort_by_price(self):
        logger.info("Sorting by Price (Low to High)...")
        xpaths = [
            self.PRICE_RADIO_XPATH,
            "//p[normalize-space()='Price']/ancestor::div[1]//input[@type='radio']",
        ]
        for xpath in xpaths:
            try:
                radio = self.find(By.XPATH, xpath, timeout=8)
                self.js_click(radio)
                logger.info("Sorted by Price.")
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
            logger.info("Sorted by Price (label click).")
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, self.BOOK_BTN_XPATH))
            )
        except Exception:
            logger.warning("Price sort not found.")

    # ── Extract results ─────────────────────────────────────────────
    def _parse_available_flight_count(self, text: str) -> int:
        match = re.search(r"(\d+)\s+flights?\s+available", text or "", re.IGNORECASE)
        if not match:
            return 0
        return int(match.group(1))

    def get_flight_count_text(self) -> str:
        visible_count_texts = []
        for el in self.find_all(By.XPATH, self.FLIGHT_COUNT_XPATH):
            try:
                text = el.text.strip()
                if el.is_displayed() and self._parse_available_flight_count(text) > 0:
                    visible_count_texts.append(text)
            except Exception:
                continue
        if visible_count_texts:
            return min(visible_count_texts, key=len)
        return ""

    def get_available_flight_count(self) -> int:
        """Return the visible 'Flights Available' count shown by ixigo."""
        count = self._parse_available_flight_count(self.driver.page_source)
        if count > 0:
            return count
        return self._parse_available_flight_count(self.get_flight_count_text())

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
        logger.info("=" * 60)
        count = self.get_flight_count_text()
        if count:
            logger.info(count)
        for i, flight in enumerate(self.get_flights(), 1):
            logger.info(f"\n--- Flight {i} ---")
            for line in flight["raw_lines"][:8]:
                logger.info(f"  {line}")
        logger.info("=" * 60)

    # ── Book a flight ───────────────────────────────────────────────
    def click_book(self, index: int = 0):
        """Click the Book button for the nth visible flight (0-based)."""
        logger.info(f"Clicking Book on flight #{index + 1}...")
        book_btns = self.find_all(By.XPATH, self.BOOK_BTN_XPATH)
        visible = [b for b in book_btns if b.is_displayed()]
        if index < len(visible):
            self.safe_click(visible[index])
            logger.info("Book clicked — proceeding to traveller details.")
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
            logger.error(f"Only {len(visible)} Book buttons visible; index {index} out of range.")
