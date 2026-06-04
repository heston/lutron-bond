import pytest

from lutronbond import hue, lutron


@pytest.fixture()
def lutron_event():
    return lutron.LutronEvent(
        lutron.Operation.UNKNOWN,
        99,
        lutron.Component.UNKNOWN,
        lutron.DeviceAction.UNKNOWN,
        '',
        '10.0.0.1'
    )


@pytest.fixture()
def lutron_output_event():
    return lutron.LutronEvent(
        lutron.Operation.OUTPUT,
        99,
        lutron.Component.ANY,
        lutron.OutputAction.SET_LEVEL,
        '100.00',
        '10.0.0.1'
    )


@pytest.fixture()
def logger(mocker):
    return mocker.patch('lutronbond.hue.logger')


@pytest.fixture
def mock_bridge(mocker):
    bridge = mocker.Mock()
    mocker.patch('lutronbond.hue.get_bridge', return_value=bridge)
    return bridge


@pytest.mark.asyncio
async def test_handler__missing_component(lutron_event, logger, mock_bridge):
    handler = hue.get_handler({
        'id': 'asdf',
        'actions': {}
    })

    result = await handler(lutron_event)

    assert result is False

    logger.warning.assert_called_with(
        'Unknown component: %s',
        lutron_event.component
    )


@pytest.mark.asyncio
async def test_handler__missing_action(lutron_event, logger, mock_bridge):
    handler = hue.get_handler({
        'id': 'asdf',
        'actions': {
            'UNKNOWN': {}
        }
    })

    result = await handler(lutron_event)

    assert result is False

    logger.warning.assert_called_with(
        'Unknown action: %s',
        lutron_event.action
    )


@pytest.mark.asyncio
async def test_handler__none_action(lutron_event, mock_bridge):
    handler = hue.get_handler({
        'id': 'asdf',
        'actions': {
            'UNKNOWN': {
                'UNKNOWN': None
            }
        }
    })

    result = await handler(lutron_event)

    assert result is False


@pytest.mark.asyncio
async def test_handler__unknown_device_method(lutron_event, logger, mock_bridge):
    del mock_bridge.lights.UNKNOWN

    handler = hue.get_handler({
        'id': 'asdf',
        'actions': {
            'UNKNOWN': {
                'UNKNOWN': 'UNKNOWN'
            }
        }
    })

    result = await handler(lutron_event)

    assert result is False

    logger.warning.assert_called_with(
        'Unknown Hue device method: %s', 'UNKNOWN'
    )


@pytest.mark.asyncio
async def test_handler__string_action__success__DEVICE(
        mocker,
        lutron_event,
        logger,
        mock_bridge):
    handler = hue.get_handler({
        'id': 'asdf',
        'actions': {
            'UNKNOWN': {
                'UNKNOWN': 'turn_on'
            }
        }
    })

    async_method = mocker.AsyncMock()
    mock_bridge.lights.turn_on = async_method

    result = await handler(lutron_event)

    logger.debug.assert_called_with(
        'Starting %s request to Hue device %s with args %s',
        'turn_on',
        'asdf',
        {}
    )
    async_method.assert_called_with('asdf')
    logger.info.assert_called_with(
        '%s request sent to Hue device %s (%s)',
        'turn_on',
        'asdf',
        'Unnamed'
    )
    assert result is True


@pytest.mark.asyncio
async def test_handler__dict_action__success__OUTPUT(
        mocker,
        lutron_output_event,
        logger,
        mock_bridge):
    handler = hue.get_handler({
        'id': 'asdf',
        'actions': {
            'ANY': {
                'SET_LEVEL': {
                    '100.00': {'set_state': {'on': True, 'brightness': 100}},
                    '0.00': {'set_state': {'on': False}},
                }
            }
        }
    })

    async_method = mocker.AsyncMock()
    mock_bridge.lights.set_state = async_method

    result = await handler(lutron_output_event)

    logger.debug.assert_called_with(
        'Starting %s request to Hue device %s with args %s',
        'set_state',
        'asdf',
        {'on': True, 'brightness': 100}
    )
    async_method.assert_called_with('asdf', on=True, brightness=100)
    logger.info.assert_called_with(
        '%s request sent to Hue device %s (%s)',
        'set_state',
        'asdf',
        'Unnamed'
    )
    assert result is True


@pytest.mark.asyncio
async def test_handler__failure(
        mocker,
        lutron_event,
        logger,
        mock_bridge):
    handler = hue.get_handler({
        'id': 'asdf',
        'actions': {
            'UNKNOWN': {
                'UNKNOWN': 'turn_on'
            }
        }
    })

    exc = Exception('API error')
    async_method = mocker.AsyncMock(side_effect=exc)
    mock_bridge.lights.turn_on = async_method

    result = await handler(lutron_event)

    async_method.assert_called_with('asdf')
    logger.error.assert_called_with(
        '%s request to Hue device %s (%s) failed: %s',
        'turn_on',
        'asdf',
        'Unnamed',
        exc
    )
    assert result is False
