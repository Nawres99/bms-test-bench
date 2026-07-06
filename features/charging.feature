Feature: Charging session behaviour
  A charging session must survive the ugly cases: cables pulled under load,
  handshakes that never answer, and recovery afterwards.

  Scenario: Normal charge from plug to complete
    Given an unplugged vehicle
    When the cable is plugged in
    And the handshake succeeds
    And charging runs to completion
    And the cable is unplugged
    Then the session state is "UNPLUGGED"

  Scenario: Cable removed under load
    Given a vehicle that is charging
    When the cable is unplugged
    Then the session state is "FAULTED"
    And the fault reason is "cable removed under load"

  Scenario: Recovery after a fault
    Given a vehicle that is charging
    When the cable is unplugged
    And the fault is cleared
    And the cable is plugged in
    And the handshake succeeds
    Then the session state is "CHARGING"

  Scenario: Handshake timeout
    Given an unplugged vehicle
    When the cable is plugged in
    And the handshake times out
    Then the session state is "FAULTED"
    And the fault reason is "handshake timeout"
