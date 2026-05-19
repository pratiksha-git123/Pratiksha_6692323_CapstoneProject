"""Behave hooks for the standalone ixigo BDD project."""
from datetime import datetime
import html
import json
import os
import shutil
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

from behave.model_core import Status
from selenium import webdriver
from selenium.webdriver import ChromeOptions, EdgeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.edge.service import Service as EdgeService

from pages.flightsearchpage import FlightSearchPage
from utils.config_reader import get, get_int
from utils.logger import get_logger
from utils.screenshot_util import take_screenshot

log = get_logger()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
ALLURE_RESULTS_DIR = REPORTS_DIR / "allure-results"
ALLURE_REPORT_DIR = REPORTS_DIR / "allure-report"
HTML_REPORT_PATH = REPORTS_DIR / "report.html"
ALLURE_COMMAND_LOG = REPORTS_DIR / "allure-command.log"


def _clean_report_dir(path: Path):
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)


def _clean_file_pattern(directory: Path, pattern: str):
    if not directory.exists():
        return
    for path in directory.glob(pattern):
        try:
            if path.is_file():
                path.unlink()
        except OSError:
            pass


def _allure_env():
    env = os.environ.copy()
    app_home = _find_allure_app_home()
    if app_home:
        env["APP_HOME"] = str(app_home)
    return env


def _find_allure_app_home() -> Path | None:
    """Find the Allure commandline app home without depending on one Windows user."""
    configured = os.environ.get("ALLURE_HOME") or os.environ.get("APP_HOME")
    if configured and Path(configured).exists():
        return Path(configured)

    appdata = os.environ.get("APPDATA")
    candidates = []
    if appdata:
        candidates.append(Path(appdata) / "npm" / "node_modules" / "allure-commandline" / "dist")

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _find_allure_bin() -> str | None:
    """Find the Allure executable on Windows/macOS/Linux."""
    configured = os.environ.get("ALLURE_BIN")
    if configured and Path(configured).exists():
        return configured

    found = shutil.which("allure")
    if found:
        return found

    appdata = os.environ.get("APPDATA")
    candidates = []
    if appdata:
        candidates.extend(
            [
                Path(appdata) / "npm" / "allure.cmd",
                Path(appdata) / "npm" / "allure",
            ]
        )

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def _allure_command(args: list[str]):
    allure_bin = _find_allure_bin()
    if not allure_bin:
        return None
    return [allure_bin, *args]


def _allure_install_message() -> str:
    return (
        "Allure commandline was not found on this system. "
        "The Behave tests still completed and the local HTML report was generated. "
        "To open the Allure report automatically, install the Allure CLI and make sure "
        "'allure' is available in PATH. On Windows with npm, use: npm install -g allure-commandline"
    )


def _run_allure(args: list[str], wait: bool = True):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = open(ALLURE_COMMAND_LOG, "a", encoding="utf-8")
    command = _allure_command(args)
    if not command:
        log_file.write(_allure_install_message() + "\n")
        log_file.close()
        return 127
    process = subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        env=_allure_env(),
        stdout=log_file,
        stderr=log_file,
    )
    if wait:
        try:
            return process.wait()
        finally:
            log_file.close()
    log_file.close()
    return 0


def _wait_for_allure_results(timeout_seconds: int = 90) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if any(ALLURE_RESULTS_DIR.glob("*result.json")):
            return True
        time.sleep(2)
    return False


