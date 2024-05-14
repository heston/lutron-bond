import asyncio
import pytest

import pytest_asyncio

from lutronbond import lutron

BRIDGE_ADDR = '10.0.0.1'


##
# LutronEvent class tests
##


def test__LutronEvent__init():
    event = lutron.LutronEvent(
        lutron.Operation.UNKNOWN,
        -99,
        lutron.Component.UNKNOWN,
        lutron.DeviceAction.UNKNOWN,
        "",
        BRIDGE_ADDR
    )

    assert event.operation is lutron.Operation.UNKNOWN
    assert event.device == -99
    assert event.component is lutron.Component.UNKNOWN
    assert event.action is lutron.DeviceAction.UNKNOWN
    assert event.parameters == ""
    assert event.bridge == BRIDGE_ADDR


def test__LutronEvent__parse__unrecognized_event():
    rawevent = b"o hai"

    with pytest.raises(ValueError):
        lutron.LutronEvent.parse(rawevent, BRIDGE_ADDR)


def test__LutronEvent__parse__invalid_event():
    rawevent = b"~OUTPUT,16,1"

    with pytest.raises(ValueError):
        lutron.LutronEvent.parse(rawevent, BRIDGE_ADDR)


def test__LutronEvent__parse__unknown_operation():
    rawevent = b"~WHOA,16,1,1"

    result = lutron.LutronEvent.parse(rawevent, BRIDGE_ADDR)

    assert result.operation is lutron.Operation.UNKNOWN


def test__LutronEvent__parse__unknown_device_component():
    rawevent = b"~DEVICE,16,99,1,1"

    result = lutron.LutronEvent.parse(rawevent, BRIDGE_ADDR)

    assert result.component is lutron.Component.UNKNOWN


def test__LutronEvent__parse__unknown_output_action():
    rawevent = b"~OUTPUT,16,9,10"

    result = lutron.LutronEvent.parse(rawevent, BRIDGE_ADDR)

    assert result.action is lutron.OutputAction.UNKNOWN


def test__LutronEvent__parse__unknown_device_action():
    rawevent = b"~DEVICE,16,1,10,1"

    result = lutron.LutronEvent.parse(rawevent, BRIDGE_ADDR)

    assert result.action is lutron.DeviceAction.UNKNOWN


def test__LutronEvent__parse__valid_device_event():
    rawevent = b"~DEVICE,16,2,1,1"

    result = lutron.LutronEvent.parse(rawevent, BRIDGE_ADDR)

    assert result.operation is lutron.Operation.DEVICE
    assert result.device == 16
    assert result.component is lutron.Component.BTN_1
    assert result.action is lutron.DeviceAction.ENABLE
    assert result.parameters == "1"
    assert result.bridge == BRIDGE_ADDR


def test__LutronEvent__parse__valid_device_event__after_command_sent():
    rawevent = b"GNET> ~DEVICE,16,2,1,1"

    result = lutron.LutronEvent.parse(rawevent, BRIDGE_ADDR)

    assert result.operation is lutron.Operation.DEVICE
    assert result.device == 16
    assert result.component is lutron.Component.BTN_1
    assert result.action is lutron.DeviceAction.ENABLE
    assert result.parameters == "1"
    assert result.bridge == BRIDGE_ADDR


def test__LutronEvent__parse__valid_output_event():
    rawevent = b"~OUTPUT,16,2,1"

    result = lutron.LutronEvent.parse(rawevent, BRIDGE_ADDR)

    assert result.operation is lutron.Operation.OUTPUT
    assert result.device == 16
    assert result.component is lutron.Component.ANY
    assert result.action is lutron.OutputAction.START_RAISING
    assert result.parameters == "1"
    assert result.bridge == BRIDGE_ADDR


def test__LutronEvent__repr():
    event = lutron.LutronEvent(
        lutron.Operation.DEVICE,
        7,
        lutron.Component.BTN_1,
        lutron.DeviceAction.PRESS,
        "",
        BRIDGE_ADDR
    )

    result = repr(event)

    assert (
        "LutronEvent("
        "operation=Operation.DEVICE, "
        "device=7, "
        "component=Component.BTN_1, "
        "action=DeviceAction.PRESS, "
        "parameters=None, "
        "bridge=10.0.0.1)"
    ) == result


def test__LutronEvent__DEVICE_str():
    event = lutron.LutronEvent(
        lutron.Operation.DEVICE,
        7,
        lutron.Component.BTN_1,
        lutron.DeviceAction.PRESS,
        "",
        BRIDGE_ADDR
    )

    result = str(event)

    assert "LutronEvent(BRIDGE:10.0.0.1 DEVICE:7 BTN_1:PRESS:None)" == result


