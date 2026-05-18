"""
test_02_search_flights.py — Verify flight search with valid routes.

Tests:
  1. Search BOM → BLR returns results
  2. Results URL contains airport codes
  3. Flight count text is displayed
  4. Multiple Book buttons are visible
  5. Search DEL → BOM works (second route)
  6. Reverse route BOM → DEL also works
"""
from datetime import date

import pytest

from selenium.webdriver.common.by import By

from pages.flightsearchpage import FlightSearchPage
from pages.resultpage import ResultPage
from utils.logger import get_logger
from utils.route_reader import get_random_route

log = get_logger()



@pytest.mark.usefixtures("driver")
class TestSearchFlights:
    """Validate that flight searches return expected results."""

    @pytest.mark.search
    @pytest.mark.order(1)
    def test_search_random_csv_route(self, driver):
        """Search one randomly chosen CSV route and return flights."""
        route = get_random_route()
        self.__class__.route = route
        page = FlightSearchPage(driver)
        page.open_search_page()
        page.select_from_city(route["from_city"], route["from_code"])
        page.select_to_city(route["to_city"], route["to_code"])
        page.select_departure_date(date.fromisoformat(route["travel_date"]))
        page.click_search()
        results = ResultPage(driver)
        results.wait_for_results(timeout=60)
        results.dismiss_results_popup()
        flights = results.get_flights()
        assert len(flights) > 0, (
            f"No flights found for {route['from_code']} ? {route['to_code']}"
        )
        log.info(
            f"PASS: {len(flights)} flights for "
            f"{route['from_code']} ? {route['to_code']}."
        )

    @pytest.mark.search
    @pytest.mark.order(2)
    def test_results_url_has_route_codes(self, driver):
        """URL should contain origin and destination airport codes."""
        route = self.__class__.route
        url = driver.current_url.lower()
        assert route["from_code"].lower() in url and route["to_code"].lower() in url, \
            f"URL missing route codes for {route}: {url}"
        log.info(f"PASS: URL contains {route['from_code']} and {route['to_code']}.")

    @pytest.mark.search
    @pytest.mark.order(3)
    def test_flight_count_displayed(self, driver):
        """Results page shows flight count or flights are visible."""
        results = ResultPage(driver)
        results.wait_for_results(timeout=15)
        count_text = results.get_flight_count_text()
        flights = results.get_flights()
        assert len(flights) > 0 or count_text != "", \
            "Neither flight count text nor flights are visible"
        log.info(f"PASS: Count: '{count_text}', flights: {len(flights)}")

    @pytest.mark.search
    @pytest.mark.order(4)
    def test_multiple_book_buttons_visible(self, driver):
        """Multiple Book buttons should be present."""
        results = ResultPage(driver)
        book_btns = results.find_all(By.XPATH, results.BOOK_BTN_XPATH)
        visible = [b for b in book_btns if b.is_displayed()]
        assert len(visible) >= 2, \
            f"Expected ≥2 Book buttons, found {len(visible)}"
        log.info(f"PASS: {len(visible)} Book buttons visible.")

    @pytest.mark.search
    @pytest.mark.order(5)
    def test_search_del_to_bom(self, isolated_driver):
        """Search Delhi → Mumbai returns flights."""
        driver = isolated_driver
        page = FlightSearchPage(driver)
        page.open_search_page()
        page.wait_for_search_form()
        page.select_from_city("Delhi", "DEL")
        page.select_to_city("Mumbai", "BOM")
        page.select_departure_date(date(2026, 6, 15))
        page.click_search()
        results = ResultPage(driver)
        results.wait_for_results(timeout=60)
        results.dismiss_results_popup()
        flights = results.get_flights()
        url = driver.current_url.lower()
        assert "del" in url and "bom" in url, \
            f"Search did not switch to DEL → BOM: {url}"
        assert len(flights) > 0, "No flights for DEL → BOM"
        log.info(f"PASS: {len(flights)} flights for DEL → BOM.")

    @pytest.mark.search
    @pytest.mark.order(6)
    def test_reverse_route_bom_to_del(self, isolated_driver):
        """Reverse route Mumbai → Delhi also works."""
        driver = isolated_driver
        page = FlightSearchPage(driver)
        page.open_search_page()
        page.wait_for_search_form()
        page.select_from_city("Mumbai", "BOM")
        page.select_to_city("Delhi", "DEL")
        page.select_departure_date(date(2026, 6, 20))
        page.click_search()
        results = ResultPage(driver)
        results.wait_for_results(timeout=30)
        results.dismiss_results_popup()
        flights = results.get_flights()
        url = driver.current_url.lower()
        assert "bom" in url and "del" in url, \
            f"Search did not switch to BOM → DEL: {url}"
        assert len(flights) > 0, "Reverse route BOM → DEL no flights"
        log.info(f"PASS: Reverse route {len(flights)} flights.")
