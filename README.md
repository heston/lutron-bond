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

* [TuyaCloud](https://www.tuya.com/) device (like a smart outlet or lightbulb). Tuya is a white-label manufacturer, and their devices are sold under many names. Tuya devices work with the *Smart Life* app.


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

To get started, try running it on your local workstation:

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
# Contents of .env file
export LB_LUTRON_BRIDGE_ADDR="<IP address of Lutron bridge>"
export LB_BOND_BRIDGE_ADDR="<IP address of Bond Bridge>"
export LB_BOND_BRIDGE_API_TOKEN="<Bond Bridge API token>"
```

`run.sh` will look for this file and load it for you.


# Configuration

Each home's configuration will be different. Look at
[config.py](blob/main/lutronbond/config.py) for comprehensive examples.

Any event from any Lutron switch or remote can be configured (in addition to
its normal function) to control a Bond, Tuya, and/or other Lutron
device.

Further down in this file it describes how to find the various IDs and metadata
needed by the config file.

## Configuration Options

**To trigger a Bond action:**

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

To see all the Bond actions available, take a look at the
[Action class here](https://github.com/bondhome/bond-async/blob/master/bond_async/action.py#L14).
The [Bond API docs](http://docs-local.appbond.com/) may also be helpful for
determining how to control specific devices. Not all devices support all
actions, so some trial-and-error may be needed.

Note that when using Lutron hard-wired switches, it's not possible to tell
which buttons were pressed, only what the last output level was. As such,
specifying actions is a little different. This format applies to all action
types, not just Bond.

```python
LUTRON_MAPPING = {
    21: {  # <-- This number is the Lutron Integration ID
        'name': 'Light',  # This is technically optional, but helps readability
        'bond': {
            'id': '6409d2a2',  # The ID of the Bond device (may be 8 or 16 chars)
            'actions': {
                'ANY': {  # <-- Special value for all output actions
                    'SET_LEVEL': { # <-- Output action
                        '100.00': 'TurnLightOn',  # Bond action when output is at 100.00%
                        '0.00': 'TurnLightOff',  # Bond action when output is at 0.00%
                    }
                }
            }
        }
    }
}

```

See page 6 of the [Lutron Integration Protocol document 040249](https://www.lutron.com/TechnicalDocumentLibrary/040249.pdf)
for details on the syntax of monitoring levels.

**To trigger a Tuya action:**

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

**To trigger a Lutron action:**

```python
LUTRON_MAPPING = {
    21: {  # <-- This number is the Lutron Integration ID of the trigger
        'name': 'My Lutron Device',  # Optional, but helps readability
        'lutron': {
            'id': 40,  # The Lutron Integration ID of the target
            'name': 'My Other Lutron Device', # Optional, but helps readability
            'bridge': 1,  # May be 1 or 2, indicating the Lutron bridge of the target.
                          # See "Use with Two Lutron Bridges" in the docs, below.
                          # Optional. If omitted, 1 is assumed.
            'actions': {
                # This is an action for a device trigger (like a Pico remote) and
                # a device target (another Pico remote)
                'BTN_1': {
                    'PRESS': {
                        'BTN_2': 'Press',
                        # When button 1 on device 21 is pressed, simulate pressing
                        # button 2 on device 40
                    }.
                },
                # This is an action for a device trigger (like a Pico remote) and
                # an output target (like a wall switch)
                'BTN_3': {
                    'PRESS': {
                        'SET_LEVEL': '100',
                        # When button 3 on device 21 is pressed, set the output level of
                        # device 40 to 100 (fully on)
                    }
                },
                # This is an action for an output trigger and a device target
                'ANY': {  # <-- the ANY keyword is always used for output triggers
                    'SET_LEVEL': {
                        '100': {
                            'BTN_1': 'Press',
                            # When device 21 is set to output level 100, simulate pressing
                            # button 1 on device 40
                        },
                    }
                },
                # This is an action for an output trigger and an output target
                'ANY': {
                    'SET_LEVEL': {
                        '100': {
                            'SET_LEVEL': '0',
                            # When device 21 is set to output level 100 (fully on),
                            # set the output level of device 40 to 0 (fully off)
                        },
                        '0': {
                            'SET_LEVEL': '100',
                            # When device 21 is set to output level 0, set the output level of
                            # device 40 to 100
                        }
                    }
                },
            }
        }
    }
}

```

Tuya, Bond, and Lutron actions may be configured on the same Integration ID.
This means that the same button on a Pico remote can trigger actions across many
devices at the same time. Actions are all run concurrently, to minimize delays.

In addition, the `tuya`, `bond`, and `lutron` keys in the config also accept a
list of actions. This allows a single Lutron event to control any number of
Bond, Tuya, and Lutron devices simultaneously.

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
        ],
        'lutron': [
            {
                'name': 'Lutron Device 1',
                # ...
            },
            {
                'name': 'Lutron Device 2',
                # ...
            }
        ]
    }
}

```

This has been tested with Lutron Pico remotes and Lutron Caseta wall switches.
Lutron produces many other types of devices, which have not been tested.
To see button mappings for a variety of different remotes, look on page 124 of
the [Lutron Integration Protocol document 040249](https://www.lutron.com/TechnicalDocumentLibrary/040249.pdf).


# Determining Lutron, Bond, and Tuya IDs

Helper scripts are available to determine the various IDs and other metadata of
the devices that may be monitored and controlled.

## To figure out Lutron IDs

```bash
python3 -m lutronbond.lutron
```

This will log events to stdout when Lutron buttons are pressed or switches are
activated. Just run it and start pressing buttons on Lutron devices to
figure out what IDs to use.

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

Some larger homes may have more than 75 Caseta devices, the limit of what can be
paired to a single bridge. While not officially suported by Lutron, many people
have had success utilizing multiple bridges to work around this. This
integration supports up to two bridges simulatneously (and theoretically more,
but I don't have an immediate need for that).

To use a second bridge, provide the following environment variable:

```bash
export LB_LUTRON_BRIDGE2_ADDR="<IP address of second Lutron bridge>"
```

In `config.py` specify an additional config for the second bridge, in this
format:

```python
LUTRON2_MAPPING = {
    # Format is identical to that in LUTRON_MAPPING,
    # but use Integration IDs from the second Lutron bridge.
}
```

# Advanced Settings

### Performance Tuning

In real-world testing, sometimes requests to the Bond Bridge or Tuya device
timeout or experience high latency. The following environment variables control
settings that may help alleviate these issues. You may need to fiddle with the
values to find ones that work. On a healthy network, the defaults should not
need to be changed.

```bash
LB_BOND_KEEPALIVE_INTERVAL=0
```
This will periodically ping the Bond Bridge to ensure there is a valid route
to it on the local network. The value is the number of seconds between pings. A
value of `0` (the default) disables this feature. A reasonable value is 60-180.

```bash
LB_BOND_RETRY_COUNT=5
```
The number of times to retry a request to the Bond Bridge in the case of a
connection error. A higher value will increase reliability, at the cost of
higher latency. Default value is 5.

```bash
LB_TUYA_RETRY_COUNT=3
```
The number of times to retry a request to a Tuya device in case of a
connection error. A higher value will increase reliability, at the cost of
higher latency. Default value is 3.

```bash
LB_TUYA_CONNECTION_TIMEOUT=3
```
The number of seconds to wait for a successful connection to a Tuya device
before timing out. Default value is 3.

### Other Settings

```bash
LB_LOG_LEVEL="INFO"
```
You can change the log level to see more (or less) output from the program.
The following values are supported (from most to least verbose): `DEBUG`,
`INFO`, `WARNING`, `ERROR`. Default value is `INFO`.


# Development & Testing

The following instructions are for developers wanting to add new features
in this project.

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
