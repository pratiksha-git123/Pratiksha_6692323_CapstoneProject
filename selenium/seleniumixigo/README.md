# Ixigo Flight Automation

Automated flight-booking test framework for ixigo using Selenium, pytest, and the Page Object Model.

## Before You Run

Update the login mobile number in:

```text
data/login_data.csv
```

Replace the existing sample number with your own mobile number before running the E2E login test, because the OTP will be sent to that number.

Example:

```csv
mobile
9876543210
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run Tests

Run all tests with an HTML report:

```bash
pytest --html=reports/report.html --self-contained-html
```

Run a specific test file:

```bash
pytest tests/test_02_search_flights.py --html=reports/report.html --self-contained-html
```

Run only negative tests:

```bash
pytest -m negative --html=reports/report.html --self-contained-html
```

Run only the full end-to-end flow:

```bash
pytest tests/test_06_e2e_full_booking.py --html=reports/report.html --self-contained-html
```

## Test Files

| Test File | Coverage |
|---|---|
| `test_01_open_and_load.py` | Site launch, title, search button, and form fields |
| `test_02_search_flights.py` | Flight search, random CSV route selection, URL validation, and reverse-route checks |
| `test_03_filter_and_sort.py` | Non-stop filter, price sorting, and result validation |
| `test_04_search_negative.py` | Realistic invalid-search scenarios |
| `test_05_booking_flow.py` | Book button flow, booking page, and traveller section validation |
| `test_06_e2e_full_booking.py` | Full journey from login to payment page |

## CSV Test Data

The framework uses CSV files to keep test data separate from test logic.

### 1. `data/flight_routes.csv`

Used for route selection during search tests. One row is chosen randomly at runtime.

Example:

```csv
from_city,from_code,to_city,to_code,travel_date
Mumbai,BOM,Bengaluru,BLR,2026-06-10
Delhi,DEL,Mumbai,BOM,2026-06-15
Mumbai,BOM,Delhi,DEL,2026-06-20
```

To add more searchable routes, add more rows in the same format.

### 2. `data/traveller_data.csv`

Used to fill traveller details during booking tests.

Example:

```csv
title,first_name,last_name,nationality,country_code,mobile,email,pincode,address
Mr,Rahul Kumar,Sharma,India,India (+91),9876543210,rahul.sharma@example.com,560001,42 MG Road Bengaluru
```

The booking flow currently uses the first valid row for traveller details.

### 3. `data/login_data.csv`

Used by the E2E login flow.

Example:

```csv
mobile
9876543210
```

The automation enters this number and clicks Continue automatically. You only need to enter the OTP manually.

## Viewing Results

After a run, open:

```text
reports/report.html
```

Screenshots are saved in:

```text
logs/
```

The framework also keeps the final page visible briefly before closing the browser, so the final state can be observed.
