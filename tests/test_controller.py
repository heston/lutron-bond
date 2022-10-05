import asyncio
import signal

import pytest

from lutronbond import lutron, controller


@pytest.fixture
def logger(mocker):
    return mocker.patch('lutronbond.controller.logger')


@pytest.fixture
def bus(mocker, amock):
    bus = mocker.patch('lutronbond.eventbus.get_bus')
    bus.return_value.pub = amock()
    return bus.return_value


@pytest.fixture
def bond_get_handler(mocker):
    return mocker.patch('lutronbond.bond.get_handler')


@pytest.mark.asyncio
async def test__handler__invalid_operation(logger):
    event = lutron.LutronEvent(
        lutron.Operation.UNKNOWN,
        99,
        lutron.Component.BTN_1,
        lutron.Action.ENABLE
    )

    await controller.handler(event)

    logger.debug.assert_called_with('Skipping Lutron event: %s', event)


@pytest.mark.asyncio
async def test__handler__valid_operation(logger, bus):
    event = lutron.LutronEvent(
        lutron.Operation.DEVICE,
        99,
        lutron.Component.BTN_1,
        lutron.Action.PRESS
    )

    await controller.handler(event)

    logger.info.assert_called_with('Handling Lutron event: %s', event)
    bus.pub.assert_called_with(99, event)


def test__add_listeners(mocker, logger, bus, bond_get_handler):
    config = {
        99: {
            'name': 'Light',
            'bondID': 'a1b2c3d4',
            'actions': {
                'BTN_1': {
                    'PRESS': 'TurnLightOn',
                }
            }
        }
    }
    subconfig = config[99]
    mocker.patch('lutronbond.config.LUTRON_BOND_MAPPING', config)
    handler = mocker.Mock()
    bond_get_handler.return_value = handler

    controller.add_listeners()

    logger.debug.assert_called_with('Subscribing to %s: %s', 99, subconfig)
    bond_get_handler.assert_called_with(subconfig)
    bus.sub.assert_called_with(99, handler)


@pytest.mark.asyncio
async def test__shutdown(mocker, amock, logger):
    get_connection = mocker.patch(
        'lutronbond.lutron.get_default_lutron_connection'
    )
    get_connection.return_value.close = amock()

    assert controller.shutting_down is False

    await controller.shutdown()

    assert controller.shutting_down is True
    assert get_connection.return_value.close.called
    logger.info.assert_called_with('Exiting...')

    controller.shutting_down = False


@pytest.mark.asyncio
async def test__start(mocker, logger, amock):
    loop = mocker.patch('asyncio.get_running_loop').return_value
    verify_connection = mocker.patch(
        'lutronbond.bond.verify_connection',
        amock()
    )
    keepalive = mocker.patch('lutronbond.bond.keepalive')
    mocker.patch('lutronbond.controller.add_listeners')
    lutron_connection = mocker.patch(
        'lutronbond.lutron.get_default_lutron_connection'
    ).return_value
    lutron_connection.open = amock()
    lutron_connection.stream = amock()

    def fake_shutdown(*args):
        controller.shutting_down = True

    lutron_connection.stream.side_effect = fake_shutdown
    lutron_connection.close = amock()

    await controller.start()

    loop.add_signal_handler.assert_called_with(signal.SIGINT, mocker.ANY)
    assert verify_connection.called
    assert keepalive.called
    assert lutron_connection.open.called
    lutron_connection.stream.assert_called_with(controller.handler)

    controller.shutting_down = False


@pytest.mark.asyncio
async def test__start__cannot_open(mocker, logger, amock):
    mocker.patch('asyncio.get_running_loop').return_value
    mocker.patch(
        'lutronbond.bond.verify_connection',
        amock()
    )
    keepalive = mocker.patch('lutronbond.bond.keepalive')
    mocker.patch('lutronbond.controller.add_listeners')
    lutron_connection = mocker.patch(
        'lutronbond.lutron.get_default_lutron_connection'
    ).return_value
    lutron_connection.open = amock()
    lutron_connection.open.return_value = False
    lutron_connection.close = amock()
    lutron_connection.stream = amock()

    await controller.start()

    assert not lutron_connection.stream.called
    assert lutron_connection.close.called
    assert keepalive.return_value.called


@pytest.mark.asyncio
async def test__start__read_error(mocker, logger, amock):
    mocker.patch('asyncio.get_running_loop').return_value
    mocker.patch(
        'lutronbond.bond.verify_connection',
        amock()
    )
    mocker.patch('lutronbond.bond.keepalive')
    mocker.patch('lutronbond.controller.add_listeners')
    lutron_connection = mocker.patch(
        'lutronbond.lutron.get_default_lutron_connection'
    ).return_value
    lutron_connection.open = amock()
    lutron_connection.stream = amock()

    def handler():
        yield asyncio.exceptions.IncompleteReadError(b'', 32)
        controller.shutting_down = True
        yield True

    lutron_connection.stream.side_effect = handler()
    lutron_connection.close = amock()

    await controller.start()

    lutron_connection.open.assert_has_calls([mocker.call(), mocker.call()])
    lutron_connection.close.assert_has_calls([mocker.call(), mocker.call()])
    lutron_connection.stream.assert_has_calls([
        mocker.call(controller.handler),
        mocker.call(controller.handler)
    ])
    logger.warning.assert_called_with(
        'Connection closed unexpectedly. Retrying...'
    )

    controller.shutting_down = False
