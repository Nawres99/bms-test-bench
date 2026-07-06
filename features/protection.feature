Feature: Battery protection
  The BMS must reach a safe state when any cell leaves its safe window,
  and the fault must stay latched until an operator clears it.

  Background:
    Given a battery pack of 8 cells at 3.7 V and 25 C

  Scenario: Over-voltage opens the contactors
    When cell 3 rises to 4.30 V
    Then the "OVP" fault is raised
    And the contactors are open

  Scenario: Over-temperature during discharge
    Given the pack is discharging at 150 A
    When cell 5 heats up to 65 C
    Then the "OTP" fault is raised
    And the pack is in safe state

  Scenario: Broken interlock loop shuts down high voltage
    When the HVIL loop opens
    Then the "HVIL" fault is raised
    And the contactors are open

  Scenario: A fault stays latched after the value recovers
    When cell 1 rises to 4.40 V
    And cell 1 returns to 3.70 V
    Then the "OVP" fault is still active
    And the pack is in safe state

  Scenario Outline: Cell voltage limits
    When cell 0 is set to <voltage> V
    Then the raised faults are "<faults>"

    Examples:
      | voltage | faults |
      | 4.30    | OVP    |
      | 4.25    | OVP    |
      | 2.40    | UVP    |
      | 2.50    | UVP    |
      | 4.00    | none   |
      | 3.00    | none   |
