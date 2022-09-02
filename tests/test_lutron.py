import pytest

from lutronbond import lutron


def test__LutronEvent__init():
    event = lutron.LutronEvent(
        lutron.Operation.UNKNOWN,
        -99,
        lutron.Component.UNKNOWN,
        lutron.Action.UNKNOWN
    )

    assert event.operation is lutron.Operation.UNKNOWN
    assert event.device == -99
    assert event.component is lutron.Component.UNKNOWN
    assert event.action is lutron.Action.UNKNOWN


def test__LutronEvent__parse__unrecognized_event():
    rawevent = b"o hai"

    with pytest.raises(ValueError):
        lutron.LutronEvent.parse(rawevent)


def test__LutronEvent__parse__invalid_event():
    rawevent = b"~OUTPUT,16,1"

    with pytest.raises(ValueError):
        lutron.LutronEvent.parse(rawevent)


def test__LutronEvent__parse__unknown_operation():
    rawevent = b"~WHOA,16,1,1"

    result = lutron.LutronEvent.parse(rawevent)

    assert result.operation is lutron.Operation.UNKNOWN


def test__LutronEvent__parse__unknown_component():
    rawevent = b"~OUTPUT,16,9,1"

    result = lutron.LutronEvent.parse(rawevent)

    assert result.component is lutron.Component.UNKNOWN


def test__LutronEvent__parse__unknown_action():
    rawevent = b"~OUTPUT,16,1,10"

    result = lutron.LutronEvent.parse(rawevent)

    assert result.action is lutron.Action.UNKNOWN


def test__LutronEvent__parse__valid_event():
    rawevent = b"~OUTPUT,16,2,1"

    result = lutron.LutronEvent.parse(rawevent)

    assert result.operation is lutron.Operation.OUTPUT
    assert result.device == 16
    assert result.component is lutron.Component.BTN_1
    assert result.action is lutron.Action.ENABLE


def test__LutronEvent__repr():
    event = lutron.LutronEvent(
        lutron.Operation.OUTPUT,
        7,
        lutron.Component.BTN_1,
        lutron.Action.PRESS
    )

    result = repr(event)

    assert (
        "LutronEvent("
        "operation=Operation.OUTPUT, "
        "device=7, "
        "component=Component.BTN_1, "
        "action=Action.PRESS)"
    ) == result



def test__LutronEvent__str():
    event = lutron.LutronEvent(
        lutron.Operation.OUTPUT,
        7,
        lutron.Component.BTN_1,
        lutron.Action.PRESS
    )

    result = str(event)

    assert "LutronEvent(OUTPUT:7 BTN_1:PRESS)" == result


@pytest.fixture
def lutron_connection():
    return lutron.LutronConnection('10.0.0.1', 23)


def test__LutronConnection__init(lutron_connection):

    assert lutron_connection.host == '10.0.0.1'
    assert lutron_connection.port == 23
    assert lutron_connection.is_connected is False
    assert lutron_connection.is_logged_in is False


@pytest.fixture
def asyncio_open_connection(mocker):
    mock_open_conn = mocker.patch('asyncio.open_connection')
    mock_open_conn.return_value = (mocker.Mock(), mocker.Mock())
    return mock_open_conn


@pytest.mark.asyncio
async def test__LutronConnection__connect(lutron_connection, asyncio_open_connection):
    result = await lutron_connection.connect()

    assert lutron_connection.is_connected is True
    assert result is True
