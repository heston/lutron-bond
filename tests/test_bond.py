import asyncio

import aiohttp
import pytest

from lutronbond import bond, lutron


@pytest.fixture(autouse=True)
def clear_get_bond_connection_cache():
    bond.get_bond_connection.cache_clear()


def test_get_bond_connection_call(mocker):
    bond_mock = mocker.patch('bond_async.Bond')

    bond.get_bond_connection('10.0.0.1', 'apikey')

    bond_mock.assert_called_with('10.0.0.1', 'apikey')


def test_get_bond_connection():
    result = bond.get_bond_connection('10.0.0.1', 'apikey')

    assert isinstance(result, bond.bond_async.Bond)


def test_get_bond_connection_cached():
    result1 = bond.get_bond_connection('10.0.0.1', 'apikey')
    result2 = bond.get_bond_connection('10.0.0.1', 'apikey')

    assert result1 is result2


def test_get_bond_connection_not_cached():
    result1 = bond.get_bond_connection('10.0.0.1', 'apikey')
    result2 = bond.get_bond_connection('10.0.0.2', 'apikey')

    assert result1 is not result2


def test_get_default_bond_connection(mocker):
    mocker.patch('lutronbond.config.BOND_BRIDGE_ADDR', '10.0.0.3')
    mocker.patch('lutronbond.config.BOND_BRIDGE_API_TOKEN', 'apikey2')
    mock_connection = mocker.patch('lutronbond.bond.get_bond_connection')
    bond.get_default_bond_connection()

    mock_connection.assert_called_with('10.0.0.3', 'apikey2')


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
    return mocker.patch('lutronbond.bond.logger')


@pytest.mark.asyncio
async def test_get_handler__missing_actions(lutron_event):
    handler = bond.get_handler({})

    with pytest.raises(KeyError):
        await handler(lutron_event)


@pytest.mark.asyncio
async def test_get_handler__unknown_component(lutron_event, logger):
    handler = bond.get_handler({'actions': {}})

    result = await handler(lutron_event)

    assert result is False

    logger.warning.assert_called_with(
        'Unknown component: %s',
        lutron_event.component
    )


@pytest.mark.asyncio
async def test_get_handler__unknown_action(lutron_event, logger):
    handler = bond.get_handler({'actions': {'UNKNOWN': {}}})

    result = await handler(lutron_event)

    assert result is False

    logger.warning.assert_called_with(
        'Unknown action: %s',
        lutron_event.action
    )


@pytest.mark.asyncio
async def test_get_handler__missing_action(lutron_event, logger):
    handler = bond.get_handler({'actions': {'UNKNOWN': {'UNKNOWN': None}}})

    result = await handler(lutron_event)

    assert result is False


@pytest.fixture
def mock_bond_action(mocker):
    return mocker.patch('bond_async.action.Action')


@pytest.fixture
def mock_default_bond_connection(mocker, amock):
    get_default_bond_connection = mocker.patch(
        'lutronbond.bond.get_default_bond_connection',
    )
    get_default_bond_connection.return_value.action = amock()
    get_default_bond_connection.return_value.version = amock()
    return get_default_bond_connection.return_value


@pytest.mark.asyncio
async def test_get_handler__str_action(
        lutron_event,
        logger,
        mock_bond_action,
        mock_default_bond_connection):
    handler = bond.get_handler({
        'actions': {'UNKNOWN': {'UNKNOWN': 'Hi'}},
        'bondID': 'bondid',
    })

    result = await handler(lutron_event)

    mock_bond_action.assert_called_with('Hi', argument=None)
    mock_default_bond_connection.action.assert_called_with(
        'bondid',
        mock_bond_action.return_value
    )
    assert result is True


