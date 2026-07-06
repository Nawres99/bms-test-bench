import pytest

from bms.model import BatteryPack
from bms.protection import (
    ProtectionMonitor,
    FAULT_OVP,
    FAULT_UVP,
    FAULT_OTP,
    FAULT_OCP,
    FAULT_HVIL,
)


def make_pack():
    return BatteryPack.with_cells(8, voltage_v=3.7, temperature_c=25.0)


@pytest.mark.parametrize(
    "stimulate, expected_fault",
    [
        (lambda p: p.set_cell_voltage(3, 4.30), FAULT_OVP),
        (lambda p: p.set_cell_voltage(3, 4.25), FAULT_OVP),  # boundary: >= trips
        (lambda p: p.set_cell_voltage(0, 2.40), FAULT_UVP),
        (lambda p: p.set_cell_temperature(5, 65.0), FAULT_OTP),
        (lambda p: setattr(p, "current_a", 250.0), FAULT_OCP),
        (lambda p: setattr(p, "current_a", -250.0), FAULT_OCP),  # discharge too
    ],
)
def test_each_limit_trips_its_fault(stimulate, expected_fault):
    pack = make_pack()
    monitor = ProtectionMonitor()
    stimulate(pack)
    faults = monitor.check(pack)
    assert faults == [expected_fault]
    assert monitor.in_safe_state
    assert not monitor.contactors_closed


def test_healthy_pack_raises_no_fault():
    monitor = ProtectionMonitor()
    assert monitor.check(make_pack()) == []
    assert monitor.contactors_closed


def test_hvil_open_trips_fault():
    monitor = ProtectionMonitor(hvil_closed=False)
    assert monitor.check(make_pack()) == [FAULT_HVIL]


def test_fault_stays_latched_after_value_recovers():
    pack = make_pack()
    monitor = ProtectionMonitor()
    pack.set_cell_voltage(1, 4.40)
    monitor.check(pack)
    pack.set_cell_voltage(1, 3.7)  # value back to normal
    monitor.check(pack)
    assert monitor.active_faults == [FAULT_OVP]  # still latched
    assert monitor.in_safe_state


def test_clear_faults_closes_contactors_again():
    pack = make_pack()
    monitor = ProtectionMonitor()
    pack.set_cell_voltage(1, 4.40)
    monitor.check(pack)
    monitor.clear_faults()
    assert monitor.active_faults == []
    assert monitor.contactors_closed


def test_simultaneous_faults_are_all_reported():
    pack = make_pack()
    monitor = ProtectionMonitor()
    pack.set_cell_voltage(0, 4.40)
    pack.set_cell_temperature(0, 70.0)
    faults = monitor.check(pack)
    assert set(faults) == {FAULT_OVP, FAULT_OTP}
