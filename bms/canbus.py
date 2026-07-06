"""Publish the pack state on a virtual CAN bus and read it back.

A real bench does not call the BMS methods directly; it watches the BMS on the
vehicle CAN bus. This module does the same in miniature. It turns the pack,
protection and charging state into CAN frames defined by ``can/bms.dbc``, puts
them on python-can's in-process virtual bus, and decodes them again with
cantools.

Everything here is synchronous. There is no background thread: you publish, then
you read. That is enough to exercise the encode and decode path, which is the
part a bench actually depends on.
"""

from pathlib import Path

import can
import cantools

DBC_PATH = Path(__file__).resolve().parent.parent / "can" / "bms.dbc"
CHANNEL = "bms"

# Charging session state name -> the value used in the DBC.
_CHARGING_VALUES = {
    "UNPLUGGED": 0,
    "PLUGGED": 1,
    "HANDSHAKE": 2,
    "CHARGING": 3,
    "COMPLETE": 4,
    "FAULTED": 5,
}


def load_database():
    """Load the DBC once so callers can share it."""
    return cantools.database.load_file(DBC_PATH)


class BmsCanPublisher:
    """Encodes BMS state and sends it as CAN frames on the given bus."""

    def __init__(self, bus, db=None):
        self.bus = bus
        self.db = db or load_database()

    def publish_pack_status(self, pack):
        message = self.db.get_message_by_name("PackStatus")
        data = message.encode({
            "SoC_percent": round(pack.soc_percent),
            "PackCurrent_A": pack.current_a,
            "MinCellVoltage_V": pack.min_cell_voltage,
            "MaxCellVoltage_V": pack.max_cell_voltage,
        })
        self._send(message.frame_id, data)

    def publish_faults(self, monitor):
        message = self.db.get_message_by_name("FaultFlags")
        active = monitor.active_faults
        data = message.encode({
            "Fault_OVP": int("OVP" in active),
            "Fault_UVP": int("UVP" in active),
            "Fault_OTP": int("OTP" in active),
            "Fault_OCP": int("OCP" in active),
            "Fault_HVIL": int("HVIL" in active),
            "ContactorsClosed": int(monitor.contactors_closed),
        })
        self._send(message.frame_id, data)

    def publish_charging_state(self, session):
        message = self.db.get_message_by_name("ChargingStatus")
        data = message.encode({"ChargingState": _CHARGING_VALUES[session.state]})
        self._send(message.frame_id, data)

    def _send(self, frame_id, data):
        self.bus.send(can.Message(arbitration_id=frame_id, data=data, is_extended_id=False))


class BmsCanReader:
    """Reads one frame off the bus and decodes it with the DBC."""

    def __init__(self, bus, db=None):
        self.bus = bus
        self.db = db or load_database()

    def read(self, timeout=1.0):
        """Return (message_name, decoded_signals) or None if nothing arrived."""
        frame = self.bus.recv(timeout=timeout)
        if frame is None:
            return None
        message = self.db.get_message_by_frame_id(frame.arbitration_id)
        return message.name, self.db.decode_message(frame.arbitration_id, frame.data)
