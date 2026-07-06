"""Passive cell balancing decision logic.

Passive balancing bleeds the highest cells through a resistor until the pack
is even again. The decision here is the simple version: any cell more than
BALANCE_THRESHOLD_V above the lowest cell should balance.
"""

BALANCE_THRESHOLD_V = 0.010  # 10 mV


def cells_to_balance(pack):
    """Return the indexes of cells that should bleed through their resistor."""
    lowest = pack.min_cell_voltage
    return [
        i for i, cell in enumerate(pack.cells)
        if cell.voltage_v - lowest > BALANCE_THRESHOLD_V
    ]
