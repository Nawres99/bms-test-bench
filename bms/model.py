"""Simplified battery pack model.

This is a simulation for test practice, not an electrochemical model.
Cell values are loosely based on a generic NMC cell (3.0 - 4.2 V working range).
Voltages and temperatures are set directly by the tests, the same way a HiL
bench injects signals into the unit under test.
"""

from dataclasses import dataclass, field


@dataclass
class Cell:
    voltage_v: float = 3.7
    temperature_c: float = 25.0


@dataclass
class BatteryPack:
    cells: list = field(default_factory=list)
    capacity_ah: float = 50.0
    soc_percent: float = 50.0
    # positive current = charging, negative = discharging
    current_a: float = 0.0

    @classmethod
    def with_cells(cls, count, voltage_v=3.7, temperature_c=25.0, **kwargs):
        cells = [Cell(voltage_v, temperature_c) for _ in range(count)]
        return cls(cells=cells, **kwargs)

    def step(self, seconds):
        """Advance the simulation by `seconds`, updating SoC by coulomb counting."""
        delta_ah = self.current_a * seconds / 3600.0
        self.soc_percent += delta_ah / self.capacity_ah * 100.0
        self.soc_percent = min(100.0, max(0.0, self.soc_percent))

    def set_cell_voltage(self, index, voltage_v):
        self.cells[index].voltage_v = voltage_v

    def set_cell_temperature(self, index, temperature_c):
        self.cells[index].temperature_c = temperature_c

    @property
    def min_cell_voltage(self):
        return min(c.voltage_v for c in self.cells)

    @property
    def max_cell_voltage(self):
        return max(c.voltage_v for c in self.cells)

    @property
    def max_cell_temperature(self):
        return max(c.temperature_c for c in self.cells)
