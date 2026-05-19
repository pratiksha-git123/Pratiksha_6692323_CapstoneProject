"""
test_08_e2e_full_booking.py — Complete end-to-end: login → search → book → payment.

Single-session ordered flow covering every step in one file.

Tests:
  1. Open site
  2. Login
  3. Search flights
  4. Apply filter + sort
  5. Click Book
  6. Booking page loaded
  7. Decline cancellation
  8. Fill traveller details
  9. Continue & confirm
  10. Add-ons page
  11. Skip to payment
  12. Payment page reached
"""
from datetime import date

import allure
import pytest

from pages.flightsearchpage import FlightSearchPage
from pages.loginpage import LoginPage
from pages.resultpage import ResultPage
from pages.bookingpage import BookingPage
from pages.addonspage import AddonsPage
from pages.paymentpage import PaymentPage
from utils.config_reader import get_int
from utils.csv_reader import read_csv

from utils.route_reader import get_random_route

from utils.logger import LogGen
from utils.screenshot_util import take_screenshot

logger =LogGen.loggen()



@pytest.mark.usefixtures("driver")
class TestE2EFullBooking:
    """Full end-to-end booking flow in a single browser session."""

    @pytest.mark.order(1)
    def test_01_open_site(self, driver):
        """Open ixigo flights page."""
        page = FlightSearchPage(driver)
        page.open_search_page()
        assert "ixigo" in driver.title.lower()
        logger.info("PASS: Site opened.")

    @pytest.mark.order(2)
    def test_02_login(self, driver):
        """Submit phone from CSV, then wait for manual OTP entry."""
        login_mobile = read_csv("login_data.csv")[0]["mobile"]
        LoginPage(driver).login(
            mobile=login_mobile,
            timeout=get_int("login", "wait_timeout", fallback=300)
        )
        logger.info("PASS: Logged in.")

    @pytest.mark.search
    @pytest.mark.order(3)
    def test_03_search_flights(self, driver):
        """Search one randomly chosen route from CSV."""
        route = get_random_route()
        page = FlightSearchPage(driver)
        page.open_search_page()
        page.wait_for_search_form()
        page.select_from_city(route["from_city"], route["from_code"])
        page.select_to_city(route["to_city"], route["to_code"])
        page.select_departure_date(date.fromisoformat(route["travel_date"]))
        page.click_search()
        take_screenshot.capture_screenshot(driver, "search_page")
        results = ResultPage(driver)
        results.wait_for_results(timeout=60)
        results.dismiss_results_popup()
        flight_count = results.get_available_flight_count()
        assert flight_count > 0, "No flights found"
        logger.info(f"PASS: {flight_count} flights available.")

    @pytest.mark.search
    @pytest.mark.order(4)
    def test_04_apply_nonstop_filter(self, driver):
        """Apply Non-Stop filter."""
        results = ResultPage(driver)
        results.apply_nonstop_filter()
        flight_count = results.get_available_flight_count()
        take_screenshot.capture_screenshot(driver, "filter")
        assert flight_count > 0, "No flights after Non-Stop filter"
        logger.info(f"PASS: Non-Stop filter → {flight_count} flights.")

    @pytest.mark.search
    @pytest.mark.order(5)
    def test_05_sort_by_price(self, driver):
        """Sort results by price (cheapest first)."""
        results = ResultPage(driver)
        results.sort_by_price()
        results.dismiss_results_popup()
        flight_count = results.get_available_flight_count()
        take_screenshot.capture_screenshot(driver, "SortBYPrice")
        assert flight_count > 0, "No flights after sort"
        logger.info(f"PASS: Sorted by price → {flight_count} flights.")

    @pytest.mark.search
    @pytest.mark.order(6)
    def test_06_print_results(self, driver):
        """Print top flight results to logger."""
        results = ResultPage(driver)
        results.print_results()
        flight_count = results.get_available_flight_count()
        assert flight_count >= 1, "No flights to print"
        logger.info(f"PASS: {flight_count} results printed.")

    @pytest.mark.booking
    @pytest.mark.order(7)
    def test_07_click_book(self, driver):
        """Book the cheapest flight."""
        ResultPage(driver).click_book(index=0)
        take_screenshot.capture_screenshot(driver, "Book Flight")
        logger.info("PASS: Book clicked.")

    @pytest.mark.booking
    @pytest.mark.order(8)
    def test_08_booking_page(self, driver):
        """Booking page loads."""
        BookingPage(driver).wait_for_booking_page(timeout=30)
        assert "/flight/booking/" in driver.current_url
        logger.info("PASS: Booking page loaded.")

    @pytest.mark.booking
    @pytest.mark.order(9)
    def test_09_decline_cancellation(self, driver):
        """Decline free cancellation."""
        BookingPage(driver).decline_free_cancellation()
        take_screenshot.capture_screenshot(driver, "Free Cancellation")
        logger.info("PASS: Cancellation declined.")

    @pytest.mark.booking
    @pytest.mark.order(10)
    def test_10_fill_traveller(self, driver):
        """Fill traveller form with CSV data."""
        booking = BookingPage(driver)
        traveller = read_csv("traveller_data.csv")[0]
        filled = booking.fill_traveller_form(traveller)
        assert filled, "Form not filled"
        take_screenshot.capture_screenshot(driver, "Traveller detail")
        logger.info(f"PASS: {traveller['first_name']} {traveller['last_name']}.")

    @pytest.mark.booking
    @pytest.mark.order(11)
    def test_11_continue_and_confirm(self, driver):
        """Continue → Confirm → Dismiss upsell."""
        booking = BookingPage(driver)
        booking.click_continue()
        booking.confirm_details()
        booking.dismiss_upsell_popup()
        logger.info("PASS: Confirmed.")

    @pytest.mark.payment
    @pytest.mark.order(12)
    def test_12_addons_page(self, driver):
        """Add-ons page loads."""
        AddonsPage(driver).wait_for_addons_page(timeout=30)
        logger.info("PASS: Add-ons page.")

    @pytest.mark.payment
    @pytest.mark.order(13)

    def test_13_select_seat(self, driver):
        """Select a seat or note none available."""
        addons = AddonsPage(driver)
        selected = addons.select_random_seat()
        if selected:
            logger.info("PASS: Seat selected.")
        else:
            logger.info("PASS: No seat layout — will skip.")

    @pytest.mark.payment
    @pytest.mark.order(14)

    def test_14_skip_to_payment(self, driver):
        """Skip to payment."""
        AddonsPage(driver).skip_to_payment()
        logger.info("PASS: Skipped to payment.")

    @pytest.mark.payment
    @pytest.mark.order(15)

    def test_15_payment_page(self, driver):
        """Payment page reached — full flow complete."""
        reached = PaymentPage(driver).wait_for_payment_page(timeout=30)
        assert reached, "Payment page not reached"
        take_screenshot.capture_screenshot(driver, "PaymentPage")
        logger.info("PASS: Payment page — E2E COMPLETE!")
