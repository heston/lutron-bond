import asyncio
import signal

import pytest

from lutronbond import lutron, controller


@pytest.fixture
def logger(mocker):
    return mocker.patch('lutronbond.controller.logger')


@pytest.fixture
def bus(mocker):
    bus = mocker.patch('lutronbond.eventbus.get_bus')
    bus.return_value.pub = mocker.Mock()
    return bus.return_value


@pytest.fixture
def bond_get_handler(mocker):
    return mocker.patch('lutronbond.bond.get_handler')


@pytest.fixture
def tuya_get_handler(mocker):
    return mocker.patch('lutronbond.tuya.get_handler')


@pytest.fixture(autouse=True)
def reset_lutron_connections():
    lutron.reset_connection_cache()


def test__handler__invalid_operation(import_config, logger):
    config = import_config()
    event = lutron.LutronEvent(
        lutron.Operation.UNKNOWN,
        99,
        lutron.Component.BTN_1,
        lutron.Action.ENABLE,
        config.LUTRON_BRIDGE_ADDR
    )

    controller.handler(event)

    logger.debug.assert_called_with('Skipping Lutron event: %s', event)


def test__handler__valid_operation(import_config, logger, bus):
    config = import_config()
    event = lutron.LutronEvent(
        lutron.Operation.DEVICE,
        99,
        lutron.Component.BTN_1,
        lutron.Action.PRESS,
        config.LUTRON_BRIDGE_ADDR
    )

    controller.handler(event)

    logger.info.assert_called_with('Handling Lutron event: %s', event)
    bus.pub.assert_called_with('{}:{}'.format(config.LUTRON_BRIDGE_ADDR, 99), event)


def test__add_bond_listener(
        mocker, logger, bus, tuya_get_handler, bond_get_handler, import_config):
    env_config = import_config()
    config = {
        99: {
            'name': 'Light',
            'bond': {
                'id': 'a1b2c3d4',
                'actions': {
                    'BTN_1': {
                        'PRESS': 'TurnLightOn',
                    }
                }
            }
        }
    }
    subconfig = config[99]
    mocker.patch('lutronbond.config.LUTRON_MAPPING', config)
    mocker.patch('lutronbond.config.LUTRON2_MAPPING', {})
    handler = mocker.Mock()
    bond_get_handler.return_value = handler

    controller.add_listeners()

    logger.debug.assert_called_with(
        'Subscribing to %s:%s -> %s',
        env_config.LUTRON_BRIDGE_ADDR, 99, subconfig
    )
    bond_get_handler.assert_called_with(subconfig['bond'])
    assert not tuya_get_handler.called
    bus.sub.assert_called_with('{}:{}'.format(env_config.LUTRON_BRIDGE_ADDR, 99), handler)


def test__add_bond_listener_list(
        mocker, logger, bus, tuya_get_handler, bond_get_handler, import_config):
    env_config = import_config()
    config = {
        99: {
            'name': 'Light',
            'bond': [
                {
                    'id': 'a1b2c3d4',
                    'actions': {
                        'BTN_1': {
                            'PRESS': 'TurnLightOn',
                        }
                    }

                },
                {
                    'id': 'e5f6g7h8',
                    'actions': {
                        'BTN_1': {
                            'PRESS': 'TurnLightOn',
                        }
                    }

                },
            ],
        }
    }
    subconfig = config[99]
    mocker.patch('lutronbond.config.LUTRON_MAPPING', config)
    mocker.patch('lutronbond.config.LUTRON2_MAPPING', {})
    handler = mocker.Mock()
    bond_get_handler.return_value = handler

    controller.add_listeners()

    logger.debug.assert_called_with(
        'Subscribing to %s:%s -> %s',
        env_config.LUTRON_BRIDGE_ADDR, 99, subconfig
    )
    bond_get_handler.assert_has_calls([
        mocker.call(subconfig['bond'][0]),
        mocker.call(subconfig['bond'][1]),
    ])
    assert not tuya_get_handler.called
    bus.sub.assert_has_calls([
        mocker.call(
            '{}:{}'.format(env_config.LUTRON_BRIDGE_ADDR, 99),
            handler
        ),
        mocker.call(
            '{}:{}'.format(env_config.LUTRON_BRIDGE_ADDR, 99),
            handler
        )
    ])


