"""Protection checks a real BMS runs continuously.

When any check trips, the monitor enters the safe state: contactors open and
the fault stays latched until it is explicitly cleared, which is how a real
BMS behaves (a fault must not silently disappear when the value recovers).
"""

from dataclasses import dataclass, field

FAULT_OVP = "OVP"    # cell over-voltage
FAULT_UVP = "UVP"    # cell under-voltage
FAULT_OTP = "OTP"    # over-temperature
FAULT_OCP = "OCP"    # over-current
FAULT_HVIL = "HVIL"  # interlock loop open


@dataclass
class Limits:
    cell_over_voltage_v: float = 4.25
    cell_under_voltage_v: float = 2.50
    over_temperature_c: float = 60.0
    over_current_a: float = 200.0


@dataclass
class ProtectionMonitor:
    limits: Limits = field(default_factory=Limits)
    hvil_closed: bool = True
    contactors_closed: bool = True
    active_faults: list = field(default_factory=list)

    def check(self, pack):
        """Run all protection checks against the pack. Returns new faults."""
        faults = []
        if pack.max_cell_voltage >= self.limits.cell_over_voltage_v:
            faults.append(FAULT_OVP)
        if pack.min_cell_voltage <= self.limits.cell_under_voltage_v:
            faults.append(FAULT_UVP)
        if pack.max_cell_temperature >= self.limits.over_temperature_c:
            faults.append(FAULT_OTP)
        if abs(pack.current_a) >= self.limits.over_current_a:
            faults.append(FAULT_OCP)
        if not self.hvil_closed:
            faults.append(FAULT_HVIL)

        new_faults = [f for f in faults if f not in self.active_faults]
        if faults:
            self._enter_safe_state(new_faults)
        return new_faults

    def _enter_safe_state(self, new_faults):
        self.contactors_closed = False
        self.active_faults.extend(new_faults)

    def clear_faults(self):
        """Operator action: clear latched faults and close contactors again."""
        self.active_faults.clear()
        self.contactors_closed = True

    @property
    def in_safe_state(self):
        return not self.contactors_closed
