# Lutron-Bond

Connector between Lutron Caseta SmartBridge Pro and Bond Bridge.

Docs are WIP.


# Requirements

* Python 3.10
* [Lutron Caseta SmartBridge Pro](https://www.casetawireless.com/us/en/pro-products) (will not work with non-Pro version)
* [Bond Bridge](https://bondhome.io/product/bond-bridge/)


# Usage

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export LUTRON_BRIDGE_ADDR="<IP address of Lutron bridge>"
export BOND_BRIDGE_ADDR="<IP address of Bond Bridge>"
export BOND_BRIDGE_API_TOKEN="<Bond Bridge API token>"
./run.sh
```


# Configuration

Look at [blob/main/lutronbond/config.py](config.py) for example configuration.