def test__add_bond_listeners__bridge2(
        mocker, logger, bus, bond_get_handler, import_config):
    env_config = import_config()
    config = {
        99: {
            'name': 'Light',
            'bond': {
                'id': 'a1b2c3d4',
                'actions': {
                    'BTN_1': {
                        'PRESS': 'TurnLightOn',
                    }
                }
            }
        }
    }

    config2 = {
        88: {
            'name': 'Light2',
            'bond': {
                'id': 'a1b2c3d4',
                'actions': {
                    'BTN_1': {
                        'PRESS': 'TurnLightOn',
                    }
                }
            }
        }
    }
    subconfig = config[99]
    subconfig2 = config2[88]
    mocker.patch('lutronbond.config.LUTRON_MAPPING', config)
    mocker.patch('lutronbond.config.LUTRON2_MAPPING', config2)
    handler = mocker.Mock()
    bond_get_handler.return_value = handler

    controller.add_listeners()

    logger.debug.assert_has_calls([
        mocker.call(
            'Subscribing to %s:%s -> %s',
            env_config.LUTRON_BRIDGE_ADDR, 99, subconfig
        ),
        mocker.call(
            'Subscribing to %s:%s -> %s',
            env_config.LUTRON_BRIDGE2_ADDR, 88, subconfig2
        )
    ])
    bond_get_handler.assert_has_calls([
        mocker.call(subconfig['bond']),
        mocker.call(subconfig2['bond'])
    ])
    bus.sub.assert_has_calls([
        mocker.call('{}:{}'.format(env_config.LUTRON_BRIDGE_ADDR, 99), handler),
        mocker.call('{}:{}'.format(env_config.LUTRON_BRIDGE2_ADDR, 88), handler)
    ])


def test__add_tuya_listener(
        mocker, logger, bus, tuya_get_handler, bond_get_handler, import_config):
    env_config = import_config()
    config = {
        99: {
            'tuya': {
                'id': 'asdf',
                'key': 'ghjk',
                'addr': '192.168.100.100',
                'version': 3.3,
                'actions': {
                    'BTN_1': {
                        'PRESS': 'TurnOn',
                        'RELEASE': None,
                    }
                }
            }
        }
    }
    subconfig = config[99]
    mocker.patch('lutronbond.config.LUTRON_MAPPING', config)
    mocker.patch('lutronbond.config.LUTRON2_MAPPING', {})
    handler = mocker.Mock()
    tuya_get_handler.return_value = handler

    controller.add_listeners()

    logger.debug.assert_called_with(
        'Subscribing to %s:%s -> %s',
        env_config.LUTRON_BRIDGE_ADDR, 99, subconfig
    )
    tuya_get_handler.assert_called_with(subconfig['tuya'])
    assert not bond_get_handler.called
    bus.sub.assert_called_with('{}:{}'.format(env_config.LUTRON_BRIDGE_ADDR, 99), handler)


