import pytest


def test_get_env__empty_default(import_config):
    config = import_config()

    with pytest.raises(RuntimeError) as e:
        config.get_env('MY_ENV_VAR')

    assert str(e.value) == (
        'Required configuration not found in environment: '
        'MY_ENV_VAR. Please set an environment variable with this '
        'name and try again.'
    )


def test_get_env__empty_str_default(import_config):
    config = import_config()

    with pytest.raises(RuntimeError) as e:
        config.get_env('MY_ENV_VAR', '')

    assert str(e.value) == (
        'Required configuration not found in environment: '
        'MY_ENV_VAR. Please set an environment variable with this '
        'name and try again.'
    )


def test_get_env__set_default(import_config):
    config = import_config()

    assert 'var' == config.get_env('MY_ENV_VAR', 'var')


def test_env__in_environment(env, import_config):
    env('LUTRON_BRIDGE_ADDR', '10.0.0.10')
    env('BOND_BRIDGE_ADDR', '10.0.0.30')
    env('BOND_BRIDGE_API_TOKEN', 'asdfasdf')

    config = import_config()

    assert config.LUTRON_BRIDGE_ADDR == '10.0.0.10'
    assert config.BOND_BRIDGE_ADDR == '10.0.0.30'
    assert config.BOND_BRIDGE_API_TOKEN == 'asdfasdf'


def test_env__not_in_environment(env, import_config):
    env('LB_BOND_BRIDGE_API_TOKEN', None)

    with pytest.raises(RuntimeError) as e:
        import_config()

    assert str(e.value) == (
        'Required configuration not found in environment: '
        'LB_BOND_BRIDGE_API_TOKEN. Please set an environment variable with '
        'this name and try again.'
    )
