from collections import defaultdict

import pytest

from lutronbond import eventbus


@pytest.fixture
def bus():
    return eventbus.EventBus()


def test_eventbus(bus):
    assert isinstance(bus._bus, defaultdict)


def test_sub__adds_action(bus, mocker):
    action = mocker.Mock()
    bus.sub('test', action)

    assert 'test' in bus._bus
    assert len(bus._bus['test']) == 1


def test_sub__adds_multiple_actions(bus, mocker):
    action1 = mocker.Mock()
    action2 = mocker.Mock()
    bus.sub('test', action1)
    bus.sub('test', action2)

    assert len(bus._bus['test']) == 2


def test_pub__invalid_key(bus):
    retval = bus.pub('test')

    assert retval is None


@pytest.mark.asyncio
async def test_pub__single_action(bus, amock):
    action = amock()
    bus.sub('test', action)

    bus.pub('test')
    await bus.await_running_handlers()

    assert action.called


@pytest.mark.asyncio
async def test_pub__multiple_actions(bus, amock):
    action1 = amock()
    action2 = amock()
    bus.sub('test', action1)
    bus.sub('test', action2)

    bus.pub('test')
    await bus.await_running_handlers()

    assert action1.called
    assert action2.called


@pytest.mark.asyncio
async def test_pub__action_with_args(bus, amock):
    action = amock()
    bus.sub('test', action)

    bus.pub('test', 1, arg=2)
    await bus.await_running_handlers()

    action.assert_called_with(1, arg=2)


def test_get_default_bus():
    result1 = eventbus.get_bus()
    result2 = eventbus.get_bus()

    assert result1 is result2


def test_get_different_bus():
    result1 = eventbus.get_bus()
    result2 = eventbus.get_bus('another')

    assert result1 is not result2