def _patch_behavior_labels() -> int:
    updated = 0
    for path in ALLURE_RESULTS_DIR.glob("*result.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        labels = data.setdefault("labels", [])
        label_names = {label.get("name") for label in labels}
        story_value = data.get("name")
        changed = False

        if "epic" not in label_names:
            labels.append({"name": "epic", "value": "Ixigo Flight Automation"})
            changed = True
        if story_value and "story" not in label_names:
            labels.append({"name": "story", "value": story_value})
            changed = True

        if changed:
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            updated += 1
    return updated


def _format_duration(start_ms: int | None, stop_ms: int | None) -> str:
    if not start_ms or not stop_ms:
        return ""
    seconds = max(0, (stop_ms - start_ms) / 1000)
    if seconds >= 60:
        minutes = int(seconds // 60)
        rem = int(seconds % 60)
        return f"{minutes}m {rem}s"
    return f"{seconds:.1f}s"


def _status_class(status: str) -> str:
    return {
        "passed": "passed",
        "failed": "failed",
        "broken": "broken",
        "skipped": "skipped",
    }.get(status, "unknown")


def _generate_html_report() -> Path:
    results = []
    for path in ALLURE_RESULTS_DIR.glob("*result.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        labels = data.get("labels", [])
        feature = next(
            (label.get("value") for label in labels if label.get("name") == "feature"),
            "Ungrouped",
        )
        results.append(
            {
                "name": data.get("name", ""),
                "feature": feature,
                "status": data.get("status", "unknown"),
                "start": data.get("start") or 0,
                "stop": data.get("stop") or 0,
                "steps": data.get("steps", []),
                "attachments": data.get("attachments", []),
            }
        )

    results.sort(key=lambda item: item["start"])
    totals = {
        "total": len(results),
        "passed": sum(1 for item in results if item["status"] == "passed"),
        "failed": sum(1 for item in results if item["status"] == "failed"),
        "broken": sum(1 for item in results if item["status"] == "broken"),
        "skipped": sum(1 for item in results if item["status"] == "skipped"),
    }
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    for index, item in enumerate(results, 1):
        steps = "".join(
            "<li>"
            f"<span class='badge {_status_class(step.get('status', 'unknown'))}'>"
            f"{html.escape(step.get('status', 'unknown'))}</span> "
            f"{html.escape(step.get('name', ''))}"
            "</li>"
            for step in item["steps"]
        )
        screenshots = []
        for attachment in item["attachments"]:
            source = attachment.get("source")
            if not source:
                continue
            href = f"allure-results/{html.escape(source)}"
            screenshots.append(
                "<button class='shot' type='button' data-src='{href}' data-title='{alt}'>"
                "<img src='{href}' alt='{alt}'>"
                "<span>{alt}</span>"
                "</button>".format(
                    href=href,
                    alt=html.escape(attachment.get("name", "screenshot")),
                )
            )
        screenshot_html = (
            f"<div class='gallery'>{''.join(screenshots)}</div>" if screenshots else "-"
        )
        rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td>{html.escape(item['feature'])}</td>"
            f"<td>{html.escape(item['name'])}</td>"
            f"<td><span class='badge {_status_class(item['status'])}'>{html.escape(item['status'])}</span></td>"
            f"<td>{_format_duration(item['start'], item['stop'])}</td>"
            f"<td>{screenshot_html}</td>"
            f"<td><details><summary>Steps</summary><ol>{steps}</ol></details></td>"
            "</tr>"
        )

    report_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Ixigo BDD Automation Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f6f8fb; color: #172033; }}
    header {{ background: #1f2937; color: white; padding: 22px 28px; }}
    h1 {{ margin: 0 0 6px; font-size: 24px; }}
    .meta {{ color: #cbd5e1; font-size: 13px; }}
    .cards {{ display: flex; gap: 12px; padding: 18px 28px; flex-wrap: wrap; }}
    .card {{ background: white; border: 1px solid #d8dee8; border-radius: 6px; padding: 12px 16px; min-width: 120px; }}
    .card strong {{ display: block; font-size: 24px; margin-bottom: 2px; }}
    main {{ padding: 0 28px 28px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border: 1px solid #d8dee8; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #e5e9f0; text-align: left; vertical-align: top; font-size: 14px; }}
    th {{ background: #eef2f7; color: #334155; position: sticky; top: 0; }}
    tr:hover {{ background: #fafcff; }}
    .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; max-width: 520px; }}
    .shot {{ display: block; border: 1px solid #d8dee8; border-radius: 6px; overflow: hidden; background: #f8fafc; color: #334155; padding: 0; cursor: zoom-in; text-align: left; font: inherit; }}
    .shot:hover {{ border-color: #2563eb; box-shadow: 0 2px 8px rgba(37, 99, 235, 0.18); }}
    .shot img {{ display: block; width: 100%; aspect-ratio: 16 / 9; object-fit: cover; border-bottom: 1px solid #d8dee8; }}
    .shot span {{ display: block; padding: 6px 8px; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .badge {{ display: inline-block; border-radius: 999px; padding: 3px 8px; color: white; font-size: 12px; text-transform: uppercase; }}
    .passed {{ background: #70ad47; }}
    .failed {{ background: #d9534f; }}
    .broken {{ background: #f0ad4e; }}
    .skipped {{ background: #8a8f98; }}
    .unknown {{ background: #607d8b; }}
    a {{ color: #1d4ed8; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    details summary {{ cursor: pointer; color: #1d4ed8; }}
    ol {{ padding-left: 22px; margin: 8px 0 0; }}
    li {{ margin: 5px 0; }}
    dialog {{ width: min(1120px, 94vw); border: 0; border-radius: 8px; padding: 0; box-shadow: 0 18px 60px rgba(15, 23, 42, 0.35); }}
    dialog::backdrop {{ background: rgba(15, 23, 42, 0.72); }}
    .modal-head {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 12px 16px; border-bottom: 1px solid #d8dee8; background: #f8fafc; }}
    .modal-title {{ font-weight: 700; color: #172033; }}
    .modal-close {{ border: 1px solid #cbd5e1; background: white; border-radius: 6px; padding: 6px 10px; cursor: pointer; }}
    .modal-body {{ padding: 12px; background: #0f172a; }}
    .modal-body img {{ display: block; width: 100%; max-height: 78vh; object-fit: contain; }}
  </style>
</head>
<body>
  <header>
    <h1>Ixigo BDD Automation Report</h1>
    <div class="meta">Generated {generated_at} | Chronological execution order</div>
  </header>
  <section class="cards">
    <div class="card"><strong>{totals['total']}</strong>Total</div>
    <div class="card"><strong>{totals['passed']}</strong>Passed</div>
    <div class="card"><strong>{totals['failed']}</strong>Failed</div>
    <div class="card"><strong>{totals['broken']}</strong>Broken</div>
    <div class="card"><strong>{totals['skipped']}</strong>Skipped</div>
  </section>
  <main>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Feature</th>
          <th>Test Case</th>
          <th>Status</th>
          <th>Duration</th>
          <th>Screenshots</th>
          <th>Details</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </main>
  <dialog id="shotDialog">
    <div class="modal-head">
      <div class="modal-title" id="shotTitle">Screenshot</div>
      <button class="modal-close" type="button" id="shotClose">Close</button>
    </div>
    <div class="modal-body">
      <img id="shotPreview" alt="Screenshot preview">
    </div>
  </dialog>
  <script>
    const dialog = document.getElementById('shotDialog');
    const preview = document.getElementById('shotPreview');
    const title = document.getElementById('shotTitle');
    document.querySelectorAll('.shot').forEach((button) => {{
      button.addEventListener('click', () => {{
        preview.src = button.dataset.src;
        title.textContent = button.dataset.title || 'Screenshot';
        if (dialog.showModal) dialog.showModal();
        else dialog.setAttribute('open', 'open');
      }});
    }});
    document.getElementById('shotClose').addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', (event) => {{
      const rect = dialog.getBoundingClientRect();
      const outside = event.clientX < rect.left || event.clientX > rect.right ||
        event.clientY < rect.top || event.clientY > rect.bottom;
      if (outside) dialog.close();
    }});
  </script>
</body>
</html>
"""
    HTML_REPORT_PATH.write_text(report_html, encoding="utf-8")
    return HTML_REPORT_PATH


def _open_html_report(path: Path):
    try:
        webbrowser.open(path.resolve().as_uri())
    except Exception as exc:
        log.warning(f"Could not open HTML report: {exc}")


def _generate_and_open_allure_report():
    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_path = REPORTS_DIR / f"allure-command-{timestamp}.log"

        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"--- allure generation {time.strftime('%Y-%m-%dT%H:%M:%S')} ---\n")

            if not _wait_for_allure_results():
                log_file.write("No Allure result JSON files were found.\n")
                return

            updated = _patch_behavior_labels()
            log_file.write(f"Updated {updated} Allure result files.\n")
            html_report = _generate_html_report()
            log_file.write(f"HTML report generated: {html_report}\n")

            _open_html_report(HTML_REPORT_PATH)

            generate_command = _allure_command(
                [
                    "generate",
                    str(ALLURE_RESULTS_DIR),
                    "-o",
                    str(ALLURE_REPORT_DIR),
                    "--clean",
                ]
            )
            if not generate_command:
                message = _allure_install_message()
                log_file.write(message + "\n")
                log.warning(message)
                return

            try:
                generate = subprocess.run(
                    generate_command,
                    cwd=str(PROJECT_ROOT),
                    env=_allure_env(),
                    stdout=log_file,
                    stderr=log_file,
                    text=True,
                )
            except OSError as exc:
                log_file.write(f"Could not start Allure commandline: {exc}\n")
                log.warning(f"Could not start Allure commandline: {exc}")
                return

            if generate.returncode != 0:
                log_file.write(f"Allure generate failed with {generate.returncode}.\n")
                return

        open_command = _allure_command(["open", str(ALLURE_REPORT_DIR)])
        if open_command:
            try:
                subprocess.Popen(
                    open_command,
                    cwd=str(PROJECT_ROOT),
                    env=_allure_env(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except OSError as exc:
                log.warning(f"Could not open Allure report: {exc}")
    except Exception as exc:
        log.exception(f"Report generation failed after Behave completed: {exc}")


def _build_driver():
    """Create a browser driver using the configured browser settings."""
    browser_name = get("browser", "name", fallback="edge").lower()
    headless = get("browser", "headless", fallback="false").lower() == "true"
    all_candidates = [
        ("chrome", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        ("chrome", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        ("edge", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        ("edge", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ]
    preferred = [candidate for candidate in all_candidates if candidate[0] == browser_name]
    fallback = [candidate for candidate in all_candidates if candidate[0] != browser_name]
    candidates = preferred + fallback

    for name, path in candidates:
        if not os.path.exists(path):
            continue
        try:
            if name == "chrome":
                options = ChromeOptions()
                options.binary_location = path
                options.add_argument("--start-maximized")
                options.add_argument("--disable-notifications")
                if headless:
                    options.add_argument("--headless=new")
                driver = webdriver.Chrome(service=Service(), options=options)
            else:
                options = EdgeOptions()
                options.binary_location = path
                options.add_argument("--start-maximized")
                options.add_argument("--disable-notifications")
                if headless:
                    options.add_argument("--headless=new")
                driver = webdriver.Edge(service=EdgeService(), options=options)
            driver.implicitly_wait(get_int("timeouts", "implicit_wait", fallback=2))
            log.info(f"Browser started: {driver.name}")
            return driver
        except OSError as exc:
            log.warning(f"Could not start {name} from {path}: {exc}")
            continue

    raise RuntimeError("No Chrome or Edge browser found.")


def before_all(context):
    """Initialize suite-level state."""
    _clean_report_dir(ALLURE_RESULTS_DIR)
    _clean_report_dir(ALLURE_REPORT_DIR)
    _clean_report_dir(LOGS_DIR)
    if HTML_REPORT_PATH.exists():
        HTML_REPORT_PATH.unlink()
    _clean_file_pattern(REPORTS_DIR, "allure-command*.log")
    _clean_file_pattern(REPORTS_DIR, "generate-open-allure.ps1")
    context.driver = None
    log.info("BDD suite started.")


def before_feature(context, feature):
    """Start one browser per feature file, like the Selenium ordered flows."""
    log.info(f"Starting feature: {feature.name}")
    context.driver = _build_driver()
    context.feature_driver = context.driver
    FlightSearchPage(context.driver).open_search_page()


def before_scenario(context, scenario):
    """Log scenario start while keeping the feature browser alive."""
    log.info(f"Starting scenario: {scenario.name}")
    if "isolated" in scenario.tags:
        context.driver = _build_driver()
        FlightSearchPage(context.driver).open_search_page()


def after_scenario(context, scenario):
    """Capture the final scenario state without closing the feature browser."""
    if getattr(context, "driver", None):
        screenshot_name = f"{scenario.name.replace(' ', '_')}_{scenario.status.name}"
        path = take_screenshot(context.driver, name=screenshot_name)
        if scenario.status == Status.failed:
            log.error(f"BDD failure screenshot saved: {path}")
        else:
            log.info(f"BDD scenario screenshot saved: {path}")
    if "isolated" in scenario.tags and getattr(context, "driver", None):
        log.info(f"Closing isolated browser after scenario: {scenario.name}")
        context.driver.quit()
        context.driver = getattr(context, "feature_driver", None)


def after_feature(context, feature):
    """Close the feature browser after all scenarios in that feature finish."""
    if getattr(context, "driver", None):
        log.info(f"Closing browser after feature: {feature.name}")
        context.driver.quit()
        context.driver = None
        context.feature_driver = None


def after_all(context):
    """Generate and open the Allure report after Allure results are flushed."""
    log.info("BDD suite finished.")
    report_thread = threading.Thread(
        target=_generate_and_open_allure_report,
        name="allure-report-generator",
        daemon=False,
    )
    report_thread.start()
    log.info(
        "Reports will open shortly. HTML works without extra tools; Allure opens when "
        f"Allure commandline is installed. Logs: {REPORTS_DIR / 'allure-command-*.log'}"
    )
