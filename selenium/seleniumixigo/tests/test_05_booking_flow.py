"""
test_05_booking_flow.py — Verify clicking Book navigates to booking page.

Tests:
  1. Click Book on first flight
  2. Booking page URL loads
  3. Traveller Details heading is present
  4. Decline free cancellation option works
"""
from datetime import date

import pytest

from selenium.webdriver.common.by import By

from pages.flightsearchpage import FlightSearchPage
from pages.resultpage import ResultPage
from pages.bookingpage import BookingPage
from utils.logger import get_logger
from utils.route_reader import get_random_route

log = get_logger()


@pytest.mark.usefixtures("driver")
class TestBookingFlow:
    """Validate clicking Book and reaching the booking page."""

    @pytest.mark.booking
    @pytest.mark.order(1)
    def test_setup_search(self, driver):
        """Search to get results for booking (no login needed)."""
        page = FlightSearchPage(driver)
        page.open_search_page()
        route = get_random_route()
        page.select_from_city(route["from_city"], route["from_code"])
        page.select_to_city(route["to_city"], route["to_code"])
        page.select_departure_date(date.fromisoformat(route["travel_date"]))
        page.click_search()
        results = ResultPage(driver)
        results.wait_for_results(timeout=60)
        results.dismiss_results_popup()
        results.apply_nonstop_filter()
        results.sort_by_price()
        results.dismiss_results_popup()
        flights = results.get_flights()
        assert len(flights) > 0, "No flights for booking test"
        log.info(f"PASS: Setup — {len(flights)} flights ready.")

    @pytest.mark.booking
    @pytest.mark.order(2)
    def test_click_book(self, driver):
        """Click Book on the cheapest flight."""
        results = ResultPage(driver)
        results.click_book(index=0)
        log.info("PASS: Book clicked.")

    @pytest.mark.booking
    @pytest.mark.order(3)
    def test_booking_page_url(self, driver):
        """URL should contain /flight/booking/."""
        booking = BookingPage(driver)
        booking.wait_for_booking_page(timeout=30)
        assert "/flight/booking/" in driver.current_url, \
            f"Not on booking page: {driver.current_url}"
        log.info("PASS: Booking page URL verified.")

    @pytest.mark.booking
    @pytest.mark.order(4)
    def test_traveller_heading_present(self, driver):
        """Traveller Details heading should be visible."""
        headings = driver.find_elements(
            By.XPATH, "//h5[normalize-space()='Traveller Details']"
        )
        assert any(h.is_displayed() for h in headings), \
            "Traveller Details heading not found"
        log.info("PASS: Traveller Details heading present.")

    @pytest.mark.booking
    @pytest.mark.order(5)
    def test_decline_free_cancellation(self, driver):
        """Decline free cancellation option should work."""
        booking = BookingPage(driver)
        booking.decline_free_cancellation()
        log.info("PASS: Free cancellation declined.")
