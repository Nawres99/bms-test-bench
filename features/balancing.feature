Feature: Passive cell balancing
  Cells drift apart over time. Any cell more than 10 mV above the lowest
  one should bleed through its balancing resistor.

  Scenario: A high cell is selected for balancing
    Given a battery pack of 4 cells at 3.70 V and 25 C
    When cell 2 is set to 3.72 V
    Then cells selected for balancing are "2"

  Scenario: An even pack does not balance
    Given a battery pack of 4 cells at 3.70 V and 25 C
    Then cells selected for balancing are "none"

  Scenario: Several high cells balance together
    Given a battery pack of 6 cells at 3.70 V and 25 C
    When cell 1 is set to 3.75 V
    And cell 4 is set to 3.73 V
    Then cells selected for balancing are "1, 4"
