import os


def get_env_str(name, default=None):
    return os.environ.get(name, default)


def get_env_int(name, default=None):
    raw = get_env_str(name, default)
    try:
        return int(raw, 10)
    except ValueError:
        return default


LUTRON_BRIDGE_ADDR = get_env_str('LUTRON_BRIDGE_ADDR', '192.168.86.247')
BOND_BRIDGE_ADDR = get_env_str('BOND_BRIDGE_ADDR', '192.168.86.60')
BOND_BRIDGE_API_TOKEN = get_env_str('BOND_BRIDGE_API_TOKEN', '913ca00159de3da0')


LUTRON_BOND_MAPPING = {
    # Lutron Integration ID->Bond Device
    -1: {
        'bondID': '6409d2a2',
        'actions': {
            'BTN_1': {
                'PRESS': 'TurnLightOn',
            },
            'BTN_2': {
                'PRESS': 'ToggleLight',
            },
            'BTN_3': {
                'PRESS': 'TurnLightOff',
            },
            'BTN_RAISE': {
                'PRESS': 'StartDimmer',
                'RELEASE': 'Stop',
            },
            'BTN_LOWER': {
                'PRESS': 'StartDimmer',
                'RELEASE': 'Stop',
            }
        }
    },
    # TBD: fan pico
    21: {
        'bondID': '6409d2a2',
        'actions': {
            'BTN_1': {
                'PRESS': {
                    'SetSpeed': 2,
                },
            },
            # TODO: Maybe support macros. Something like this:
            #
            # 'BTN_2': {
            #     'PRESS': [
            #         'TurnOn',
            #         {'SetSpeed': 2},
            #     ]
            # }
            'BTN_2': {
                'PRESS': 'ToggleDirection'
            },
            'BTN_3': {
                'PRESS': 'TurnOff',
            },
            'BTN_RAISE': {
                'PRESS': {
                    'SetSpeed': 3,
                },
            },
            'BTN_LOWER': {
                'PRESS': {
                    'SetSpeed': 1,
                },
            }
        }
    }
}
