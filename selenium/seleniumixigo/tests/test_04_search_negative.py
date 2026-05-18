"""
test_04_search_negative.py — Realistic invalid search scenarios.

These are ordinary mistakes a traveler can make while using the form:
  1. Choosing the same city for From and To
  2. Trying to search before selecting a destination
  3. Typing a destination but never choosing a valid dropdown option
"""
from datetime import date

import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.flightsearchpage import FlightSearchPage
from utils.logger import get_logger

log = get_logger()


@pytest.mark.usefixtures("driver")
class TestSearchNegative:
    """Validate realistic user-input failures on the flight search form."""

    def _assert_search_did_not_reach_results(self, driver, timeout: int = 8):
        """Search should remain on the form instead of opening the results page."""
        with pytest.raises(Exception):
            WebDriverWait(driver, timeout).until(
                EC.url_contains("search/result")
            )

    @pytest.mark.negative
    @pytest.mark.order(1)
    def test_same_origin_and_destination_is_blocked(self, driver):
        """A traveler should not be able to search BOM → BOM."""
        page = FlightSearchPage(driver)
        page.open_search_page()
        page.wait_for_search_form()
        page.select_from_city("Mumbai", "BOM")
        page.select_to_city("Mumbai", "BOM")
        page.select_departure_date(date(2026, 6, 10))
        page.click_search()

        self._assert_search_did_not_reach_results(driver)
        log.info("PASS: Same-origin search was blocked.")

    @pytest.mark.negative
    @pytest.mark.order(2)
    def test_search_without_destination_is_blocked(self, driver):
        """A traveler who skips the To field should not reach results."""
        page = FlightSearchPage(driver)
        page.open_search_page()
        page.wait_for_search_form()
        page.select_from_city("Mumbai", "BOM")
        page.select_departure_date(date(2026, 6, 10))
        page.click_search()

        self._assert_search_did_not_reach_results(driver)
        log.info("PASS: Search without destination was blocked.")

    @pytest.mark.negative
    @pytest.mark.order(3)
    def test_unselected_typed_destination_is_not_accepted(self, driver):
        """Typing text alone should not count as selecting a valid destination."""
        page = FlightSearchPage(driver)
        page.open_search_page()
        page.wait_for_search_form()
        page.select_from_city("Mumbai", "BOM")

        to_label = driver.find_element(By.XPATH, "//span[text()='To']")
        page.safe_click(to_label)
        destination_input = driver.switch_to.active_element
        destination_input.send_keys("Delhi")

        page.select_departure_date(date(2026, 6, 10))
        page.click_search()

        self._assert_search_did_not_reach_results(driver)
        log.info("PASS: Unselected typed destination was not accepted.")
