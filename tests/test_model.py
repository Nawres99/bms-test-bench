from bms.model import BatteryPack


def test_soc_increases_while_charging():
    pack = BatteryPack.with_cells(8, capacity_ah=50.0, soc_percent=50.0)
    pack.current_a = 25.0  # charging
    pack.step(3600)  # one hour
    assert pack.soc_percent == 100.0  # 25 Ah into 50 Ah pack = +50%


def test_soc_decreases_while_discharging():
    pack = BatteryPack.with_cells(8, capacity_ah=50.0, soc_percent=50.0)
    pack.current_a = -10.0
    pack.step(1800)  # half an hour -> -5 Ah -> -10%
    assert round(pack.soc_percent, 1) == 40.0


def test_soc_is_clamped_between_0_and_100():
    pack = BatteryPack.with_cells(4, capacity_ah=10.0, soc_percent=95.0)
    pack.current_a = 50.0
    pack.step(3600)
    assert pack.soc_percent == 100.0
    pack.current_a = -50.0
    pack.step(3 * 3600)
    assert pack.soc_percent == 0.0


def test_min_max_cell_readings():
    pack = BatteryPack.with_cells(4)
    pack.set_cell_voltage(2, 4.1)
    pack.set_cell_voltage(0, 3.2)
    pack.set_cell_temperature(1, 41.0)
    assert pack.max_cell_voltage == 4.1
    assert pack.min_cell_voltage == 3.2
    assert pack.max_cell_temperature == 41.0
