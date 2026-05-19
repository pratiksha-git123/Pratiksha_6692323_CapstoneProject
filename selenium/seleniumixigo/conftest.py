"""
conftest.py — pytest fixtures for browser setup/teardown and page objects.
"""
import os
import shutil
import sys
import time
from pathlib import Path

import pytest

from utils.screenshot_util import take_screenshot

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(__file__))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver import ChromeOptions, EdgeOptions

from utils.config_reader import get, get_int
from utils.logger import LogGen

logger =LogGen.loggen()




# Ensure report folders exist so pytest-html/allure never fail on missing paths.
PROJECT_ROOT = Path(__file__).parent
REPORTS_DIR = PROJECT_ROOT / "reports"
ALLURE_RESULTS_DIR = REPORTS_DIR / "allure-results"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
HTML_REPORT_PATH = REPORTS_DIR / "report.html"
REPORTS_DIR.mkdir(exist_ok=True)


def _clean_path(path):
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        try:
            path.unlink()
        except OSError as exc:
            logger.warning(f"Could not clean report file {path}: {exc}")


def pytest_configure(config):
    if hasattr(config, "workerinput"):
        return

    for path in (ALLURE_RESULTS_DIR, SCREENSHOTS_DIR, HTML_REPORT_PATH):
        _clean_path(path)

    ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)


def pytest_html_report_title(report):
    report.title = "Ixigo Selenium Automation Report"


# ── Parallel / Sequential mode from config ─────────────────────────
def pytest_load_initial_conftests(early_config, args, parser):
    """Read execution mode from config.properties and inject xdist args.

    config.properties → [execution] mode = parallel | sequential
    parallel  = 6 browsers at once (1 per file, --dist loadfile)
    sequential = 1 browser at a time (default)
    """
    mode = get("execution", "mode", fallback="sequential").lower()
    # Only inject if user didn't already pass -n on command line
    if mode == "parallel" and not any(a.startswith("-n") for a in args):
        args.extend(["-n", "auto", "--dist", "loadfile"])


# ── Browser fixture ─────────────────────────────────────────────────
def _build_driver():
    """Create a browser driver (Edge or Chrome)."""
    browser_name = get("browser", "name", fallback="edge").lower()
    headless = get("browser", "headless", fallback="false").lower() == "true"

    candidates = [
        ("chrome", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        ("chrome", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        ("edge", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        ("edge", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ]

    drv = None
    for name, path in candidates:
        if not os.path.exists(path):
            continue
        if name == "chrome":
            opts = ChromeOptions()
            opts.binary_location = path
            opts.add_argument("--start-maximized")
            opts.add_argument("--disable-notifications")
            opts.add_argument("--disable-features=Autofill")
            if headless:
                opts.add_argument("--headless=new")
            drv = webdriver.Chrome(service=Service(), options=opts)
        else:
            opts = EdgeOptions()
            opts.binary_location = path
            opts.add_argument("--start-maximized")
            opts.add_argument("--disable-notifications")
            opts.add_argument("--disable-features=Autofill")
            if headless:
                opts.add_argument("--headless=new")
            drv = webdriver.Edge(service=EdgeService(), options=opts)
        break

    if drv is None:
        pytest.exit("No Chrome or Edge browser found.")

    drv.implicitly_wait(get_int("timeouts", "implicit_wait", fallback=2))
    logger.info(f"Browser started: {drv.name}")

    return drv


@pytest.fixture(scope="class")
def driver(request):
    """Create one browser per test class."""
    drv = _build_driver()
    yield drv
    pause_seconds = get_int("execution", "final_page_pause_seconds", fallback=3)
    if pause_seconds > 0:
        logger.info(f"Keeping final page visible for {pause_seconds}s before closing.")
        time.sleep(pause_seconds)
    # Take a screenshot of the final page before closing
    try:
        class_name = request.cls.__name__ if request.cls else "unknown"
        path = take_screenshot.capture_screenshot(drv, name=f"final_{class_name}")
        logger.info(f"Final screenshot saved: {path}")
    except Exception as exc:
        logger.warning(f"Could not take final screenshot: {exc}")
    try:
        logger.info("Closing browser.")
        drv.quit()
    except Exception as exc:
        logger.warning(f"Browser quit failed: {exc}")


@pytest.fixture
def isolated_driver():
    """Create a fresh browser for standalone test cases."""
    drv = _build_driver()
    yield drv
    pause_seconds = get_int("execution", "final_page_pause_seconds", fallback=3)
    if pause_seconds > 0:
        logger.info(f"Keeping final page visible for {pause_seconds}s before closing.")
        time.sleep(pause_seconds)
    try:
        path = take_screenshot.capture_screenshot(drv, name="final_isolated_driver")
        logger.info(f"Final screenshot saved: {path}")
    except Exception as exc:
        logger.warning(f"Could not take final screenshot: {exc}")
    logger.info("Closing browser.")
    drv.quit()


def _driver_from_item(item):
    return item.funcargs.get("driver") or item.funcargs.get("isolated_driver")


def _capture_allure_step_screenshot(driver, name):
    path = take_screenshot.capture_screenshot(driver, name=name)
    logger.info(f"Allure step screenshot saved: {path}")
    return path


# ── Auto-screenshot for every test step ─────────────────────────────
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        drv = _driver_from_item(item)
        if drv:
            status = "failed" if report.failed else "skipped" if report.skipped else "passed"
            screenshot_name = f"{item.name}_{status}"
            try:
                _capture_allure_step_screenshot(drv, screenshot_name)
            except Exception as exc:
                logger.error(f"Screenshot could not be captured: {exc}")

#---allure----
# Allure test
def pytest_unconfigure(config):
    """
    This built-in Pytest hook runs exactly once after
    all tests have finished and the browsers are closed.
    """
    print("-------TESTS COMPLETE! GENERATING AND OPENING ALLURE REPORT--------")
    print("-------------------------------------------------------\n")

    # Automatically triggers the terminal command to open the report
    os.system("allure serve reports/allure-results")




