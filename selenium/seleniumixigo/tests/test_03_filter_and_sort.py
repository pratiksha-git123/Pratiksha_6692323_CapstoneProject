"""
test_03_filter_and_sort.py — Verify filters and sorting on results page.

Tests:
  1. Non-Stop filter shows results
  2. Price sort orders flights cheapest first
  3. Results remain after applying both filter + sort
  4. Print top results to log
"""
import re
from datetime import date

import pytest

from pages.flightsearchpage import FlightSearchPage
from pages.resultpage import ResultPage
from utils.logger import get_logger
from utils.route_reader import get_random_route

log = get_logger()


@pytest.mark.usefixtures("driver")
class TestFilterAndSort:
    """Validate filter and sort on the flight results page."""

    @pytest.mark.search
    @pytest.mark.order(1)
    def test_setup_search(self, driver):
        """Open site, search BOM → BLR to get results."""
        page = FlightSearchPage(driver)
        page.open_search_page()
        page.select_from_city("Mumbai", "BOM")
        page.select_to_city("Bengaluru", "BLR")
        page.select_departure_date(date(2026, 6, 10))
        page.click_search()
        results = ResultPage(driver)
        results.wait_for_results(timeout=60)
        results.dismiss_results_popup()
        flights = results.get_flights()
        assert len(flights) > 0, "No results to test filters on"
        log.info(f"PASS: Setup — {len(flights)} flights loaded.")

    @pytest.mark.search
    @pytest.mark.order(2)
    def test_nonstop_filter_shows_results(self, driver):
        """Non-Stop filter still returns flights."""
        results = ResultPage(driver)
        results.apply_nonstop_filter()
        flights = results.get_flights()
        assert len(flights) > 0, "Non-Stop filter returned zero flights"
        log.info(f"PASS: Non-Stop → {len(flights)} flights.")

    @pytest.mark.search
    @pytest.mark.order(3)
    def test_sort_by_price_cheapest_first(self, driver):
        """After price sort, first flight is cheapest."""
        results = ResultPage(driver)
        results.sort_by_price()
        results.dismiss_results_popup()
        flights = results.get_flights(max_results=3)
        assert len(flights) >= 2, "Need ≥2 flights to verify sort"
        prices = []
        for f in flights:
            match = re.search(r'₹\s*([\d,]+)', f["card_text"])
            if match:
                prices.append(int(match.group(1).replace(",", "")))
        if len(prices) >= 2:
            assert prices[0] <= prices[1], \
                f"Not sorted: ₹{prices[0]} > ₹{prices[1]}"
        log.info(f"PASS: Price sort — {prices}")

    @pytest.mark.search
    @pytest.mark.order(4)
    def test_results_after_filter_and_sort(self, driver):
        """Results should still exist after both filter + sort."""
        results = ResultPage(driver)
        flights = results.get_flights()
        assert len(flights) > 0, "No flights after filter + sort"
        log.info(f"PASS: {len(flights)} flights after filter+sort.")

    @pytest.mark.search
    @pytest.mark.order(5)
    def test_print_results(self, driver):
        """Print top results to log for manual verification."""
        results = ResultPage(driver)
        results.print_results()
        flights = results.get_flights()
        assert len(flights) >= 1, "No flights to print"
        log.info(f"PASS: {len(flights)} results printed.")
