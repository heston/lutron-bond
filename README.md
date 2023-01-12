# Lutron-Bond

[![pytest](https://github.com/heston/lutron-bond/actions/workflows/pytest.yml/badge.svg)](https://github.com/heston/lutron-bond/actions/workflows/pytest.yml)
[![flake8](https://github.com/heston/lutron-bond/actions/workflows/flake8.yml/badge.svg)](https://github.com/heston/lutron-bond/actions/workflows/flake8.yml)
[![mypy](https://github.com/heston/lutron-bond/actions/workflows/mypy.yml/badge.svg)](https://github.com/heston/lutron-bond/actions/workflows/mypy.yml)

Connector between Lutron Caseta SmartBridge Pro and Bond Bridge and/or Tuya Devices.

# Requirements

* Python 3.10
* [Lutron Caseta SmartBridge Pro](https://www.casetawireless.com/us/en/pro-products) (will not work with non-Pro version)
* [Bond Bridge](https://bondhome.io/product/bond-bridge/)

_Optional_

* [TuyaCloud](https://www.tuya.com/) device (like a smart outlet or lightbulb). Tuya is a white-label manufacturer, and their devices are sold under many names. Tuya devices work with the Smart Life app.


# Usage

## Set Up Lutron Bridge

Before proceeding, ensure that your Lutron bridge is listening for incoming connections:

1. Open the Lutron app on your phone.
1. Tap the gear icon in the upper left.
1. Tap "Advanced" towards the bottom of the menu.
1. Tap "Integration"
1. Select the checkbox next to "Telnet Support"


## Run Software

This software must be running somewhere on your local network (with access to
the Lutron and Bond hubs) in order for it to work. A Raspberry Pi, or other always-on
computer is a good choice. However, how to deploy this is left as an exercise
for the reader (look at [lutronbond.service](blob/main/lutronbond.service) for
a starting place).

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export LB_LUTRON_BRIDGE_ADDR="<IP address of Lutron bridge>"
export LB_BOND_BRIDGE_ADDR="<IP address of Bond Bridge>"
export LB_BOND_BRIDGE_API_TOKEN="<Bond Bridge API token>"
./run.sh
```

Alternatively, the environment variable export lines may be specified in a file
named `.env` in the same directory as `run.sh`. For example:

```txt
export LB_LUTRON_BRIDGE_ADDR="<IP address of Lutron bridge>"
export LB_BOND_BRIDGE_ADDR="<IP address of Bond Bridge>"
export LB_BOND_BRIDGE_API_TOKEN="<Bond Bridge API token>"
```

`run.sh` will look for this file and load it for you.


# Configuration

Each home's configuration will be different. Look at
[config.py](blob/main/lutronbond/config.py) for an example configuration.

Any button press from any Lutron switch/remote can be configured (in addition to
its normal function) to control a Bond and/or Tuya device. To do this, you'll need the
Lutron Integration ID (the ID of the Lutron switch in the hub). You will also need
the Bond ID and/or Tuya device credentials.

You'll also need to figure out which action the Bond Bridge or Tuya device should
take when a Lutron action is performed.

For example, to trigger a Bond action:

```python
LUTRON_MAPPING = {
    21: {  # <-- This number is the Lutron Integration ID
        'name': 'Fan Light',  # This is technically optional, but helps readability
        'bond': {
            'id': '6409d2a2',  # The ID of the Bond device (may be 8 or 16 chars)
            'actions': {
                'BTN_1': {
                    'PRESS': 'TurnLightOn',  # Bond action
                    'RELEASE': None,  # No-op. Technically optional.
                },
                'BTN_3': {
                    'PRESS': 'TurnLightOff',
                    'RELEASE': None,
                },
            }
        }
    }
}

```

To see all the Bond actions available, take a look at the [Action class here](https://github.com/bondhome/bond-async/blob/master/bond_async/action.py#L14).
Not all devices support all actions, so some trial-and-error may be needed.

To trigger a Tuya action:

```python
LUTRON_MAPPING = {
    21: {  # <-- This number is the Lutron Integration ID
        'name': 'Smart Switch 1',  # Optional, but helps readability
        'tuya': {
            'id': 'ebfe2b76f486db7b067lvm',  # The ID of the Tuya device (see docs below)
            'key': 'b073d73bea4f94f5',  # See docs below
            'addr': '192.168.1.195',  # IP address of Tuya device on local network
            'version': 3.3,  # See docs below
            'actions': {
                'BTN_1': {
                    'PRESS': 'TurnOn',  # Tuya action
                    'RELEASE': None,  # No-op. Technically optional.
                },
                'BTN_3': {
                    'PRESS': 'TurnOff',
                    'RELEASE': None,
                },
            }
        }
    }
}

```

Both Tuya and Bond actions may be configured on the same Lutron ID. This means
that the same button on a Pico remote can trigger both a Bond device and a
Tuya device at the same time.

In addition, the `tuya` and `bond` keys in the config also accept a list of
actions. This allows a single Lutron action to control any number of Bond
and any number of Tuya devices simultaneously. Kinda like scenes!

```python
LUTRON_MAPPING = {
    21: {  # <-- This number is the Lutron Integration ID
        'name': 'Pico 1',  # Optional, but helps readability
        'tuya': [
            {
                'name': 'Tuya Switch 1',
                # ...
            },
            {
                'name': 'Tuya Switch 2',
                # ...
            }
        ],
        'bond': [
            {
                'name': 'Bond Device 1',
                # ...
            },
            {
                'name': 'Bond Device 2',
                # ...
            }
        ]
    }
}

```

This has only been tested with Lutron Pico remotes. To see button mappings
for a variety of different remotes, look on page 124 of the [Lutron
Integration Protocol document 040249](https://www.lutron.com/TechnicalDocumentLibrary/040249.pdf)

The [Bond API docs](http://docs-local.appbond.com/) may also be helpful for
determining how to control specific devices.


# Determining Lutron and Bond IDs

A couple helper scripts are available to determine the various IDs of the
Lutron and Bond systems.

## To figure out Lutron IDs

```bash
python3 -m lutronbond.lutron
```

This will log events to stdout when Lutron buttons are pressed. Just run that,
and start pressing buttons on Pico remotes to figure out what IDs to use.

## To figure out Bond IDs

```bash
python3 -m lutronbond.bond
```

This will dump a lot of info in JSON format to stdout about the Bond Bridge.
Reading this should provide the required IDs.


## To figure out Tuya connection details

This bridge communicates with Tuya devices over the local network, requiring
no Internet connection. Getting the appropriate connection details is somewhat
involved, though.

We depend on [tinytuya](https://github.com/jasonacox/tinytuya) for TuyaCloud
support. Please see [the TinyTuya Docs](https://github.com/jasonacox/tinytuya#setup-wizard---getting-local-keys) for detailed set up instructions. The
TinyTuya Setup Wizard will provide all of the connection details needed
to configure this bridge with your Tuya devices.

At this time, only support for smart switches is provided. As such, only the
actions `TurnOn` and `TurnOff` are implemented.


# Use with Two Lutron Bridges

Some larger homes may have more than 75 Caseta devices, the limit of what can be paired
to a single bridge. While not officially suported by Lutron, many people have had success
utilizing multiple bridges to work around this. This integration supports up to two bridges
simulatneously (and theoretically more, but I don't have an immediate need for that).

To use a second bridge, provide the following environment variable:

```bash
export LB_LUTRON_BRIDGE2_ADDR="<IP address of second Lutron bridge>"
```

In `config.py` specify an additional config for the second bridge, in this format:

```python
LUTRON2_MAPPING = {
    # Format is identical to that in LUTRON_MAPPING,
    # but use Integration IDs from the second Lutron bridge.
}
```

# Reliability Tuning

In real-world testing, sometimes requests to the Bond Bridge time out or
experience high latency. The following environment variables control settings
that may help alleviate these issues:

```
LB_BOND_KEEPALIVE_INTERVAL=0
```
This will periodically ping the Bond Bridge to ensure there is a valid route
to it on the local network. The value is the number of seconds between pings. A
value of `0` (the default) disables this feature. A reasonable value is 60-180.

```
LB_BOND_RETRY_COUNT=5
```
The number of times to retry a request to the Bond Bridge in the case of a
connection error. A higher value will increase reliability, at the cost of
higher latency. Default value is 5.

# Development & Testing

You can change the log level to see more (or less) output from the program.

```bash
export LB_LOG_LEVEL="DEBUG"
```

The following values are supported (from most to least verbose): `DEBUG`,
`INFO`, `WARNING`, `ERROR`.

To set up development dependencies:
```bash
source venv/bin/activate
pip install -r requirements_dev.txt
```

Run lint:
```bash
flake8
```

Run static analysis:
```bash
mypy -p lutronbond -p tests
```

Run unit tests:
```bash
pytest
```

Generate a coverage report:
```bash
pytest --cov --cov-report=html
```
