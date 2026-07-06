import pytest

from bms.charging import (
    ChargingSession,
    InvalidTransition,
    UNPLUGGED,
    CHARGING,
    COMPLETE,
    FAULTED,
)


def start_charging_session():
    session = ChargingSession()
    session.plug_in()
    session.begin_handshake()
    session.handshake_ok()
    return session


def test_happy_path_to_complete():
    session = start_charging_session()
    assert session.state == CHARGING
    session.complete()
    session.unplug()
    assert session.state == UNPLUGGED


def test_unplug_under_load_is_a_fault():
    session = start_charging_session()
    session.unplug()
    assert session.state == FAULTED
    assert session.fault_reason == "cable removed under load"


def test_recovery_after_fault():
    session = start_charging_session()
    session.unplug()  # fault
    session.clear_fault()
    session.plug_in()
    session.begin_handshake()
    session.handshake_ok()
    assert session.state == CHARGING


def test_handshake_timeout_faults_the_session():
    session = ChargingSession()
    session.plug_in()
    session.begin_handshake()
    session.handshake_timeout()
    assert session.state == FAULTED
    assert session.fault_reason == "handshake timeout"


def test_cannot_charge_without_handshake():
    session = ChargingSession()
    session.plug_in()
    with pytest.raises(InvalidTransition):
        session.handshake_ok()


def test_cannot_plug_twice():
    session = ChargingSession()
    session.plug_in()
    with pytest.raises(InvalidTransition):
        session.plug_in()


def test_events_are_recorded():
    session = start_charging_session()
    session.complete()
    assert [e[1] for e in session.events] == [
        "PLUGGED",
        "HANDSHAKE",
        CHARGING,
        COMPLETE,
    ]
