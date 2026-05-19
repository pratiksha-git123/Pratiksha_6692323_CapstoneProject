# Ixigo Flight Booking BDD Automation

BDD version of the ixigo flight automation project built with Behave,
Selenium WebDriver, and the Page Object Model.

## Project Structure

```text
Ixigo_Flight_Automation_BDD/
|-- behave.ini
|-- requirements.txt
|-- config/
|-- data/
|-- pages/
|-- utils/
`-- features/
    |-- environment.py
    |-- combined_flow.feature
    |-- e2e_full_booking.feature
    `-- steps/
        |-- combined_flow_steps/
        |   `-- combined_steps.py
        `-- e2e_full_booking_steps/
            `-- e2e_steps.py
```

## Design

- Feature files describe the user flow in plain language.
- Step definitions call Page Objects so Selenium locators stay out of the Gherkin files.
- Step definitions are split into two folders: one for the combined flow and one for the full E2E booking flow.
- `behave.ini` enables nested step modules so Behave loads those two step folders directly.
- The browser stays alive for a feature so the BDD execution follows the Selenium-style ordered flow.
- Isolated negative scenarios can still use their own browser when tagged for isolation.
- The combined flow uses the same fixed routes and dates as the Selenium combined test.
- The full E2E flow uses a random route from `data/flight_routes.csv`.
- Login mobile data is read from `data/login_data.csv`.
- Traveller details are read from `data/traveller_data.csv`.
- Combined scenarios cover search controls, search results, filter/sort, negative route validation, and booking-page navigation.
- The full E2E scenario covers login, random route search, filter/sort, booking, traveller details, add-ons, optional seat selection, and payment.
- The full E2E scenario submits the configured mobile number and waits for manual OTP entry, matching the Selenium E2E flow.

## Run

```bash
pip install -r requirements.txt
python -m behave
```

The default `python -m behave` command writes fresh report files, creates
`reports/report.html`, and opens that local HTML report automatically.

If the Allure commandline tool is installed on the system, the same command also
generates `reports/allure-report` and opens the Allure server automatically.
The Python package `allure-behave` only creates Allure result files; the separate
Allure commandline tool is required to generate and serve the interactive Allure UI.

On Windows with npm installed:

```bash
npm install -g allure-commandline
```

After installation, make sure this works from a new terminal:

```bash
allure --version
```

Useful optional commands:

```bash
python -m behave --dry-run
python -m behave --tags=@search
python -m behave --tags=@e2e
python -m behave --tags=@search -f html-pretty -o reports/behave-report.html --junit --junit-directory reports/junit
```

## Reports

The default Behave command creates:

- `reports/report.html` for submission-friendly HTML output with screenshots
- `reports/allure-results/` with Allure result JSON and screenshots
- `reports/allure-report/` when the Allure commandline tool is available
- `reports/allure-command-*.log` with report generation details

If Allure is not installed, the test run still passes and the local HTML report
still opens. The log will explain that only the Allure UI generation was skipped.