def test__LutronEvent__OUTPUT_str():
    event = lutron.LutronEvent(
        lutron.Operation.OUTPUT,
        7,
        lutron.Component.ANY,
        lutron.OutputAction.SET_LEVEL,
        "100.0",
        BRIDGE_ADDR
    )

    result = str(event)

    assert "LutronEvent(BRIDGE:10.0.0.1 OUTPUT:7 ANY:SET_LEVEL:100.0)" == result


##
# LutronCommand class tests
##

def test__LutronCommand__init():
    command = lutron.LutronCommand(
        lutron.Operation.OUTPUT,
        1,
        lutron.Component.ANY,
        lutron.OutputAction.SET_LEVEL,
        "100.0",
        BRIDGE_ADDR
    )

    assert command.operation is lutron.Operation.OUTPUT
    assert command.device == 1
    assert command.component is lutron.Component.ANY
    assert command.action is lutron.OutputAction.SET_LEVEL
    assert command.parameters == "100.0"
    assert command.bridge == BRIDGE_ADDR


def test__LutronCommand__output_action():
    command = lutron.LutronCommand(
        lutron.Operation.OUTPUT,
        1,
        lutron.Component.ANY,
        lutron.OutputAction.SET_LEVEL,
        "75",
        BRIDGE_ADDR
    )

    assert "#OUTPUT,1,1,75\r\n" == str(command)


def test__LutronCommand__device_action():
    command = lutron.LutronCommand(
        lutron.Operation.DEVICE,
        2,
        lutron.Component.BTN_3,
        lutron.DeviceAction.PRESS,
        "",
        BRIDGE_ADDR
    )

    assert "#DEVICE,2,4,3\r\n" == str(command)


##
# LutronConnection class tests
##


@pytest.fixture
def lutron_connection(mocker):
    c = lutron.LutronConnection('10.0.0.1', 23)
    c.logger = mocker.Mock()
    return c


def test__LutronConnection__init(lutron_connection):

    assert lutron_connection.host == '10.0.0.1'
    assert lutron_connection.port == 23
    assert lutron_connection.is_connected is False
    assert lutron_connection.is_logged_in is False


@pytest.fixture
def asyncio_open_connection(mocker, amock):
    mock_open_conn = mocker.patch('asyncio.open_connection', amock())

    reader = mocker.Mock()
    reader.read = amock()
    reader.readuntil = amock()

    writer = mocker.Mock()
    writer.wait_closed = amock()
    writer.drain = amock()

    mock_open_conn.return_value = (reader, writer)

    return mock_open_conn


@pytest_asyncio.fixture
async def connected_lutron_connection(
        lutron_connection,
        asyncio_open_connection
):
    await lutron_connection.connect()
    return lutron_connection


@pytest.mark.asyncio
async def test__LutronConnection__connect(
        lutron_connection,
        asyncio_open_connection
):
    result = await lutron_connection.connect()

    assert asyncio_open_connection.called
    assert lutron_connection.is_connected is True
    assert result is True


@pytest.mark.asyncio
async def test__LutronConnection__close__not_opened(lutron_connection):
    result = await lutron_connection.close()

    assert result is False


@pytest.mark.asyncio
async def test__LutronConnection__close__opened(
        connected_lutron_connection,
        asyncio_open_connection
):
    result = await connected_lutron_connection.close()

    assert result is True
    assert connected_lutron_connection._writer.close.called
    assert connected_lutron_connection._writer.wait_closed.called


@pytest.mark.asyncio
async def test__LutronConnection__login__not_connected(lutron_connection):
    with pytest.raises(RuntimeError):
        await lutron_connection.login()


@pytest.mark.asyncio
async def test__LutronConnection__login__already_logged_in(connected_lutron_connection):
    connected_lutron_connection.is_logged_in = True
    result = await connected_lutron_connection.login()

    assert result is True
    connected_lutron_connection.logger.debug.assert_called_with('Already logged in!')


