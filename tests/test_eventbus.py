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


@pytest.mark.asyncio
async def test_pub__invalid_key(bus):
    retval = await bus.pub('test')

    assert retval is None


@pytest.mark.asyncio
async def test_pub__single_action(bus, Amock):
    action = Amock()
    bus.sub('test', action)

    await bus.pub('test')

    assert action.called


@pytest.mark.asyncio
async def test_pub__multiple_action(bus, Amock):
    action1 = Amock()
    action2 = Amock()
    bus.sub('test', action1)
    bus.sub('test', action2)

    await bus.pub('test')

    assert action1.called
    assert action2.called


@pytest.mark.asyncio
async def test_pub__action_with_args(bus, Amock):
    action = Amock()
    bus.sub('test', action)

    await bus.pub('test', 1, arg=2)

    action.assert_called_with(1, arg=2)
