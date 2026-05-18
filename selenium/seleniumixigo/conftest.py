"""
conftest.py — pytest fixtures for browser setup/teardown and page objects.
"""
import os
import sys
import time
import pytest

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(__file__))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver import ChromeOptions, EdgeOptions

from utils.config_reader import get, get_int
from utils.logger import get_logger
from utils.screenshot_util import take_screenshot

log = get_logger()

# Ensure reports directory exists so pytest-html never fails on missing folder
os.makedirs(os.path.join(os.path.dirname(__file__), "reports"), exist_ok=True)


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
    log.info(f"Browser started: {drv.name}")

    return drv


@pytest.fixture(scope="class")
def driver(request):
    """Create one browser per test class."""
    drv = _build_driver()
    yield drv
    pause_seconds = get_int("execution", "final_page_pause_seconds", fallback=3)
    if pause_seconds > 0:
        log.info(f"Keeping final page visible for {pause_seconds}s before closing.")
        time.sleep(pause_seconds)
    # Take a screenshot of the final page before closing
    try:
        class_name = request.cls.__name__ if request.cls else "unknown"
        path = take_screenshot(drv, name=f"final_{class_name}")
        log.info(f"Final screenshot saved: {path}")
    except Exception as exc:
        log.warning(f"Could not take final screenshot: {exc}")
    try:
        log.info("Closing browser.")
        drv.quit()
    except Exception as exc:
        log.warning(f"Browser quit failed: {exc}")


@pytest.fixture
def isolated_driver():
    """Create a fresh browser for standalone test cases."""
    drv = _build_driver()
    yield drv
    pause_seconds = get_int("execution", "final_page_pause_seconds", fallback=3)
    if pause_seconds > 0:
        log.info(f"Keeping final page visible for {pause_seconds}s before closing.")
        time.sleep(pause_seconds)
    try:
        path = take_screenshot(drv, name="final_isolated_driver")
        log.info(f"Final screenshot saved: {path}")
    except Exception as exc:
        log.warning(f"Could not take final screenshot: {exc}")
    log.info("Closing browser.")
    drv.quit()


# ── Auto-screenshot on failure ──────────────────────────────────────
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        drv = item.funcargs.get("driver")
        if drv:
            try:
                path = take_screenshot(drv, name=item.name)
                log.error(f"Screenshot saved: {path}")
            except Exception as exc:
                log.error(f"Screenshot could not be captured: {exc}")