@pytest.mark.asyncio
async def test__LutronConnection__login__send_username(
        mocker,
        connected_lutron_connection
):
    connected_lutron_connection._reader.read.return_value = lutron.LOGIN_PROMPT
    result = await connected_lutron_connection.login()

    assert result is False
    assert connected_lutron_connection.is_logged_in is False

    connected_lutron_connection.logger.debug.assert_any_call('Starting login...')
    connected_lutron_connection.logger.debug.assert_any_call('Sending username')

    connected_lutron_connection._writer.write.assert_has_calls([
        # Try 1
        mocker.call(lutron.USERNAME),
        mocker.call(lutron.LINE_TERM),
        # Try 2
        mocker.call(lutron.USERNAME),
        mocker.call(lutron.LINE_TERM),
        # Try 3
        mocker.call(lutron.USERNAME),
        mocker.call(lutron.LINE_TERM),
        # Try 4
        mocker.call(lutron.USERNAME),
        mocker.call(lutron.LINE_TERM),
        # Try 5
        mocker.call(lutron.USERNAME),
        mocker.call(lutron.LINE_TERM),
    ])


@pytest.mark.asyncio
async def test__LutronConnection__login__send_password(
        mocker,
        connected_lutron_connection
):
    connected_lutron_connection._reader.read.return_value = (
        lutron.PASSWORD_PROMPT
    )
    result = await connected_lutron_connection.login()

    assert result is False
    assert connected_lutron_connection.is_logged_in is False

    connected_lutron_connection.logger.debug.assert_any_call('Starting login...')
    connected_lutron_connection.logger.debug.assert_any_call('Sending password')

    connected_lutron_connection._writer.write.assert_has_calls([
        # Try 1
        mocker.call(lutron.PASSWORD),
        mocker.call(lutron.LINE_TERM),
        # Try 2
        mocker.call(lutron.PASSWORD),
        mocker.call(lutron.LINE_TERM),
        # Try 3
        mocker.call(lutron.PASSWORD),
        mocker.call(lutron.LINE_TERM),
        # Try 4
        mocker.call(lutron.PASSWORD),
        mocker.call(lutron.LINE_TERM),
        # Try 5
        mocker.call(lutron.PASSWORD),
        mocker.call(lutron.LINE_TERM),
    ])


@pytest.mark.asyncio
async def test__LutronConnection__login__ready(connected_lutron_connection):
    connected_lutron_connection._reader.read.return_value = (
        lutron.READY_PROMPT
    )
    result = await connected_lutron_connection.login()

    assert result is True
    assert connected_lutron_connection.is_logged_in is True

    connected_lutron_connection.logger.debug.assert_any_call('Starting login...')
    connected_lutron_connection.logger.debug.assert_any_call('Login successful!')

    assert not connected_lutron_connection._writer.write.called


@pytest.mark.asyncio
async def test__LutronConnection__open(amock, lutron_connection):
    lutron_connection.connect = amock()
    lutron_connection.login = amock()

    await lutron_connection.open()

    assert lutron_connection.connect.called
    assert lutron_connection.login.called


@pytest.fixture
def logged_in_lutron_connection(connected_lutron_connection):
    connected_lutron_connection.is_logged_in = True
    return connected_lutron_connection


@pytest.mark.asyncio
async def test__LutronConnection__stream__invalid_data(
        mocker,
        amock,
        logged_in_lutron_connection
):
    parse_mock = mocker.patch('lutronbond.lutron.LutronEvent.parse')
    parse_error = ValueError('Invalid')
    parse_mock.side_effect = parse_error

    logged_in_lutron_connection._reader.readuntil.side_effect = [
        'Bogus data',
        asyncio.exceptions.IncompleteReadError(b'', 32),
    ]

    callback = amock()

    with pytest.raises(asyncio.exceptions.IncompleteReadError):
        await logged_in_lutron_connection.stream(callback)

    parse_mock.assert_called_with('Bogus data', BRIDGE_ADDR)
    assert not callback.called

    logged_in_lutron_connection.logger.info.assert_called_with(
        'Listening for events...'
    )
    logged_in_lutron_connection.logger.debug.assert_called_with(
        'Got data: %s', 'Bogus data'
    )
    logged_in_lutron_connection.logger.error.assert_called_with(
        'Error parsing event: %s', parse_error
    )


