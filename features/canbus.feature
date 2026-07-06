Feature: BMS state on the CAN bus
  The pack publishes its state as CAN frames. Decoding those frames should give
  back the same faults, measurements and charging state, so a bench reading the
  bus sees what the BMS sees.

  Background:
    Given a virtual CAN bus

  Scenario: A protection fault shows up in the fault frame
    Given a battery pack of 8 cells at 3.7 V and 25 C
    When cell 2 rises to 4.40 V
    And the BMS publishes its fault flags
    Then the decoded frame is "FaultFlags"
    And the "OVP" flag is set
    And the "UVP" flag is clear
    And the contactors are reported open

  Scenario: Pack status carries the measured values
    Given a battery pack of 8 cells at 3.90 V and 25 C
    When the BMS publishes its pack status
    Then the decoded frame is "PackStatus"
    And the reported max cell voltage is 3.90 V

  Scenario: Charging state is published by name
    Given a vehicle that is charging
    When the BMS publishes its charging state
    Then the decoded frame is "ChargingStatus"
    And the charging state on the bus is "CHARGING"
