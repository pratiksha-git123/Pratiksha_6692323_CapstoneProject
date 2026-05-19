"""Steps for the full end-to-end ixigo booking flow."""
from behave import then, when

from combined_flow_steps.combined_steps import _capture, _csv_row, _search_route
from pages.addonspage import AddonsPage
from pages.bookingpage import BookingPage
from pages.loginpage import LoginPage
from pages.paymentpage import PaymentPage
from utils.config_reader import get_int
from utils.route_reader import get_random_route


@when("the traveler logs in using mobile row {row_number:d} from CSV")
def step_login_using_mobile_csv(context, row_number):
    login_mobile = _csv_row("login_data.csv", row_number)["mobile"]
    LoginPage(context.driver).login(
        mobile=login_mobile,
        timeout=get_int("login", "wait_timeout", fallback=300),
    )


@when("the traveler searches using a random route from CSV")
def step_search_random_route(context):
    _search_route(context, get_random_route())


@when("the traveler fills traveller details using row {row_number:d} from CSV")
def step_fill_traveller_details(context, row_number):
    booking_page = BookingPage(context.driver)
    traveller = _csv_row("traveller_data.csv", row_number)
    context.traveller = traveller
    assert booking_page.fill_traveller_form(traveller), "Traveller form was not filled"
    _capture(context, "Traveller_detail")


@when("the traveler completes traveller details using row {row_number:d} from CSV")
def step_complete_traveller_details(context, row_number):
    BookingPage(context.driver).decline_free_cancellation()
    step_fill_traveller_details(context, row_number)
    step_continue_and_confirm(context)


@when("the traveler clicks continue on traveller details")
def step_click_continue_on_traveller_details(context):
    BookingPage(context.driver).click_continue()


@when("the traveler continues and confirms traveller details")
def step_continue_and_confirm(context):
    booking_page = BookingPage(context.driver)
    booking_page.click_continue()
    booking_page.confirm_details()
    booking_page.dismiss_upsell_popup()


@then("the booking page should reject the traveller details")
def step_booking_page_rejects_invalid_details(context):
    booking_page = BookingPage(context.driver)
    assert "/flight/booking/" in context.driver.current_url, (
        "Invalid traveller details unexpectedly left the booking page"
    )
    assert booking_page.has_form_validation_error(), (
        "Expected a validation message for invalid traveller details"
    )


@then("the add-ons page should be displayed")
def step_addons_page_displayed(context):
    AddonsPage(context.driver).wait_for_addons_page(timeout=30)
    _capture(context, "Addons_page")


@when("the traveler selects a seat if available")
def step_select_seat_if_available(context):
    AddonsPage(context.driver).select_random_seat()
    _capture(context, "Seat_selection")


@when("the traveler proceeds through add-ons")
def step_proceed_through_addons(context):
    addons_page = AddonsPage(context.driver)
    addons_page.wait_for_addons_page(timeout=30)
    addons_page.select_random_seat()
    addons_page.skip_to_payment()


@when("the traveler skips seat selection and proceeds to payment")
def step_skip_seat_selection(context):
    addons_page = AddonsPage(context.driver)
    addons_page.wait_for_addons_page(timeout=30)
    addons_page.skip_to_payment()


@when("the traveler skips to payment")
def step_skip_to_payment(context):
    AddonsPage(context.driver).skip_to_payment()
    _capture(context, "Skip_to_payment")


@then("the payment page should be displayed")
def step_payment_displayed(context):
    assert PaymentPage(context.driver).wait_for_payment_page(timeout=30), (
        "Payment page was not reached"
    )
    _capture(context, "PaymentPage")
