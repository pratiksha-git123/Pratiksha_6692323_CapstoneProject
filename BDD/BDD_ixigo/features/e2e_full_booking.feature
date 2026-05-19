Feature: Ixigo full end-to-end booking
  As a traveler
  I want the BDD suite to follow the same Selenium E2E checkpoints
  So that Allure shows the same flow with Behave scenarios

  @e2e
  Scenario: Open site
    Given the traveler opens the ixigo flights page
    Then the ixigo flights page should be loaded

  @e2e
  Scenario: Login
    When the traveler logs in using mobile row 1 from CSV

  @e2e @search
  Scenario: Search flights
    Given the traveler opens the ixigo flights page
    When the traveler searches using a random route from CSV
    Then matching flight results should be displayed

  @e2e @search
  Scenario: Apply nonstop filter
    When the traveler applies the nonstop filter
    Then at least one visible flight should remain

  @e2e @search
  Scenario: Sort by price
    When the traveler sorts results by lowest price
    Then at least one visible flight should remain

  @e2e @search
  Scenario: Print results
    When the traveler prints the visible flight results
    Then at least one visible flight should remain

  @e2e @booking
  Scenario: Click book
    When the traveler books the first visible flight

  @e2e @booking
  Scenario: Booking page
    Then the booking page should be displayed

  @e2e @booking
  Scenario: Decline cancellation
    When the traveler declines free cancellation

  @e2e @booking
  Scenario: Fill traveller
    When the traveler fills traveller details using row 1 from CSV

  @e2e @booking
  Scenario: Continue and confirm
    When the traveler continues and confirms traveller details

  @e2e @payment
  Scenario: Add-ons page
    Then the add-ons page should be displayed

  @e2e @payment
  Scenario: Select seat
    When the traveler selects a seat if available

  @e2e @payment
  Scenario: Skip to payment
    When the traveler skips to payment

  @e2e @payment
  Scenario: Payment page
    Then the payment page should be displayed
