from unittest import mock

import pytest

from lutronbond import lutron
from lutronbond import synthesizer


@pytest.fixture
def mock_bus():
    with mock.patch('lutronbond.eventbus.get_bus') as mock_get_bus:
        bus = mock.Mock()
        mock_get_bus.return_value = bus
        yield bus


@pytest.fixture
def synth():
    # Return a fresh instance for each test
    return synthesizer.EventSynthesizer()


@pytest.fixture
def mock_time():
    with mock.patch('time.time') as m:
        m.return_value = 1000.0
        yield m


def create_event(
    operation=lutron.Operation.DEVICE,
    action=lutron.DeviceAction.PRESS,
    device=1,
    component=lutron.Component.BTN_1,
    bridge="10.0.0.10"
) -> lutron.LutronEvent:
    return lutron.LutronEvent(
        operation=operation,
        device=device,
        component=component,
        action=action,
        parameters="",
        bridge=bridge
    )


def test_ignores_non_device_events(synth, mock_bus, mock_time):
    event = create_event(operation=lutron.Operation.OUTPUT, action=lutron.OutputAction.SET_LEVEL)
    synth.process(event)
    
    # Should not update state
    assert len(synth.last_press_times) == 0
    # Should not publish anything
    mock_bus.pub.assert_not_called()


def test_ignores_non_press_events(synth, mock_bus, mock_time):
    event = create_event(action=lutron.DeviceAction.RELEASE)
    synth.process(event)
    
    assert len(synth.last_press_times) == 0
    mock_bus.pub.assert_not_called()


def test_first_press_records_timestamp(synth, mock_bus, mock_time):
    event = create_event()
    synth.process(event)
    
    key = "10.0.0.10:1:BTN_1"
    assert synth.last_press_times[key] == 1000.0
    mock_bus.pub.assert_not_called()


def test_second_press_within_window_publishes_dbltap(synth, mock_bus, mock_time):
    event = create_event()
    
    # First press at 1000.0
    synth.process(event)
    
    # Second press at 1000.2 (within 0.4 window)
    mock_time.return_value = 1000.2
    synth.process(event)
    
    key = "10.0.0.10:1:BTN_1"
    # Should reset timestamp
    assert synth.last_press_times[key] == 0.0
    
    # Should publish DBLTAP event
    mock_bus.pub.assert_called_once()
    args, _ = mock_bus.pub.call_args
    pub_key, pub_event = args
    
    assert pub_key == "10.0.0.10:1"
    assert pub_event.operation == lutron.Operation.DEVICE
    assert pub_event.action == lutron.DeviceAction.DBLTAP
    assert pub_event.device == 1
    assert pub_event.component == lutron.Component.BTN_1


def test_second_press_outside_window_updates_timestamp(synth, mock_bus, mock_time):
    event = create_event()
    
    # First press at 1000.0
    synth.process(event)
    
    # Second press at 1000.5 (outside 0.4 window)
    mock_time.return_value = 1000.5
    synth.process(event)
    
    key = "10.0.0.10:1:BTN_1"
    # Should update timestamp
    assert synth.last_press_times[key] == 1000.5
    
    # Should NOT publish DBLTAP
    mock_bus.pub.assert_not_called()


def test_different_buttons_tracked_independently(synth, mock_bus, mock_time):
    event_btn1 = create_event(component=lutron.Component.BTN_1)
    event_btn2 = create_event(component=lutron.Component.BTN_2)
    
    # Press btn1 at 1000.0
    synth.process(event_btn1)
    
    # Press btn2 at 1000.2
    mock_time.return_value = 1000.2
    synth.process(event_btn2)
    
    # Neither should publish
    mock_bus.pub.assert_not_called()
    
    # Both should have their own timestamps
    assert synth.last_press_times["10.0.0.10:1:BTN_1"] == 1000.0
    assert synth.last_press_times["10.0.0.10:1:BTN_2"] == 1000.2
    
    # Press btn1 again at 1000.3 (within window for btn1)
    mock_time.return_value = 1000.3
    synth.process(event_btn1)
    
    # btn1 should publish DBLTAP
    mock_bus.pub.assert_called_once()
    args, _ = mock_bus.pub.call_args
    _, pub_event = args
    assert pub_event.component == lutron.Component.BTN_1
    assert pub_event.action == lutron.DeviceAction.DBLTAP


def test_get_synthesizer_caches_instance():
    # Clear cache if any
    synthesizer.get_synthesizer.cache_clear()
    
    synth1 = synthesizer.get_synthesizer()
    synth2 = synthesizer.get_synthesizer()
    
    assert synth1 is synth2