@pytest.mark.asyncio
async def test__LutronConnection__stream__valid_data(
        mocker,
        logged_in_lutron_connection
):
    parse_mock = mocker.patch('lutronbond.lutron.LutronEvent.parse')
    event = lutron.LutronEvent(
        lutron.Operation.DEVICE,
        1,
        lutron.Component.BTN_1,
        lutron.DeviceAction.PRESS,
        "",
        BRIDGE_ADDR
    )
    parse_mock.return_value = event

    logged_in_lutron_connection._reader.readuntil.side_effect = [
        'Bogus data',
        asyncio.exceptions.IncompleteReadError(b'', 32),
    ]

    callback = mocker.Mock()

    with pytest.raises(asyncio.exceptions.IncompleteReadError):
        await logged_in_lutron_connection.stream(callback)

    parse_mock.assert_called_with('Bogus data', BRIDGE_ADDR)
    callback.assert_called_with(event)

    logged_in_lutron_connection.logger.info.assert_called_with(
        'Listening for events...'
    )
    logged_in_lutron_connection.logger.debug.assert_called_with(
        'Got data: %s', 'Bogus data'
    )


@pytest.fixture
def lutron_command():
    return lutron.LutronCommand(
        lutron.Operation.OUTPUT,
        1,
        lutron.Component.ANY,
        lutron.OutputAction.SET_LEVEL,
        "75",
        '10.0.0.1'
    )


@pytest.mark.asyncio
async def test__LutronConnection__send__not_connected(
    logged_in_lutron_connection,
    lutron_command
):
    logged_in_lutron_connection.is_connected = False

    with pytest.raises(RuntimeError):
        await logged_in_lutron_connection.send(lutron_command)


@pytest.mark.asyncio
async def test__LutronConnection__send__not_logged_in(
    logged_in_lutron_connection,
    lutron_command
):
    logged_in_lutron_connection.is_logged_in = False

    with pytest.raises(RuntimeError):
        await logged_in_lutron_connection.send(lutron_command)


@pytest.mark.asyncio
async def test__LutronConnection__send__wrong_bridge(
    logged_in_lutron_connection,
    lutron_command
):
    lutron_command.bridge = '192.168.0.1'

    with pytest.raises(ValueError):
        await logged_in_lutron_connection.send(lutron_command)


@pytest.mark.asyncio
async def test__LutronConnection__send(
    amock,
    mocker,
    logged_in_lutron_connection,
    lutron_command
):
    logged_in_lutron_connection._writer = mocker.Mock()
    logged_in_lutron_connection._writer.drain = amock()

    await logged_in_lutron_connection.send(lutron_command)

    logged_in_lutron_connection._writer.write.assert_called_with(
        b'#OUTPUT,1,1,75\r\n'
    )
    assert logged_in_lutron_connection._writer.drain.called


##
# Module getters tests
##


def test_get_lutron_connection():
    result1 = lutron.get_lutron_connection('10.0.0.1')
    result2 = lutron.get_lutron_connection('10.0.0.1')

    assert result1 is result2
    assert len(lutron.connections) == 1


def test_get_lutron_connection__different():
    result1 = lutron.get_lutron_connection('10.0.0.1')
    result2 = lutron.get_lutron_connection('10.0.0.2')

    assert result1 is not result2
    assert len(lutron.connections) == 2


def test_get_default_lutron_connection(mocker):
    mock_get_connection = mocker.patch(
        'lutronbond.lutron.get_lutron_connection'
    )
    mocker.patch('lutronbond.config.LUTRON_BRIDGE_ADDR', '10.0.0.3')
    lutron.get_default_lutron_connection()

    mock_get_connection.assert_called_with('10.0.0.3')


def test_reset_connection_cache():
    result1 = lutron.get_lutron_connection('10.0.0.1')
    lutron.get_lutron_connection('10.0.0.2')

    assert len(lutron.connections) == 2

    lutron.reset_connection_cache()

    assert len(lutron.connections) == 0

    result2 = lutron.get_lutron_connection('10.0.0.1')

    assert result1 is not result2


##
# lutron.get_handler tests
##


@pytest.fixture()
def logger(mocker):
    return mocker.patch('lutronbond.lutron.logger')


def test_get_handler__missing_actions():
    with pytest.raises(KeyError):
        lutron.get_handler({})


def test_handler__unknown_bridge(logger):
    with pytest.raises(ValueError):
        lutron.get_handler({'actions': {}, 'bridge': 3})


def test_handler__missing_integration_id(logger):
    with pytest.raises(KeyError):
        lutron.get_handler({'actions': {}, 'bridge': 1})


@pytest.fixture()
def lutron_device_event():
    return lutron.LutronEvent(
        lutron.Operation.DEVICE,
        99,
        lutron.Component.BTN_1,
        lutron.DeviceAction.PRESS,
        '',
        '10.0.0.1'
    )