def test__add_tuya_listener_list(
        mocker, logger, bus, tuya_get_handler, bond_get_handler, import_config):
    env_config = import_config()
    config = {
        99: {
            'tuya': [
                {
                    'id': 'asdf',
                    'key': 'ghjk',
                    'addr': '192.168.100.100',
                    'version': 3.3,
                    'actions': {
                        'BTN_1': {
                            'PRESS': 'TurnOn',
                            'RELEASE': None,
                        }
                    }
                },
                {
                    'id': 'qwer',
                    'key': 'tyui',
                    'addr': '192.168.100.200',
                    'version': 3.1,
                    'actions': {
                        'BTN_1': {
                            'PRESS': 'TurnOn',
                            'RELEASE': None,
                        }
                    }
                },
            ],
        }
    }
    subconfig = config[99]
    mocker.patch('lutronbond.config.LUTRON_MAPPING', config)
    mocker.patch('lutronbond.config.LUTRON2_MAPPING', {})
    handler = mocker.Mock()
    tuya_get_handler.return_value = handler

    controller.add_listeners()

    logger.debug.assert_called_with(
        'Subscribing to %s:%s -> %s',
        env_config.LUTRON_BRIDGE_ADDR, 99, subconfig
    )
    tuya_get_handler.assert_has_calls([
        mocker.call(subconfig['tuya'][0]),
        mocker.call(subconfig['tuya'][1]),
    ])
    assert not bond_get_handler.called
    bus.sub.assert_has_calls([
        mocker.call(
            '{}:{}'.format(env_config.LUTRON_BRIDGE_ADDR, 99),
            handler
        ),
        mocker.call(
            '{}:{}'.format(env_config.LUTRON_BRIDGE_ADDR, 99),
            handler
        )
    ])


def test__add_tuya_and_bond_listeners(
        mocker, logger, bus, tuya_get_handler, bond_get_handler, import_config):
    env_config = import_config()
    config = {
        99: {
            'tuya': {
                'id': 'asdf',
                'key': 'ghjk',
                'addr': '192.168.100.100',
                'version': 3.3,
                'actions': {
                    'BTN_1': {
                        'PRESS': 'TurnOn',
                        'RELEASE': None,
                    }
                }
            },
            'bond': {
                'id': 'a1b2c3d4',
                'actions': {
                    'BTN_1': {
                        'PRESS': 'TurnLightOn',
                    }
                }
            }
        }
    }
    subconfig = config[99]
    mocker.patch('lutronbond.config.LUTRON_MAPPING', config)
    mocker.patch('lutronbond.config.LUTRON2_MAPPING', {})
    tuya_handler = mocker.Mock()
    tuya_get_handler.return_value = tuya_handler
    bond_handler = mocker.Mock()
    bond_get_handler.return_value = bond_handler

    controller.add_listeners()

    logger.debug.assert_called_with(
        'Subscribing to %s:%s -> %s',
        env_config.LUTRON_BRIDGE_ADDR, 99, subconfig
    )
    tuya_get_handler.assert_called_with(subconfig['tuya'])
    bond_get_handler.assert_called_with(subconfig['bond'])
    bus.sub.assert_has_calls([
        mocker.call(
            '{}:{}'.format(env_config.LUTRON_BRIDGE_ADDR, 99),
            bond_handler
        ),
        mocker.call(
            '{}:{}'.format(env_config.LUTRON_BRIDGE_ADDR, 99),
            tuya_handler
        )
    ])


@pytest.mark.asyncio
async def test__shutdown(mocker, amock, logger):
    get_connection = mocker.patch(
        'lutronbond.lutron.LutronConnection'
    )
    get_connection.return_value.close = amock()

    lutron.get_lutron_connection('a')
    lutron.get_lutron_connection('b')

    assert controller.shutting_down is False

    await controller.shutdown()

    assert controller.shutting_down is True
    assert len(lutron.connections) == 2
    assert all(c.close.called for c in lutron.connections)
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
        'lutronbond.lutron.LutronConnection'
    ).return_value
    lutron_connection.open = amock(return_value=True)
    lutron_connection.stream = amock()
    lutron_connection.close = amock()

    def fake_shutdown(*args):
        controller.shutting_down = True

    lutron_connection.stream.side_effect = fake_shutdown

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
        'lutronbond.lutron.LutronConnection'
    ).return_value
    lutron_connection.open = amock(return_value=False)
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
        'lutronbond.lutron.LutronConnection'
    ).return_value
    lutron_connection.open = amock(return_value=True)

    def handler():
        # Connection 1 stream raises read error
        yield asyncio.exceptions.IncompleteReadError(b'', 32)
        # Connection 2 stream returns normally
        yield
        controller.shutting_down = True
        # Connection 1 stream returns normally
        yield
        # Connection 2 stream returns normally
        yield

    lutron_connection.stream = amock(side_effect=handler())
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
