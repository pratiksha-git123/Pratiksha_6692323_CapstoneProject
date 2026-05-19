"""
BasePage — common Selenium helpers inherited by all page objects.
"""
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.logger import get_logger

log = get_logger()


class BasePage:
    """Base class for all Page Objects."""

    def __init__(self, driver: WebDriver, timeout: int = 10):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(
            driver, timeout,
            ignored_exceptions=[StaleElementReferenceException],
        )

    # ── Element finders ─────────────────────────────────────────────
    def find(self, by: str, value: str, timeout: int | None = None) -> WebElement:
        w = WebDriverWait(self.driver, timeout or self.timeout)
        return w.until(EC.presence_of_element_located((by, value)))

    def find_visible(self, by: str, value: str, timeout: int | None = None) -> WebElement:
        w = WebDriverWait(self.driver, timeout or self.timeout)
        return w.until(EC.visibility_of_element_located((by, value)))

    def find_clickable(self, by: str, value: str, timeout: int | None = None) -> WebElement:
        w = WebDriverWait(self.driver, timeout or self.timeout)
        return w.until(EC.element_to_be_clickable((by, value)))

    def find_all(self, by: str, value: str) -> list[WebElement]:
        return self.driver.find_elements(by, value)

    # ── Click helpers ───────────────────────────────────────────────
    def safe_click(self, element: WebElement):
        """Scroll into view and click; fallback to JS click."""
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", element
        )
        try:
            element.click()
        except (ElementClickInterceptedException, Exception):
            self.driver.execute_script("arguments[0].click();", element)

    def js_click(self, element: WebElement):
        """Force-click via JavaScript (for opacity-0 checkboxes/radios)."""
        self.driver.execute_script("arguments[0].click();", element)

    def click_first_match(self, xpaths: list[str], timeout: int = 10) -> WebElement:
        """Try each XPath; click the first one that becomes clickable."""
        for xpath in xpaths:
            try:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                self.safe_click(el)
                return el
            except (TimeoutException, Exception):
                continue
        raise TimeoutException(f"None of these XPaths were clickable: {xpaths}")

    # ── Input helpers ───────────────────────────────────────────────
    def clear_and_type(self, element: WebElement, text: str):
        element.click()
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(text)

    # ── Wait helpers ────────────────────────────────────────────────
    def wait_for_url_contains(self, fragment: str, timeout: int = 30):
        WebDriverWait(self.driver, timeout).until(
            EC.url_contains(fragment)
        )

    def wait_for_element_gone(self, by: str, value: str, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until_not(
            EC.presence_of_element_located((by, value))
        )

    # ── Popup / overlay handling ────────────────────────────────────
    def dismiss_clevertap_popup(self):
        """Close the CleverTap iframe interstitial if present."""
        try:
            iframe = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "wiz-iframe-intent"))
            )
            self.driver.switch_to.frame(iframe)
            try:
                btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.ID, "closeButton"))
                )
                btn.click()
                log.info("CleverTap popup closed.")
            except Exception:
                pass
            self.driver.switch_to.default_content()
        except TimeoutException:
            pass

        # JS fallback — remove overlay nodes
        self.driver.execute_script("""
            for (const id of ['intentOpacityDiv','intentPreview','wiz-iframe-intent']) {
                const el = document.getElementById(id);
                if (el) el.remove();
            }
        """)

    def close_sale_banner(self):
        """Hide the Flash Sale banner via JS."""
        self.driver.execute_script("""
            let s = document.querySelector(
                'section[aria-label*="Sale"], [role="region"][aria-label*="Sale"]'
            );
            if (!s) {
                for (const el of document.querySelectorAll('div, section')) {
                    if (el.textContent.includes('Flash Sale') && el.children.length <= 3) {
                        s = el; break;
                    }
                }
            }
            if (s) s.style.display = 'none';
        """)
        log.info("Sale banner closed.")

    def press_escape(self):
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass

    def dismiss_all_popups(self):
        """Run all popup-dismissal routines."""
        self.dismiss_clevertap_popup()
        self.close_sale_banner()
        self.press_escape()

    # ── Navigation ──────────────────────────────────────────────────
    def open(self, url: str):
        log.info(f"Opening {url}")
        self.driver.get(url)

    @property
    def current_url(self) -> str:
        return self.driver.current_url

    @property
    def title(self) -> str:
        return self.driver.title
