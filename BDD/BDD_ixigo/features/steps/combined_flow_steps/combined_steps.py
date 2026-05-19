"""Steps for the combined ixigo BDD flow."""
import re
import time
from datetime import date

from behave import given, then, when
from selenium.webdriver.common.by import By

from pages.bookingpage import BookingPage
from pages.flightsearchpage import FlightSearchPage
from pages.resultpage import ResultPage
from utils.config_reader import get_int
from utils.csv_reader import read_csv
from utils.screenshot_util import take_screenshot


def _csv_row(filename: str, row_number: int) -> dict:
    """Return a 1-based CSV row and fail clearly for invalid test data."""
    rows = read_csv(filename)
    assert rows, f"No data found in {filename}"
    assert 1 <= row_number <= len(rows), (
        f"Requested row {row_number} from {filename}, but only {len(rows)} row(s) exist"
    )
    return rows[row_number - 1]


def _capture(context, name: str):
    """Save a step screenshot without making screenshots part of the assertion."""
    try:
        path = take_screenshot(context.driver, name=name)
        context.last_screenshot = path
    except Exception as exc:
        context.last_screenshot_error = str(exc)


def _search_route(context, route: dict):
    search_page = FlightSearchPage(context.driver)
    context.route = route
    search_page.wait_for_search_form()
    search_page.select_from_city(route["from_city"], route["from_code"])
    search_page.select_to_city(route["to_city"], route["to_code"])
    search_page.select_departure_date(date.fromisoformat(route["travel_date"]))
    search_page.click_search()
    _capture(context, "search_page")


@given("the traveler opens the ixigo flights page")
def step_open_ixigo(context):
    search_page = FlightSearchPage(context.driver)
    search_page.open_search_page()


@then("the ixigo flights page should be loaded")
def step_ixigo_page_loaded(context):
    assert "ixigo" in context.driver.title.lower(), "ixigo page did not load"


@then("the main search controls should be visible")
def step_search_controls_visible(context):
    assert context.driver.find_elements(By.XPATH, FlightSearchPage.FROM_INPUT_XPATH), (
        "From field missing"
    )
    assert context.driver.find_elements(By.XPATH, FlightSearchPage.TO_INPUT_XPATH), (
        "To field missing"
    )
    assert context.driver.find_elements(By.XPATH, FlightSearchPage.SEARCH_BTN_XPATH), (
        "Search button missing"
    )


@when("the traveler searches using route data row {row_number:d} from CSV")
def step_search_route_from_csv(context, row_number):
    _search_route(context, _csv_row("flight_search.csv", row_number))


@when('the traveler searches from "{from_city}" "{from_code}" to "{to_city}" "{to_code}" on "{travel_date}"')
def step_search_explicit_route(context, from_city, from_code, to_city, to_code, travel_date):
    _search_route(
        context,
        {
            "from_city": from_city,
            "from_code": from_code,
            "to_city": to_city,
            "to_code": to_code,
            "travel_date": travel_date,
        },
    )
    time.sleep(3)


@when('the traveler searches with source "{from_city}" "{from_code}" and no destination')
def step_search_without_destination(context, from_city, from_code):
    search_page = FlightSearchPage(context.driver)
    search_page.wait_for_search_form()
    search_page.select_from_city(from_city, from_code)
    search_page.click_search()
    time.sleep(4)


@then("matching flight results should be displayed")
def step_results_displayed(context):
    result_page = ResultPage(context.driver)
    result_page.wait_for_results(
        timeout=get_int("timeouts", "results_load", fallback=60)
    )
    result_page.dismiss_results_popup()
    flight_count = result_page.get_available_flight_count()
    assert flight_count > 0, "No flights found on results page"


@when("the traveler applies the nonstop filter")
def step_apply_nonstop_filter(context):
    result_page = ResultPage(context.driver)
    result_page.apply_nonstop_filter()
    _capture(context, "filter")


@when("the traveler sorts results by lowest price")
def step_sort_by_lowest_price(context):
    result_page = ResultPage(context.driver)
    result_page.sort_by_price()
    result_page.dismiss_results_popup()
    _capture(context, "SortBYPrice")


@when("the traveler filters nonstop flights and sorts by lowest price")
def step_filter_and_sort(context):
    step_apply_nonstop_filter(context)
    step_sort_by_lowest_price(context)


@then("at least one visible flight should remain")
def step_visible_flights_remain(context):
    result_page = ResultPage(context.driver)
    flight_count = result_page.get_available_flight_count()
    assert flight_count > 0, "No flights visible after the current action"
    assert result_page.has_visible_book_buttons(), "No visible Book buttons found"


@then("at least two visible book buttons should be displayed")
def step_at_least_two_book_buttons(context):
    result_page = ResultPage(context.driver)
    buttons = result_page.find_all(By.XPATH, result_page.BOOK_BTN_XPATH)
    visible = [button for button in buttons if button.is_displayed()]
    assert len(visible) >= 2, f"Only {len(visible)} Book button(s) visible"


@then("visible prices should be sorted by lowest price when available")
def step_visible_prices_sorted(context):
    prices = []
    for flight in ResultPage(context.driver).get_flights(max_results=3):
        match = re.search(r"(?:Rs\.?|INR|\u20b9)\s*([\d,]+)", flight["card_text"])
        if match:
            prices.append(int(match.group(1).replace(",", "")))

    if len(prices) >= 2:
        assert prices[0] <= prices[1], f"Price sorting failed: {prices}"


@when("the traveler prints the visible flight results")
def step_print_flight_results(context):
    result_page = ResultPage(context.driver)
    result_page.print_results()
    assert result_page.get_available_flight_count() >= 1, "No flights to print"


@when("the traveler books the first visible flight")
def step_book_first_flight(context):
    ResultPage(context.driver).click_book(index=0)
    _capture(context, "Book_Flight")


@then("the booking page should be displayed")
def step_booking_page_displayed(context):
    BookingPage(context.driver).wait_for_booking_page(timeout=30)
    page_text = context.driver.page_source.lower()
    current_url = context.driver.current_url.lower()
    assert (
        "/flight/booking/" in current_url
        or "booking" in current_url
        or "review" in current_url
        or "traveller" in page_text
        or "passenger" in page_text
        or "contact details" in page_text
    ), "Booking page did not load"


@when("the traveler declines free cancellation")
def step_decline_free_cancellation(context):
    BookingPage(context.driver).decline_free_cancellation()
    _capture(context, "Free_Cancellation")


@when("the traveler declines free cancellation if available")
def step_decline_free_cancellation_if_available(context):
    try:
        step_decline_free_cancellation(context)
    except Exception:
        pass


@then('the route "{route_fragment}" should not be accepted')
def step_route_should_not_be_accepted(context, route_fragment):
    assert route_fragment.lower() not in context.driver.current_url.lower(), (
        f"Same source/destination route was accepted: {context.driver.current_url}"
    )


@then("the traveler should remain off the flight results page")
def step_should_remain_off_results(context):
    assert "search/result" not in context.driver.current_url.lower(), (
        "Search unexpectedly navigated to results without a destination"
    )
