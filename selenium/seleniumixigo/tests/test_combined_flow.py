"""
test_combined_flow.py
Complete Ixigo E2E Flow
"""

import re
import time
from datetime import date

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.flightsearchpage import FlightSearchPage
from pages.resultpage import ResultPage
from pages.bookingpage import BookingPage

from utils.config_reader import get
from utils.logger import LogGen

logger =LogGen.loggen()



##################################################
# MAIN FLOW
##################################################

@pytest.mark.usefixtures("driver")
class TestIxigoCompleteFlow:


    @pytest.mark.order(1)
    def test_open_ixigo_page(self,driver):

        page=FlightSearchPage(driver)

        page.open_search_page()

        assert "ixigo" in driver.title.lower(),\
            "Ixigo page did not open"

        logger.info("PASS: ixigo opened")


    @pytest.mark.order(2)
    def test_page_elements_present(self,driver):

        from_fields=driver.find_elements(
            By.XPATH,
            FlightSearchPage.FROM_INPUT_XPATH
        )

        to_fields=driver.find_elements(
            By.XPATH,
            FlightSearchPage.TO_INPUT_XPATH
        )

        search_btn=driver.find_elements(
            By.XPATH,
            "//button[normalize-space()='Search']"
        )

        assert len(from_fields)>0,\
            "From field missing"

        assert len(to_fields)>0,\
            "To field missing"

        assert len(search_btn)>0,\
            "Search button missing"

        logger.info(
            "PASS: page elements present"
        )


    @pytest.mark.order(3)
    def test_search_bom_to_blr(self,driver):

        page=FlightSearchPage(driver)

        page.open_search_page()

        page.select_from_city(
            "Mumbai",
            "BOM"
        )

        page.select_to_city(
            "Bengaluru",
            "BLR"
        )

        page.select_departure_date(
            date(2026,6,10)
        )

        page.click_search()

        results=ResultPage(driver)

        results.wait_for_results(
            timeout=60
        )

        results.dismiss_results_popup()

        flight_count=results.get_available_flight_count()

        assert flight_count>0,\
            "No flights found"

        logger.info(
            f"PASS:{flight_count} flights available"
        )


    @pytest.mark.order(4)
    def test_flight_count_and_book_buttons(
            self,
            driver
    ):

        results=ResultPage(driver)

        flight_count=results.get_available_flight_count()

        buttons=results.find_all(
            By.XPATH,
            results.BOOK_BTN_XPATH
        )

        visible=[
            x for x in buttons
            if x.is_displayed()
        ]

        assert flight_count>0,\
            "No flights visible"

        assert len(visible)>=2,\
            f"Only {len(visible)} buttons"

        logger.info("PASS")


    @pytest.mark.order(5)
    def test_filter_and_sort(
            self,
            driver
    ):

        results=ResultPage(driver)

        results.apply_nonstop_filter()

        results.sort_by_price()

        flight_count=results.get_available_flight_count()
        assert flight_count>0,\
            "No flights after filter and sort"

        flights=results.get_flights(
            max_results=3
        )

        prices=[]

        for f in flights:

            match=re.search(
                r'₹\s*([\d,]+)',
                f["card_text"]
            )

            if match:

                prices.append(
                    int(
                        match.group(1)
                        .replace(",","")
                    )
                )

        if len(prices)>=2:

            assert prices[0]<=prices[1],\
            f"Price sorting failed:{prices}"

        logger.info(
            f"PASS:{prices}"
        )


    @pytest.mark.order(6)
    def test_print_results(
            self,
            driver
    ):

        ResultPage(driver).print_results()

        logger.info("PASS")



##################################################
# NEGATIVE
##################################################

@pytest.mark.usefixtures("isolated_driver")
class TestNegativeFlow:


    @pytest.mark.order(7)
    def test_same_source_destination(
            self,
            isolated_driver
    ):

        driver=isolated_driver

        page=FlightSearchPage(driver)

        page.open_search_page()

        page.select_from_city(
            "Mumbai",
            "BOM"
        )

        page.select_to_city(
            "Mumbai",
            "BOM"
        )

        page.click_search()

        time.sleep(3)

        assert "bom-bom" not in \
               driver.current_url.lower(),\
               "ERROR: Same source accepted"

        logger.info("PASS")


    @pytest.mark.order(8)
    def test_search_without_destination(
            self,
            isolated_driver
    ):

        driver=isolated_driver

        page=FlightSearchPage(driver)

        page.open_search_page()

        page.select_from_city(
            "Mumbai",
            "BOM"
        )

        page.click_search()

        time.sleep(4)

        assert \
        "search/result" not in \
        driver.current_url.lower(),\
        "ERROR: search worked without destination"

        logger.info("PASS")



##################################################
# BOOKING FLOW
##################################################

@pytest.mark.usefixtures("isolated_driver")
class TestBookingFlow:


    @pytest.mark.order(9)
    def test_booking_flow(
            self,
            isolated_driver
    ):

        driver=isolated_driver

        page=FlightSearchPage(driver)

        page.open_search_page()

        page.select_from_city(
            "Mumbai",
            "BOM"
        )

        page.select_to_city(
            "Bengaluru",
            "BLR"
        )

        page.select_departure_date(
            date(2026,6,4)
        )

        page.click_search()

        results=ResultPage(driver)

        results.wait_for_results(
            timeout=60
        )

        results.dismiss_results_popup()

        results.apply_nonstop_filter()

        results.sort_by_price()

        flight_count=results.get_available_flight_count()

        assert flight_count>0,\
            "ERROR: no flights available"

        results.click_book(
            index=0
        )

        time.sleep(7)

        # switch if new tab opens
        if len(driver.window_handles)>1:

            driver.switch_to.window(
                driver.window_handles[-1]
            )

        booking=BookingPage(driver)

        page_loaded=False

        try:

            WebDriverWait(
                driver,
                40
            ).until(

                lambda d:

                (
                    "booking" in
                    d.current_url.lower()

                    or

                    "traveller" in
                    d.page_source.lower()

                    or

                    "passenger" in
                    d.page_source.lower()

                    or

                    "contact details" in
                    d.page_source.lower()

                    or

                    "review" in
                    d.current_url.lower()
                )
            )

            page_loaded=True

        except:

            page_loaded=False


        assert page_loaded,\
        f"""
ERROR: Booking page not detected

Current URL:
{driver.current_url}

Title:
{driver.title}

Tabs:
{len(driver.window_handles)}

Reason:
Traveller / Passenger / Contact Details text not found
"""


        # optional
        try:
            booking.decline_free_cancellation()
        except:
            logger.info(
                "No cancellation popup found"
            )

        logger.info(
            "PASS: booking flow completed"
        )
