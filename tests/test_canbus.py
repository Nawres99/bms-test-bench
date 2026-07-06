import can
import pytest

from bms.canbus import CHANNEL, BmsCanPublisher, BmsCanReader
from bms.charging import ChargingSession
from bms.model import BatteryPack
from bms.protection import ProtectionMonitor


@pytest.fixture
def bus_pair():
    # Two buses on the same in-process virtual channel: one publishes, one reads.
    sender = can.Bus(interface="virtual", channel=CHANNEL)
    receiver = can.Bus(interface="virtual", channel=CHANNEL)
    yield sender, receiver
    sender.shutdown()
    receiver.shutdown()


def test_fault_flags_survive_the_round_trip(bus_pair):
    sender, receiver = bus_pair
    pack = BatteryPack.with_cells(8)
    monitor = ProtectionMonitor()
    pack.set_cell_voltage(2, 4.40)  # over-voltage
    monitor.check(pack)

    BmsCanPublisher(sender).publish_faults(monitor)
    name, decoded = BmsCanReader(receiver).read()

    assert name == "FaultFlags"
    assert decoded["Fault_OVP"] == 1
    assert decoded["Fault_UVP"] == 0
    assert decoded["ContactorsClosed"] == 0  # contactors opened on the fault


def test_pack_status_values_round_trip(bus_pair):
    sender, receiver = bus_pair
    pack = BatteryPack.with_cells(8, voltage_v=3.90)
    pack.soc_percent = 74.0
    pack.current_a = -120.0

    BmsCanPublisher(sender).publish_pack_status(pack)
    name, decoded = BmsCanReader(receiver).read()

    assert name == "PackStatus"
    assert decoded["SoC_percent"] == 74
    assert decoded["PackCurrent_A"] == pytest.approx(-120.0, abs=0.1)
    assert decoded["MaxCellVoltage_V"] == pytest.approx(3.90, abs=0.001)


def test_charging_state_decodes_to_its_name(bus_pair):
    sender, receiver = bus_pair
    session = ChargingSession()
    session.plug_in()
    session.begin_handshake()
    session.handshake_timeout()  # -> FAULTED

    BmsCanPublisher(sender).publish_charging_state(session)
    name, decoded = BmsCanReader(receiver).read()

    assert name == "ChargingStatus"
    assert str(decoded["ChargingState"]) == "FAULTED"
