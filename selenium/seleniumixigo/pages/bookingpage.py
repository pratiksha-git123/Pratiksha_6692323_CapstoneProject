"""
BookingPage — handles the Review & Traveller Details page (Step 2).

ixigo uses floating label elements for form fields. The label element type
varies by airline provider (div, label, span, legend). All XPaths use //*
to match any element type.  Title can be a custom textbox dropdown OR a
native <select>.  Contact fields may be pre-filled from the logged-in
account.
"""
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.basepage import BasePage
from utils.logger import LogGen

logger =LogGen.loggen()

class BookingPage(BasePage):
    """Page Object for the Review & Traveller Details step."""

    # ── Locators ─────────────────────────────────────────────────────
    TRAVELLER_HEADING_XPATH = "//h5[normalize-space()='Traveller Details']"

    DECLINE_CANCELLATION_XPATH = (
        "//input[@type='radio'][following-sibling::*[contains(.,'don')]]"
    )
    DECLINE_CANCELLATION_LABEL_XPATH = (
        "//*[.//input[@type='radio']][.//text()[contains(.,'don')]]"
    )

    CONTINUE_BTN_XPATH = "//button[normalize-space()='Continue']"
    CONFIRM_BTN_XPATH = "//button[normalize-space()='Confirm']"
    NO_THANKS_XPATH = (
        "//button[contains(text(),'No') and contains(text(),'Thanks')]"
        " | //button[contains(text(),'No, thanks')]"
    )
    VALIDATION_MESSAGE_XPATH = (
        "//*[contains(@class,'error') or contains(@class,'invalid')]"
        "[normalize-space()]"
        " | //*[contains(text(),'valid email')]"
        " | //*[contains(text(),'valid mobile')]"
        " | //*[contains(text(),'required')]"
    )

    # ── Wait for booking page ────────────────────────────────────────
    def wait_for_booking_page(self, timeout: int = 30):
        logger.info("Waiting for booking/traveller details page...")
        WebDriverWait(self.driver, timeout).until(
            EC.url_contains("/flight/booking/")
        )
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, self.TRAVELLER_HEADING_XPATH)
            )
        )
        logger.info("Booking page loaded.")

    # ── Decline Free Cancellation ─────────────────────────────────────
    def decline_free_cancellation(self):
        logger.info("Selecting 'I don't want Free Cancellation'...")
        try:
            section = self.find(
                By.XPATH, "//*[contains(.,'Add Free Cancellation')]", timeout=10,
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", section
            )
        except TimeoutException:
            pass

        xpaths = [
            self.DECLINE_CANCELLATION_XPATH,
            "(//*[contains(.,'Add Free Cancellation')]"
            "//input[@type='radio'])[last()]",
            self.DECLINE_CANCELLATION_LABEL_XPATH,
        ]
        for xpath in xpaths:
            try:
                radio = self.find(By.XPATH, xpath, timeout=5)
                self.js_click(radio)
                logger.info("Declined Free Cancellation.")
                return
            except TimeoutException:
                continue
        logger.warning("Could not find 'I don't want Free Cancellation' radio.")

    # ── Deselect any pre-selected saved travellers ─────────────────
    def _deselect_saved_travellers(self):
        """Uncheck any pre-selected saved traveller checkboxes so we can
        fill the form manually."""
        logger.info("Deselecting any pre-selected saved travellers...")
        try:
            checkboxes = self.driver.find_elements(
                By.XPATH,
                "//h5[normalize-space()='Traveller Details']"
                "/ancestor::*[1]//input[@type='checkbox']"
            )
            for cb in checkboxes:
                try:
                    if cb.is_selected():
                        self.js_click(cb)
                        logger.info("Unchecked a pre-selected saved traveller.")
                except Exception:
                    continue
        except Exception:
            pass

    # ── Expand the traveller form (click edit icon) ──────────────────
    def _expand_traveller_form(self):
        """Click the Adult 1 section/edit icon to expand the form fields."""
        logger.info("Expanding traveller form...")
        try:
            # Try clicking the edit/pencil icon or "Adult 1" text
            xpaths = [
                "//*[contains(text(),'Adult 1')]/preceding-sibling::img",
                "//*[contains(text(),'Adult 1')]/..",
                "//*[contains(text(),'Adult')]//ancestor::*[1]//img",
            ]
            for xpath in xpaths:
                try:
                    el = self.find(By.XPATH, xpath, timeout=3)
                    self.js_click(el)
                    # Wait for form fields to appear
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((
                            By.XPATH, "//*[normalize-space()='Title']"
                        ))
                    )
                    logger.info("Expanded traveller form.")
                    return
                except TimeoutException:
                    continue
        except Exception:
            pass

    # ── Generic input finder (handles div/label/span/legend labels) ──
    def _find_input(self, label_text: str, exact: bool = True,
                    timeout: int = 10):
        """Find an input/select near a floating label.

        Tries multiple XPath strategies so that the code works regardless
        of whether the label is a <div>, <label>, <span>, or <legend>.
        """
        if exact:
            pred = f"normalize-space()='{label_text}'"
        else:
            pred = f"contains(text(),'{label_text}')"

        strategies = [
            f"//*[{pred}]/following-sibling::input",
            f"//*[{pred}]/following-sibling::select",
            f"//*[{pred}]/parent::*//input[not(@type='hidden')]",
            f"//*[{pred}]/parent::*//select",
        ]

        for xpath in strategies:
            try:
                el = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                if el.is_displayed():
                    logger.info(f"Found '{label_text}' via: {xpath}")
                    return el
            except (TimeoutException, Exception):
                continue

        raise TimeoutException(
            f"Field '{label_text}' not found after {len(strategies)} strategies"
        )

    # ── Title selection ──────────────────────────────────────────────
    def select_title(self, title: str) -> bool:
        logger.info(f"Selecting title: {title}")
        try:
            el = self._find_input("Title", exact=True, timeout=8)
        except TimeoutException:
            logger.error("Title field NOT FOUND.")
            return False

        tag = el.tag_name.lower()

        # Native <select>
        if tag == "select":
            from selenium.webdriver.support.ui import Select
            try:
                Select(el).select_by_visible_text(title)
                logger.info(f"Title '{title}' selected via <select>.")
                return True
            except Exception:
                try:
                    Select(el).select_by_value(title)
                    return True
                except Exception:
                    logger.error(f"Could not select '{title}' from <select>.")
                    return False

        # Custom dropdown textbox — click to open, then click option
        self.safe_click(el)

        try:
            option = self.find_clickable(
                By.XPATH,
                f"//p[normalize-space()='{title}']"
                f" | //*[normalize-space()='{title}'"
                f"    and (self::div or self::li or self::span)]",
                timeout=5,
            )
            self.safe_click(option)
            logger.info(f"Title '{title}' selected from dropdown.")
            return True
        except TimeoutException:
            logger.info(f"Typing title '{title}' directly.")
            el.send_keys(Keys.CONTROL, "a")
            el.send_keys(title)
            el.send_keys(Keys.RETURN)
            return True

    # ── Fill a single field ──────────────────────────────────────────
    def _fill_field(self, label_text: str, value: str,
                    exact: bool = True) -> bool:
        """Find a field by its label and type into it.  Returns True on
        success, False if the field was not found."""
        if not value:
            return True
        logger.info(f"Filling '{label_text}': {value}")
        try:
            el = self._find_input(label_text, exact=exact, timeout=8)
        except TimeoutException:
            logger.error(f"FIELD NOT FOUND: '{label_text}'")
            return False

        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", el
            )
            el.click()
            el.send_keys(Keys.CONTROL, "a")
            el.send_keys(Keys.DELETE)
            el.send_keys(value)
            el.send_keys(Keys.ESCAPE)

            actual = el.get_attribute("value") or ""
            if value.lower() not in actual.lower():
                logger.warning(
                    f"'{label_text}': expected '{value}', got '{actual}'"
                )
            return True
        except Exception as e:
            logger.error(f"Failed to fill '{label_text}': {e}")
            return False

    def _fill_if_empty(self, label_text: str, value: str,
                       exact: bool = True):
        """Fill a field only when it is currently empty."""
        if not value:
            return
        try:
            el = self._find_input(label_text, exact=exact, timeout=5)
            current = el.get_attribute("value") or ""
            if current.strip():
                logger.info(f"'{label_text}' pre-filled: '{current}' — keeping.")
                return
            self._fill_field(label_text, value, exact=exact)
        except TimeoutException:
            logger.warning(f"'{label_text}' not found — skipping.")

    # ── Fill entire form from CSV row ───────────────────────────────
    def fill_traveller_form(self, data: dict) -> bool:
        """Fill every traveller form field manually from CSV data.
        Returns True if all required fields were filled successfully."""
        logger.info("Filling traveller form from CSV data...")
        title = data.get("title", "Mr")
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")

        # Step 0: Deselect any auto-selected saved travellers
        self._deselect_saved_travellers()

        # Step 0b: Expand the form if it's collapsed
        self._expand_traveller_form()

        ok = True

        # 1. Title
        if not self.select_title(title):
            ok = False

        # 2. First & Middle Name
        if not self._fill_field("First", first_name, exact=False):
            ok = False

        # 3. Last Name
        if not self._fill_field("Last Name", last_name):
            ok = False

        # 4. Mobile Number
        if not self._fill_field("Mobile Number", data.get("mobile", "")):
            ok = False

        # 5. Email
        if not self._fill_field("Email", data.get("email", "")):
            ok = False

        # 6. Pincode (optional — not all providers show Billing Address)
        pincode = data.get("pincode", "")
        if pincode:
            try:
                self._find_input("Pincode", exact=True, timeout=3)
                if not self._fill_field("Pincode", pincode):
                    ok = False
            except TimeoutException:
                logger.info("Pincode field not present on this provider — skipping.")

        # 7. Address (optional — not all providers show Billing Address)
        address = data.get("address", "")
        if address:
            try:
                self._find_input("Address", exact=True, timeout=3)
                if not self._fill_field("Address", address):
                    ok = False
            except TimeoutException:
                logger.info("Address field not present on this provider — skipping.")

        if ok:
            logger.info("Traveller form filled successfully (all fields).")
        else:
            logger.error("Some traveller fields could NOT be filled!")
        return ok

    # ── Click Continue ───────────────────────────────────────────────
    def click_continue(self):
        logger.info("Clicking Continue...")
        btn = self.find_clickable(By.XPATH, self.CONTINUE_BTN_XPATH, timeout=10)
        self.safe_click(btn)
        # Wait for Confirm button or page transition
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, self.CONFIRM_BTN_XPATH))
            )
        except TimeoutException:
            pass
        logger.info("Continue clicked.")

    # ── Confirm traveller details (Review dialog) ────────────────────
    def confirm_details(self):
        logger.info("Looking for Confirm button on review dialogger...")
        try:
            btn = self.find_clickable(By.XPATH, self.CONFIRM_BTN_XPATH, timeout=10)
            self.safe_click(btn)
            logger.info("Confirm clicked.")
            # Wait for page transition (addons page or upsell popup)
            WebDriverWait(self.driver, 10).until(
                lambda d: "booking" not in d.current_url or
                len(d.find_elements(By.XPATH, self.NO_THANKS_XPATH)) > 0
            )
        except TimeoutException:
            logger.info("No Confirm dialog appeared — continuing.")

    # ── Dismiss upsell popups ────────────────────────────────────────
    def dismiss_upsell_popup(self):
        logger.info("Checking for upsell popup...")
        try:
            btn = self.find_clickable(By.XPATH, self.NO_THANKS_XPATH, timeout=8)
            self.safe_click(btn)
            logger.info("Upsell popup dismissed (No, Thanks).")
        except TimeoutException:
            alt_xpaths = [
                "//button[contains(text(),'Skip')]",
                "//*[contains(@class,'close')]//img[contains(@alt,'close')]/..",
            ]
            for xpath in alt_xpaths:
                try:
                    btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    self.safe_click(btn)
                    logger.info("Upsell popup dismissed (alt).")
                    return
                except (TimeoutException, Exception):
                    continue
            logger.info("No upsell popup found.")

    def has_form_validation_error(self) -> bool:
        for message in self.find_all(By.XPATH, self.VALIDATION_MESSAGE_XPATH):
            try:
                if message.is_displayed() and message.text.strip():
                    return True
            except Exception:
                continue
        return False

    # ── Full booking flow ────────────────────────────────────────────
    def complete_traveller_details(self, data: dict):
        self.fill_traveller_form(data)
        self.click_continue()
        self.confirm_details()
        self.dismiss_upsell_popup()
        logger.info("Traveller details completed — proceeding to add-ons.")