@pytest.mark.asyncio
async def test_get_handler__dict_action(
        lutron_event,
        logger,
        mock_bond_action,
        mock_default_bond_connection):
    handler = bond.get_handler({
        'actions': {'UNKNOWN': {'UNKNOWN': {'Hi': 3}}},
        'bondID': 'bondid',
    })

    result = await handler(lutron_event)

    mock_bond_action.assert_called_with('Hi', argument=3)
    mock_default_bond_connection.action.assert_called_with(
        'bondid',
        mock_bond_action.return_value
    )
    logger.info.assert_called_with(
        '%s for %s request sent to Bond Bridge %s',
        'Hi',
        'Unnamed',
        'bondid'
    )
    assert result is True


@pytest.mark.asyncio
async def test_get_handler__retry_on_exception__failed(
        mocker,
        lutron_event,
        logger,
        mock_bond_action,
        mock_default_bond_connection):
    mock_default_bond_connection.action.side_effect = (
        aiohttp.client_exceptions.ClientConnectorError(
            mocker.Mock('192.168.86.60:80'),
            mocker.Mock(errno=1, strerror='huh')
        )
    )
    handler = bond.get_handler({
        'actions': {'UNKNOWN': {'UNKNOWN': 'Hi'}},
        'bondID': 'bondid',
    })

    result = await handler(lutron_event)

    mock_bond_action.assert_called_with('Hi', argument=None)
    mock_default_bond_connection.action.assert_called_with(
        'bondid',
        mock_bond_action.return_value
    )
    assert result is False


@pytest.mark.asyncio
async def test_get_handler__retry_on_exception__success(
        mocker,
        lutron_event,
        logger,
        mock_bond_action,
        mock_default_bond_connection):

    def effect():
        yield aiohttp.client_exceptions.ClientConnectorError(
            mocker.Mock('192.168.86.60:80'),
            mocker.Mock(errno=1, strerror='huh')
        )
        yield aiohttp.client_exceptions.ClientConnectorError(
            mocker.Mock('192.168.86.60:80'),
            mocker.Mock(errno=1, strerror='huh')
        )
        yield True

    mock_default_bond_connection.action.side_effect = effect()

    handler = bond.get_handler({
        'actions': {'UNKNOWN': {'UNKNOWN': 'Hi'}},
        'bondID': 'bondid',
    })

    result = await handler(lutron_event)

    mock_bond_action.assert_called_with('Hi', argument=None)
    mock_default_bond_connection.action.assert_called_with(
        'bondid',
        mock_bond_action.return_value
    )
    assert result is True


@pytest.mark.asyncio
async def test_verify_connection(mock_default_bond_connection, logger):

    mock_default_bond_connection.version.return_value = {
        'model': 'model',
        'fw_ver': 'version',
    }
    await bond.verify_connection()

    assert mock_default_bond_connection.version.called
    logger.info.assert_called_with(
        'Connected to Bond Bridge. Model model. Version version'
    )


@pytest.mark.asyncio
async def test_keepalive(
        mock_default_bond_connection,
        logger,
        mocker,
        event_loop
):
    mocker.patch('lutronbond.config.BOND_KEEPALIVE_INTERVAL', 0.01)

    cancel = bond.keepalive()
    event_loop.call_later(0.02, cancel)
    await asyncio.sleep(0.03)

    assert mock_default_bond_connection.version.called
    logger.debug.assert_called_with('Bond keepalive check successful')


@pytest.mark.asyncio
async def test_keepalive_disabled(
        mock_default_bond_connection,
        logger,
        mocker
):
    mocker.patch('lutronbond.config.BOND_KEEPALIVE_INTERVAL', 0)

    cancel = bond.keepalive()
    await asyncio.sleep(0.01)

    assert cancel() is True
    assert not mock_default_bond_connection.version.called
    assert not logger.debug.called


@pytest.mark.asyncio
async def test_keepalive_cancel(
        mock_default_bond_connection,
        logger,
        mocker,
        event_loop
):
    mocker.patch('lutronbond.config.BOND_KEEPALIVE_INTERVAL', 0.02)

    cancel = bond.keepalive()
    event_loop.call_later(0.01, cancel)
    await asyncio.sleep(0.03)

    assert not mock_default_bond_connection.version.called
    assert not logger.debug.called
