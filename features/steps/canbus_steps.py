import can
from behave import given, then, when

from bms.canbus import CHANNEL, BmsCanPublisher, BmsCanReader


@given("a virtual CAN bus")
def step_virtual_bus(context):
    # One bus to publish, one to read, on the same in-process virtual channel.
    context.can_sender = can.Bus(interface="virtual", channel=CHANNEL)
    context.can_reader = can.Bus(interface="virtual", channel=CHANNEL)
    context.publisher = BmsCanPublisher(context.can_sender)
    context.reader = BmsCanReader(context.can_reader)


@when("the BMS publishes its fault flags")
def step_publish_faults(context):
    context.publisher.publish_faults(context.monitor)
    context.decoded_name, context.decoded = context.reader.read()


@when("the BMS publishes its pack status")
def step_publish_status(context):
    context.publisher.publish_pack_status(context.pack)
    context.decoded_name, context.decoded = context.reader.read()


@when("the BMS publishes its charging state")
def step_publish_charging(context):
    context.publisher.publish_charging_state(context.session)
    context.decoded_name, context.decoded = context.reader.read()


@then('the decoded frame is "{name}"')
def step_decoded_frame(context, name):
    assert context.decoded_name == name, f"decoded {context.decoded_name}, expected {name}"


@then('the "{flag}" flag is set')
def step_flag_set(context, flag):
    assert context.decoded[f"Fault_{flag}"] == 1


@then('the "{flag}" flag is clear')
def step_flag_clear(context, flag):
    assert context.decoded[f"Fault_{flag}"] == 0


@then("the contactors are reported open")
def step_contactors_reported_open(context):
    assert context.decoded["ContactorsClosed"] == 0


@then("the reported max cell voltage is {voltage:g} V")
def step_reported_max_voltage(context, voltage):
    assert abs(context.decoded["MaxCellVoltage_V"] - voltage) < 0.001


@then('the charging state on the bus is "{state}"')
def step_charging_state_on_bus(context, state):
    assert str(context.decoded["ChargingState"]) == state