@pytest.mark.asyncio
async def test_handler__unknown_component(lutron_device_event, logger):
    handler = lutron.get_handler({'actions': {}, 'bridge': 1, 'id': 2})

    result = await handler(lutron_device_event)

    assert result is False

    logger.warning.assert_called_with(
        'Unknown component: %s',
        lutron_device_event.component
    )


@pytest.mark.asyncio
async def test_handler__unspecified_action(lutron_device_event, logger):
    handler = lutron.get_handler(
        {'actions': {'BTN_1': {}}, 'bridge': 1, 'id': 2}
    )

    result = await handler(lutron_device_event)

    assert result is False

    logger.warning.assert_called_with(
        'Unknown action: %s',
        lutron_device_event.action
    )


@pytest.mark.asyncio
async def test_handler__none_action(lutron_device_event, logger):
    handler = lutron.get_handler(
        {'actions': {'BTN_1': {'PRESS': None}}, 'bridge': 1, 'id': 2}
    )

    result = await handler(lutron_device_event)

    assert result is False

    assert not logger.warning.called


@pytest.mark.asyncio
async def test_handler__invalid_device_action(lutron_device_event, logger):
    handler = lutron.get_handler(
        {'actions': {'BTN_1': {'PRESS': 'TurnOn'}}, 'bridge': 1, 'id': 2}
    )

    with pytest.raises(ValueError):
        await handler(lutron_device_event)


@pytest.fixture
def get_lutron_connection(mocker, amock):
    connection = mocker.Mock()
    connection.send = amock()
    mocker.patch('lutronbond.lutron.get_lutron_connection').return_value = connection
    return connection


@pytest.mark.asyncio
async def test_handler__device_event__device_action(
        get_lutron_connection,
        lutron_device_event,
        logger,
        mocker
):
    handler = lutron.get_handler({
        'actions': {
            'BTN_1': {
                'PRESS': {
                    'BTN_1': 'PRESS'
                }
            }
        },
        'bridge': 1,
        'id': 2
    })

    result = await handler(lutron_device_event)

    assert result is True

    call = logger.debug.call_args[0]
    command = call[1]

    assert (
        'LutronCommand('
        'operation=Operation.DEVICE, '
        'device=2, '
        'component=Component.BTN_1, '
        'action=DeviceAction.PRESS, '
        'parameters=None, '
        'bridge=10.0.0.10'
        ')') == repr(command)

    logger.debug.assert_called_with(
        'Translated event into Lutron command: %s', command
    )


@pytest.mark.asyncio
async def test_handler__device_event__device_action__omitted_bridge(
        get_lutron_connection,
        lutron_device_event,
        logger,
        mocker
):
    handler = lutron.get_handler({
        'actions': {
            'BTN_1': {
                'PRESS': {
                    'BTN_1': 'PRESS'
                }
            }
        },
        'id': 2
    })

    result = await handler(lutron_device_event)

    assert result is True

    call = logger.debug.call_args[0]
    command = call[1]

    assert (
        'LutronCommand('
        'operation=Operation.DEVICE, '
        'device=2, '
        'component=Component.BTN_1, '
        'action=DeviceAction.PRESS, '
        'parameters=None, '
        'bridge=10.0.0.10'
        ')') == repr(command)

    logger.debug.assert_called_with(
        'Translated event into Lutron command: %s', command
    )


@pytest.mark.asyncio
async def test_handler__device_event__device_action__bridge2(
        get_lutron_connection,
        lutron_device_event,
        logger,
        mocker
):
    handler = lutron.get_handler({
        'actions': {
            'BTN_1': {
                'PRESS': {
                    'BTN_1': 'PRESS'
                }
            }
        },
        'bridge': 2,
        'id': 2
    })

    result = await handler(lutron_device_event)

    assert result is True

    call = logger.debug.call_args[0]
    command = call[1]

    assert (
        'LutronCommand('
        'operation=Operation.DEVICE, '
        'device=2, '
        'component=Component.BTN_1, '
        'action=DeviceAction.PRESS, '
        'parameters=None, '
        'bridge=10.0.0.20'
        ')') == repr(command)

    logger.debug.assert_called_with(
        'Translated event into Lutron command: %s', command
    )


