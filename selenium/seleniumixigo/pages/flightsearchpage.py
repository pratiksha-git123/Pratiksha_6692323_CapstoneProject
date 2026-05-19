"""
FlightSearchPage - fills in the ixigo flight search form.
"""
import time
from datetime import date

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.basepage import BasePage
from utils.logger import LogGen

logger =LogGen.loggen()


class FlightSearchPage(BasePage):
    """Page Object for the ixigo flight search form."""

    URL = "https://www.ixigo.com/flights"

    FROM_INPUT_XPATH = (
        "/html/body/main/div[2]/div[1]/div[3]/div[2]"
        "/div[1]/div[1]/div[2]/div/div/div[2]/input"
    )
    TO_INPUT_XPATH = (
        "/html/body/main/div[2]/div[1]/div[3]/div[2]"
        "/div[1]/div[2]/div[2]/div/div/div[2]/input"
    )
    SEARCH_BTN_XPATH = "//button[normalize-space()='Search']"
    CALENDAR_LABEL_CSS = "span.react-calendar__navigation__label__labelText"
    CALENDAR_NEXT_CSS = "button.react-calendar__navigation__next-button"
    CALENDAR_TILE_XPATH = (
        "//button[contains(@class,'react-calendar__tile')]"
        "//abbr[@aria-label='{label}']/parent::button"
    )
    LISTITEM_XPATH = "//div[@role='listitem']"
    FIELD_VALUE_TESTIDS = {
        "From": "originId",
        "To": "destinationId",
    }

    def open_search_page(self):
        self.open(self.URL)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.XPATH, self.SEARCH_BTN_XPATH))
        )
        self.dismiss_all_popups()

    def wait_for_search_form(self, timeout: int = 15):
        """Wait until the search form is interactive (From input clickable)."""
        logger.info("Waiting for search form to be interactive...")
        WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, self.SEARCH_BTN_XPATH))
        )
        # The "From" label is rendered with different tags depending on whether
        # the form is fresh or already prefilled, so match the visible text
        # instead of assuming a specific element type.
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, "//*[normalize-space()='From']"))
        )
        logger.info("Search form is ready.")

    def select_from_city(self, city: str, code: str):
        self._fill_city("From", city, code, self.FROM_INPUT_XPATH)

    def select_to_city(self, city: str, code: str):
        self._fill_city("To", city, code, self.TO_INPUT_XPATH)

    def select_departure_date(self, travel_date: date):
        month_year = travel_date.strftime("%B %Y")
        day = travel_date.day
        aria_label = f"{travel_date.strftime('%B')} {day}, {travel_date.year}"
        logger.info(f"Selecting date: {day} {month_year}")

        try:
            departure = self.driver.find_element(
                By.XPATH, "//p[text()='Departure']/ancestor::div[contains(@class,'flex')][1]"
            )
            self.safe_click(departure)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.CALENDAR_LABEL_CSS))
            )
        except Exception:
            pass

        for _ in range(14):
            try:
                labels = self.find_all(By.CSS_SELECTOR, self.CALENDAR_LABEL_CSS)
                if any(month_year in label.text for label in labels):
                    break
                next_button = self.driver.find_element(By.CSS_SELECTOR, self.CALENDAR_NEXT_CSS)
                self.safe_click(next_button)
                WebDriverWait(self.driver, 3).until(
                    EC.staleness_of(labels[0]) if labels else EC.presence_of_element_located(
                        (By.CSS_SELECTOR, self.CALENDAR_LABEL_CSS)
                    )
                )
            except Exception:
                time.sleep(0.3)

        tile_xpath = self.CALENDAR_TILE_XPATH.format(label=aria_label)
        try:
            day_button = self.find_clickable(By.XPATH, tile_xpath, timeout=5)
            self.safe_click(day_button)
            logger.info(f"Selected date: {aria_label}")
            return
        except TimeoutException:
            pass

        try:
            abbr = self.driver.find_element(By.CSS_SELECTOR, f"abbr[aria-label='{aria_label}']")
            self.safe_click(abbr)
            logger.info(f"Selected date (abbr fallback): {aria_label}")
        except Exception:
            logger.warning(f"Could not select date {aria_label}")

    def click_search(self):
        logger.info("Clicking Search...")
        self.dismiss_all_popups()
        button = self.find_clickable(By.XPATH, self.SEARCH_BTN_XPATH)
        self.safe_click(button)
        logger.info("Search clicked.")

    def _fill_city(self, label: str, city: str, code: str, fallback_xpath: str):
        logger.info(f"Selecting {label}: {city} ({code})")
        city_input = self._open_city_picker(label)

        if city_input is None:
            city_input = self._first_visible_text_input()

        if city_input is None:
            try:
                city_input = self.find_clickable(By.XPATH, fallback_xpath, timeout=3)
            except TimeoutException:
                pass

        if city_input is None:
            logger.error(f"Could not find {label} input!")
            return

        # Type the human city name, then select the exact airport code from
        # the populated dropdown. Typing only the code is less reliable on
        # ixigo because "BOM" can fuzzily resolve to places like Boma.
        self.clear_and_type(city_input, city)
        self._pick_city_option(city, code)

    def _open_city_picker(self, label: str):
        # After selecting the origin, ixigo often opens the destination input
        # automatically. Reuse that focused input instead of clicking again and
        # risking a second dropdown state.
        try:
            active = self.driver.switch_to.active_element
            if active.tag_name == "input" and active.is_displayed():
                return active
        except Exception:
            pass

        # Prefilled forms show a compact summary ("BOM - Mumbai") instead of
        # exposing the text input immediately. Click that summary first when it
        # exists, then type into the input that opens.
        testid = self.FIELD_VALUE_TESTIDS.get(label)
        if testid:
            try:
                current_value = self.find_clickable(
                    By.CSS_SELECTOR, f"[data-testid='{testid}']", timeout=3
                )
                self.safe_click(current_value)
                return self.find_clickable(
                    By.CSS_SELECTOR, "input:focus, input[autofocus]", timeout=5
                )
            except Exception:
                pass

        try:
            field_label = self.driver.find_element(
                By.XPATH, f"//*[normalize-space()='{label}']"
            )
            container = field_label.find_element(
                By.XPATH, "./ancestor::div[contains(@class,'flex')][1]"
            )
            self.safe_click(container)
            return self.find_clickable(
                By.CSS_SELECTOR, "input:focus, input[autofocus]", timeout=5
            )
        except Exception:
            return None

    def _first_visible_text_input(self):
        for element in self.find_all(By.CSS_SELECTOR, "input"):
            try:
                input_type = element.get_attribute("type") or ""
                if element.is_displayed() and element.is_enabled() and input_type in ("", "text", "search"):
                    return element
            except Exception:
                continue
        return None

    def _pick_city_option(self, city: str, code: str):
        for attempt in range(2):
            try:
                options = WebDriverWait(self.driver, 8).until(
                    EC.presence_of_all_elements_located((By.XPATH, self.LISTITEM_XPATH))
                )
                # ixigo can briefly show an initial fuzzy list and then update
                # it again; give the dropdown a moment to settle before click.
                time.sleep(2)
                options = self.find_all(By.XPATH, self.LISTITEM_XPATH)
                for option in options:
                    if not option.is_displayed():
                        continue

                    lines = [line.strip() for line in option.text.splitlines() if line.strip()]
                    option_code = lines[0] if lines else ""
                    option_text = " ".join(lines[1:]).lower()
                    if option_code == code and city.lower() in option_text:
                        self.safe_click(option)
                        logger.info(f"Selected {code} from dropdown.")
                        return
            except TimeoutException:
                pass

            if attempt == 0:
                logger.info(f"{code} not in dropdown — clearing and retyping...")
                active = self.driver.switch_to.active_element
                active.send_keys(Keys.CONTROL, "a")
                active.send_keys(Keys.BACKSPACE)
                # Wait for dropdown to clear
                WebDriverWait(self.driver, 5).until_not(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='listitem']"))
                )
                active.send_keys(code)
                # Wait for new dropdown options to appear
                WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='listitem']"))
                )
                time.sleep(2)

        logger.warning(f"Could not find {code} in dropdown — pressing Enter on current suggestion.")
        self.driver.switch_to.active_element.send_keys(Keys.ENTER)
