"""
test_combined_flow.py
Complete Ixigo E2E flow
"""

import re
from datetime import date

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.flightsearchpage import FlightSearchPage
from pages.resultpage import ResultPage
from pages.bookingpage import BookingPage

from utils.config_reader import get
from utils.logger import get_logger

log = get_logger()


@pytest.mark.usefixtures("driver")
class TestIxigoCompleteFlow:

    ##################################################
    # PAGE LOAD
    ##################################################

    @pytest.mark.order(1)
    def test_open_ixigo_page(self, driver):

        page = FlightSearchPage(driver)

        page.open_search_page()

        assert "ixigo" in driver.title.lower()

        log.info("PASS: ixigo loaded")


    @pytest.mark.order(2)
    def test_page_elements_present(self, driver):

        from_fields = driver.find_elements(
            By.XPATH,
            FlightSearchPage.FROM_INPUT_XPATH
        )

        to_fields = driver.find_elements(
            By.XPATH,
            FlightSearchPage.TO_INPUT_XPATH
        )

        buttons=driver.find_elements(
            By.XPATH,
            "//button[normalize-space()='Search']"
        )

        assert len(from_fields)>0
        assert len(to_fields)>0
        assert len(buttons)>0

        log.info("PASS: page elements present")


    ##################################################
    # SEARCH
    ##################################################

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

        flights=results.get_flights()

        assert len(flights)>0

        url=driver.current_url.lower()

        assert "bom" in url
        assert "blr" in url

        log.info(
            f"PASS: {len(flights)} flights"
        )


    @pytest.mark.order(4)
    def test_flight_count_and_book_buttons(self,driver):

        results=ResultPage(driver)

        count=results.get_flight_count_text()

        flights=results.get_flights()

        buttons=results.find_all(
            By.XPATH,
            results.BOOK_BTN_XPATH
        )

        visible=[
            x for x in buttons
            if x.is_displayed()
        ]

        assert len(flights)>0 or count!=""

        assert len(visible)>=2

        log.info(
            f"PASS: {len(visible)} buttons"
        )


    ##################################################
    # FILTER + SORT
    ##################################################

    @pytest.mark.order(5)
    def test_filter_and_sort(self,driver):

        results=ResultPage(driver)

        results.apply_nonstop_filter()

        results.sort_by_price()

        results.dismiss_results_popup()

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

            assert prices[0]<=prices[1]

        log.info(
            f"PASS: {prices}"
        )


    @pytest.mark.order(6)
    def test_print_results(self,driver):

        results=ResultPage(driver)

        results.print_results()

        flights=results.get_flights()

        assert len(flights)>0

        log.info("PASS")


    ##################################################
    # NEGATIVE
    ##################################################

    @pytest.mark.order(7)
    def test_same_source_destination(self,driver):

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

        page.select_departure_date(
            date(2026,6,10)
        )

        page.click_search()

        WebDriverWait(
            driver,
            10
        ).until(
            lambda d: d.current_url
        )

        url=driver.current_url.lower()

        # Should fail if BOM→BOM actually proceeds
        assert not (
            "bom-bom" in url
        ), \
        "Same source-destination allowed"

        log.info(
            "PASS: same route blocked"
        )


    @pytest.mark.order(8)
    def test_search_without_destination(self,driver):

        page=FlightSearchPage(driver)

        page.open_search_page()

        page.select_from_city(
            "Mumbai",
            "BOM"
        )

        page.select_departure_date(
            date(2026,6,10)
        )

        page.click_search()

        import time
        time.sleep(3)

        url=driver.current_url.lower()

        assert "search/result" not in url

        log.info(
            "PASS: destination mandatory"
        )


##################################################
# BOOKING
##################################################

@pytest.mark.usefixtures(
    "isolated_driver"
)
class TestBookingFlow:

    @pytest.mark.order(9)
    def test_booking_flow(
            self,
            isolated_driver
    ):

        driver=isolated_driver

        page=FlightSearchPage(driver)

        page.open_search_page()

        from_city=get(
            "search",
            "from_city",
            fallback="Mumbai"
        )

        from_code=get(
            "search",
            "from_code",
            fallback="BOM"
        )

        to_city=get(
            "search",
            "to_city",
            fallback="Bengaluru"
        )

        to_code=get(
            "search",
            "to_code",
            fallback="BLR"
        )

        travel_date=date.fromisoformat(
            get(
                "search",
                "travel_date",
                fallback="2026-06-04"
            )
        )

        page.select_from_city(
            from_city,
            from_code
        )

        page.select_to_city(
            to_city,
            to_code
        )

        page.select_departure_date(
            travel_date
        )

        page.click_search()

        results=ResultPage(driver)

        results.wait_for_results(
            timeout=60
        )

        results.dismiss_results_popup()

        results.apply_nonstop_filter()

        results.sort_by_price()

        results.dismiss_results_popup()

        flights=results.get_flights()

        assert len(flights)>0

        results.click_book(
            index=0
        )

        booking=BookingPage(
            driver
        )

        booking.wait_for_booking_page(
            timeout=40
        )

        assert "/flight/booking/" \
               in driver.current_url

        heading=driver.find_elements(
            By.XPATH,
            "//h5[contains(.,'Traveller')]"
        )

        assert any(
            x.is_displayed()
            for x in heading
        )

        booking.decline_free_cancellation()

        log.info(
            "PASS: booking completed"
        )