@pytest.mark.asyncio
async def test_handler__device_event__output_action(
        get_lutron_connection,
        lutron_device_event,
        logger,
        mocker
):
    handler = lutron.get_handler({
        'actions': {
            'BTN_1': {
                'PRESS': {
                    'SET_LEVEL': '100,0.01'
                }
            }
        },
        'bridge': 1,
        'id': 2
    })

    result = await handler(lutron_device_event)

    assert result is True

    call = logger.debug.call_args[0]
    command = call[1]

    assert (
        'LutronCommand('
        'operation=Operation.OUTPUT, '
        'device=2, '
        'component=Component.ANY, '
        'action=OutputAction.SET_LEVEL, '
        'parameters=100,0.01, '
        'bridge=10.0.0.10'
        ')') == repr(command)

    logger.debug.assert_called_with(
        'Translated event into Lutron command: %s', command
    )


@pytest.fixture()
def lutron_output_event():
    return lutron.LutronEvent(
        lutron.Operation.OUTPUT,
        99,
        lutron.Component.ANY,
        lutron.OutputAction.SET_LEVEL,
        '100',
        '10.0.0.1'
    )


@pytest.mark.asyncio
async def test_handler__output_event__output_action(
        get_lutron_connection,
        lutron_output_event,
        logger,
        mocker
):
    handler = lutron.get_handler({
        'actions': {
            'ANY': {
                'SET_LEVEL': {
                    '100': {
                        'SET_LEVEL': '100,0.50',
                    },
                    '0': {
                        'SET_LEVEL': '0,0.05',
                    }
                }
            }
        },
        'bridge': 1,
        'id': 2
    })

    result = await handler(lutron_output_event)

    assert result is True

    call = logger.debug.call_args[0]
    command = call[1]

    assert (
        'LutronCommand('
        'operation=Operation.OUTPUT, '
        'device=2, '
        'component=Component.ANY, '
        'action=OutputAction.SET_LEVEL, '
        'parameters=100,0.50, '
        'bridge=10.0.0.10'
        ')') == repr(command)

    logger.debug.assert_called_with(
        'Translated event into Lutron command: %s', command
    )


@pytest.mark.asyncio
async def test_handler__output_event__device_action(
        get_lutron_connection,
        lutron_output_event,
        logger,
        mocker
):
    handler = lutron.get_handler({
        'actions': {
            'ANY': {
                'SET_LEVEL': {
                    '100': {
                        'BTN_1': 'PRESS',
                    },
                    '0': {
                        'BTN_3': 'PRESS',
                    }
                }
            }
        },
        'bridge': 1,
        'id': 2
    })

    result = await handler(lutron_output_event)

    assert result is True

    call = logger.debug.call_args[0]
    command = call[1]

    assert (
        'LutronCommand('
        'operation=Operation.DEVICE, '
        'device=2, '
        'component=Component.BTN_1, '
        'action=DeviceAction.PRESS, '
        'parameters=None, '
        'bridge=10.0.0.10'
        ')') == repr(command)

    logger.debug.assert_called_with(
        'Translated event into Lutron command: %s', command
    )


@pytest.mark.asyncio
async def test_handler__device_event__unknown_device_action(
        get_lutron_connection,
        lutron_device_event,
        logger,
        mocker
):
    handler = lutron.get_handler({
        'actions': {
            'BTN_1': {
                'PRESS': {
                    'HOKEY_POKEY': True
                }
            }
        },
        'bridge': 1,
        'id': 2
    })

    with pytest.raises(RuntimeError) as e:
        await handler(lutron_device_event)

    assert 'Unknown action encountered: HOKEY_POKEY' == str(e.value)


@pytest.mark.asyncio
async def test_handler__output_event__unconfigured_output_action(
        get_lutron_connection,
        lutron_output_event,
        logger,
        mocker
):
    handler = lutron.get_handler({
        'actions': {
            'ANY': {
                'SET_LEVEL': {
                    '0': {
                        'BTN_1': 'PRESS',
                    }
                }
            }
        },
        'bridge': 1,
        'id': 2
    })

    result = await handler(lutron_output_event)

    assert result is False

    logger.warning.assert_called_with(
        'Action not specified in config: %s:%s',
        lutron_output_event.action,
        lutron_output_event.parameters
    )


@pytest.mark.asyncio
async def test_handler__output_event__unknown_output_action(
        get_lutron_connection,
        lutron_output_event,
        logger,
        mocker
):
    handler = lutron.get_handler({
        'actions': {
            'ANY': {
                'SET_LEVEL': {
                    'qux': {
                        'BTN_1': 'PRESS',
                    }
                }
            }
        },
        'bridge': 1,
        'id': 2
    })

    result = await handler(lutron_output_event)

    assert result is False

    logger.warning.assert_called_with(
        'Action not specified in config: %s:%s',
        lutron_output_event.action,
        lutron_output_event.parameters
    )
