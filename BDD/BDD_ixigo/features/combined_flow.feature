Feature: Ixigo combined flow
  As a traveler
  I want the Behave suite to match the Selenium combined flow
  So that only the framework changes, not the tested behavior

  @search
  Scenario: Open ixigo page
    Given the traveler opens the ixigo flights page
    Then the ixigo flights page should be loaded

  @search
  Scenario: Page elements are present
    Then the main search controls should be visible

  @search
  Scenario: Search BOM to BLR flights
    Given the traveler opens the ixigo flights page
    When the traveler searches from "Mumbai" "BOM" to "Bengaluru" "BLR" on "2026-06-10"
    Then matching flight results should be displayed
    And at least one visible flight should remain

  @search
  Scenario: Flight count and book buttons are visible
    Then at least one visible flight should remain
    And at least two visible book buttons should be displayed

  @search
  Scenario: Apply nonstop filter and sort by price
    When the traveler applies the nonstop filter
    And the traveler sorts results by lowest price
    Then at least one visible flight should remain
    And visible prices should be sorted by lowest price when available

  @search
  Scenario: Print flight results
    When the traveler prints the visible flight results
    Then at least one visible flight should remain

  @negative @isolated
  Scenario: Same source and destination should not navigate to results
    Given the traveler opens the ixigo flights page
    When the traveler searches from "Mumbai" "BOM" to "Mumbai" "BOM" on "2026-06-04"
    Then the route "bom-bom" should not be accepted

  @negative @isolated
  Scenario: Search without destination should not navigate to results
    Given the traveler opens the ixigo flights page
    When the traveler searches with source "Mumbai" "BOM" and no destination
    Then the traveler should remain off the flight results page

  @booking @isolated
  Scenario: Booking flow reaches traveller details
    Given the traveler opens the ixigo flights page
    When the traveler searches from "Mumbai" "BOM" to "Bengaluru" "BLR" on "2026-06-04"
    Then matching flight results should be displayed
    When the traveler applies the nonstop filter
    And the traveler sorts results by lowest price
    Then at least one visible flight should remain
    When the traveler books the first visible flight
    Then the booking page should be displayed
    When the traveler declines free cancellation if available
    Then the booking page should be displayed
