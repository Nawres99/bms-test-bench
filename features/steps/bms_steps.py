from behave import given, when, then

from bms.model import BatteryPack
from bms.protection import ProtectionMonitor
from bms.balancing import cells_to_balance
from bms.charging import ChargingSession


# --- battery pack / protection ---------------------------------------------

@given("a battery pack of {count:d} cells at {voltage:g} V and {temp:g} C")
def step_make_pack(context, count, voltage, temp):
    context.pack = BatteryPack.with_cells(count, voltage_v=voltage, temperature_c=temp)
    context.monitor = ProtectionMonitor()
    context.raised = []


@given("the pack is discharging at {amps:g} A")
def step_discharge(context, amps):
    context.pack.current_a = -amps


@when("cell {index:d} rises to {voltage:g} V")
@when("cell {index:d} returns to {voltage:g} V")
@when("cell {index:d} is set to {voltage:g} V")
def step_set_voltage(context, index, voltage):
    context.pack.set_cell_voltage(index, voltage)
    context.raised = context.monitor.check(context.pack)


@when("cell {index:d} heats up to {temp:g} C")
def step_set_temperature(context, index, temp):
    context.pack.set_cell_temperature(index, temp)
    context.raised = context.monitor.check(context.pack)


@when("the HVIL loop opens")
def step_open_hvil(context):
    context.monitor.hvil_closed = False
    context.raised = context.monitor.check(context.pack)


@then('the "{fault}" fault is raised')
def step_fault_raised(context, fault):
    assert fault in context.raised, f"expected {fault} in {context.raised}"


@then('the "{fault}" fault is still active')
def step_fault_latched(context, fault):
    assert fault in context.monitor.active_faults


@then('the raised faults are "{faults}"')
def step_faults_are(context, faults):
    expected = [] if faults == "none" else [f.strip() for f in faults.split(",")]
    assert context.raised == expected, f"expected {expected}, got {context.raised}"


@then("the contactors are open")
def step_contactors_open(context):
    assert not context.monitor.contactors_closed


@then("the pack is in safe state")
def step_safe_state(context):
    assert context.monitor.in_safe_state


# --- balancing --------------------------------------------------------------

@then('cells selected for balancing are "{indexes}"')
def step_balancing_cells(context, indexes):
    expected = [] if indexes == "none" else [int(i) for i in indexes.split(",")]
    assert cells_to_balance(context.pack) == expected


# --- charging session -------------------------------------------------------

@given("an unplugged vehicle")
def step_unplugged(context):
    context.session = ChargingSession()


@given("a vehicle that is charging")
def step_charging_vehicle(context):
    context.session = ChargingSession()
    context.session.plug_in()
    context.session.begin_handshake()
    context.session.handshake_ok()


@when("the cable is plugged in")
def step_plug(context):
    context.session.plug_in()


@when("the handshake succeeds")
def step_handshake_ok(context):
    context.session.begin_handshake()
    context.session.handshake_ok()


@when("the handshake times out")
def step_handshake_timeout(context):
    context.session.begin_handshake()
    context.session.handshake_timeout()


@when("charging runs to completion")
def step_complete(context):
    context.session.complete()


@when("the cable is unplugged")
def step_unplug(context):
    context.session.unplug()


@when("the fault is cleared")
def step_clear_fault(context):
    context.session.clear_fault()


@then('the session state is "{state}"')
def step_session_state(context, state):
    assert context.session.state == state, f"state is {context.session.state}"


@then('the fault reason is "{reason}"')
def step_fault_reason(context, reason):
    assert context.session.fault_reason == reason
