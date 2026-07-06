# Design notes

Short notes on the choices, mostly for myself.

**Why signals are injected instead of simulated.** On a HiL bench the test
stimulates the unit under test; the physics comes from the simulator, not the
test. I kept the same shape: tests set voltages/temperatures directly and the
"BMS" logic reacts. Modelling real cell behaviour would be a different project.

**Why faults latch.** First version cleared the fault as soon as the value
came back into range. That is wrong for a BMS: a cell that touched 4.4 V is an
event someone must look at, not a condition that expires. So `ProtectionMonitor`
keeps faults until `clear_faults()`, and the latching behaviour has its own
scenario and test.

**Why behave and pytest both.** pytest for the low-level checks (boundaries,
clamping, invalid transitions), Gherkin for the behaviours someone non-technical
should be able to read. That split matches how BDD is used in test teams.

**Boundary convention.** Limits trip on >= / <= (4.25 V exactly is a fault).
Both sides of each boundary are in the scenario outline examples.
