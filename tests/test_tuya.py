import pytest

from lutronbond import tuya, lutron


@pytest.fixture()
def lutron_event():
    return lutron.LutronEvent(
        lutron.Operation.UNKNOWN,
        99,
        lutron.Component.UNKNOWN,
        lutron.Action.UNKNOWN,
        '10.0.0.1'
    )


@pytest.fixture()
def logger(mocker):
    return mocker.patch('lutronbond.tuya.logger')


def test_get_handler__missing_device():
    with pytest.raises(KeyError):
        tuya.get_handler({})


def test_get_handler__missing_device_details(logger):
    with pytest.raises(KeyError):
        tuya.get_handler({'tuya': {}})

    logger.error.assert_called_with(
        'Invalid Tuya device: %s',
        {}
    )


def test_get_handler__missing_actions():
    with pytest.raises(KeyError):
        tuya.get_handler({
            'tuya': {
                'id': 'asdf',
                'addr': '10.0.0.2',
                'localKey': 'ghjk',
                'version': 3.3
            }
        })


@pytest.mark.asyncio
async def test_handler__missing_component(lutron_event, logger):
    handler = tuya.get_handler({
        'tuya': {
            'id': 'asdf',
            'addr': '10.0.0.2',
            'localKey': 'ghjk',
            'version': 3.3,
            'actions': {}
        }
    })

    result = await handler(lutron_event)

    assert result is False

    logger.warning.assert_called_with(
        'Unknown component: %s',
        lutron_event.component
    )


@pytest.mark.asyncio
async def test_handler__missing_action(lutron_event, logger):
    handler = tuya.get_handler({
        'tuya': {
            'id': 'asdf',
            'addr': '10.0.0.2',
            'localKey': 'ghjk',
            'version': 3.1,
            'actions': {
                'UNKNOWN': {}
            }
        }
    })

    result = await handler(lutron_event)

    assert result is False

    logger.warning.assert_called_with(
        'Unknown action: %s',
        lutron_event.action
    )


@pytest.mark.asyncio
async def test_handler__none_action(lutron_event, logger):
    handler = tuya.get_handler({
        'tuya': {
            'id': 'asdf',
            'addr': '10.0.0.2',
            'localKey': 'ghjk',
            'version': 3.1,
            'actions': {
                'UNKNOWN': {
                    'UNKNOWN': None
                }
            }
        }
    })

    result = await handler(lutron_event)

    assert result is False


@pytest.mark.asyncio
async def test_handler__unknown_device_method(lutron_event, logger):
    handler = tuya.get_handler({
        'tuya': {
            'id': 'asdf',
            'addr': '10.0.0.2',
            'localKey': 'ghjk',
            'version': 3.3,
            'actions': {
                'UNKNOWN': {
                    'UNKNOWN': 'UNKNOWN'
                }
            }
        }
    })

    result = await handler(lutron_event)

    assert result is False

    logger.warning.assert_called_with(
        'Unknown device method: %s', 'UNKNOWN'
    )


@pytest.fixture
def mock_device(mocker):
    return mocker.patch('tinytuya.OutletDevice').return_value


@pytest.mark.asyncio
async def test_handler__turn_on(
        mocker,
        lutron_event,
        logger,
        mock_device):
    handler = tuya.get_handler({
        'tuya': {
            'id': 'asdf',
            'addr': '10.0.0.2',
            'localKey': 'ghjk',
            'version': 3.3,
            'actions': {
                'UNKNOWN': {
                    'UNKNOWN': 'TurnOn'
                }
            }
        }
    })

    result = await handler(lutron_event)

    logger.debug.assert_called_with(
        'Starting %s request to Tuya device %s',
        'TurnOn',
        'asdf'
    )
    assert mock_device.turn_on.called
    logger.info.assert_called_with(
        '%s request sent to Tuya device %s (%s)',
        'TurnOn',
        'asdf',
        'Unnamed'
    )
    assert result is True


@pytest.mark.asyncio
async def test_handler__turn_off(
        mocker,
        lutron_event,
        logger,
        mock_device):
    handler = tuya.get_handler({
        'tuya': {
            'id': 'asdf',
            'addr': '10.0.0.2',
            'localKey': 'ghjk',
            'version': 3.3,
            'actions': {
                'UNKNOWN': {
                    'UNKNOWN': 'TurnOff'
                }
            }
        }
    })

    result = await handler(lutron_event)

    logger.debug.assert_called_with(
        'Starting %s request to Tuya device %s',
        'TurnOff',
        'asdf'
    )
    assert mock_device.turn_off.called
    logger.info.assert_called_with(
        '%s request sent to Tuya device %s (%s)',
        'TurnOff',
        'asdf',
        'Unnamed'
    )
    assert result is True
