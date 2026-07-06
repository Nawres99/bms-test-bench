"""Charging session state machine.

The states follow the rough shape of a charging session as ISO 15118 sees it:

    UNPLUGGED -> PLUGGED -> HANDSHAKE -> CHARGING -> COMPLETE

FAULTED is reached from a handshake timeout or from pulling the cable under
load, and must be cleared before a new session can start. This is a
simplification: the real protocol has many more message exchanges.
"""

UNPLUGGED = "UNPLUGGED"
PLUGGED = "PLUGGED"
HANDSHAKE = "HANDSHAKE"
CHARGING = "CHARGING"
COMPLETE = "COMPLETE"
FAULTED = "FAULTED"


class InvalidTransition(Exception):
    pass


class ChargingSession:
    def __init__(self):
        self.state = UNPLUGGED
        self.fault_reason = None
        self.events = []

    def _go(self, new_state, reason=None):
        self.events.append((self.state, new_state, reason))
        self.state = new_state
        self.fault_reason = reason if new_state == FAULTED else None

    def _require(self, *states):
        if self.state not in states:
            raise InvalidTransition(
                f"cannot do this from {self.state}, expected one of {states}"
            )

    def plug_in(self):
        self._require(UNPLUGGED)
        self._go(PLUGGED)

    def begin_handshake(self):
        self._require(PLUGGED)
        self._go(HANDSHAKE)

    def handshake_ok(self):
        self._require(HANDSHAKE)
        self._go(CHARGING)

    def handshake_timeout(self):
        self._require(HANDSHAKE)
        self._go(FAULTED, reason="handshake timeout")

    def complete(self):
        self._require(CHARGING)
        self._go(COMPLETE)

    def unplug(self):
        # pulling the cable under load is a fault; otherwise a normal end
        if self.state == CHARGING:
            self._go(FAULTED, reason="cable removed under load")
        elif self.state in (PLUGGED, HANDSHAKE, COMPLETE):
            self._go(UNPLUGGED)
        else:
            raise InvalidTransition(f"cannot unplug from {self.state}")

    def clear_fault(self):
        self._require(FAULTED)
        self._go(UNPLUGGED)
