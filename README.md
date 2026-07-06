# bms-test-bench

I'm preparing for automotive test automation roles (BMS and EV charging validation),
and I don't have access to a real HiL bench. So I built the next best thing: a small
simulated battery pack in Python, and around it the kind of tests I would write on a
real bench — Gherkin scenarios run by behave, parameterized pytest cases, and an HTML
report generator.

The point of this repo is not the battery model (it is deliberately simple). The point
is the test engineering around it: readable scenarios, boundary cases, fault latching,
recovery paths, and reporting.

## What a real bench does vs what this repo does

| On a real HiL bench | Here |
|---|---|
| Real BMS ECU under test | `bms/` — a simplified pack model, protection logic, balancing, charging session |
| CANoe / VeriStand inject signals | Tests set cell voltages, temperatures and currents directly |
| ECU-TEST orchestrates test cases | behave (Gherkin) + pytest |
| ATX report generation | `tools/report.py` (pandas + jinja2) |
| CI integration | GitHub Actions and GitLab CI, both in this repo |
| Signals read off the vehicle CAN bus | `bms/canbus.py` + `can/bms.dbc` on python-can's virtual bus |

## What is covered

- Protection: cell over/under-voltage (OVP/UVP), over-temperature (OTP),
  over-current (OCP), HVIL open loop. Faults latch until cleared, contactors
  open on any fault — same behaviour a real BMS must show.
- Passive balancing: cells more than 10 mV above the lowest one are selected
  to bleed.
- Charging session state machine (rough shape of an ISO 15118 session):
  plug → handshake → charging → complete, with the ugly cases — cable pulled
  under load, handshake timeout, recovery after a fault.
- SoC by coulomb counting, clamped to 0–100 %.

## Running it

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

pytest -v            # unit tests
behave               # BDD scenarios
python tools/report.py samples/drive_cycle_log.csv -o report.html
```

The sample log contains a short synthetic drive-and-charge cycle with a few
deliberate limit violations, so the report has something to show.

## Status / next steps

Done since the first version:

- CAN: the pack status, fault flags and charging state are published as CAN
  frames on a virtual bus and decoded back with a DBC (`can/bms.dbc`,
  `bms/canbus.py`). It is python-can's in-process virtual bus, so there is no
  real bit rate, arbitration or timing - just the encode and decode path a
  bench relies on.

Still simplified or missing:

- The pack model has no voltage response to current (voltages are injected by
  the tests). Fine for testing the logic, wrong for physics.
- Thermal behaviour is injected, not modelled.
- No SoH estimation yet.
