"""
test_01_open_and_load.py — Verify site loads correctly (no login needed).

Tests:
  1. ixigo flights page opens successfully
  2. Page title contains 'ixigo'
  3. Search button is present on page load
  4. From/To input fields are present
"""
import pytest

from selenium.webdriver.common.by import By

from pages.flightsearchpage import FlightSearchPage
from utils.logger import get_logger

log = get_logger()


@pytest.mark.usefixtures("driver")
class TestOpenAndLoad:
    """Verify the site opens and key elements are present."""

    @pytest.mark.order(1)
    def test_open_ixigo_page(self, driver):
        """Site should load without errors."""
        page = FlightSearchPage(driver)
        page.open_search_page()
        assert "ixigo" in driver.title.lower(), \
            f"Page title does not contain 'ixigo': {driver.title}"
        log.info("PASS: ixigo page loaded.")

    @pytest.mark.order(2)
    def test_page_title_correct(self, driver):
        """Title should mention flights or ixigo."""
        title = driver.title.lower()
        assert "ixigo" in title or "flight" in title, \
            f"Unexpected page title: {driver.title}"
        log.info(f"PASS: Page title is '{driver.title}'.")

    @pytest.mark.order(3)
    def test_search_button_present(self, driver):
        """Search button should be visible on the homepage."""
        buttons = driver.find_elements(By.XPATH, "//button[normalize-space()='Search']")
        visible = [b for b in buttons if b.is_displayed()]
        assert len(visible) >= 1, "Search button not found on page"
        log.info("PASS: Search button is present.")

    @pytest.mark.order(4)
    def test_search_form_fields_present(self, driver):
        """From and To input areas should be present."""
        from_fields = driver.find_elements(By.XPATH, FlightSearchPage.FROM_INPUT_XPATH)
        to_fields = driver.find_elements(By.XPATH, FlightSearchPage.TO_INPUT_XPATH)
        assert len(from_fields) > 0 or len(to_fields) > 0, \
            "Search form fields (From/To) not found"
        log.info("PASS: Search form fields are present.")
