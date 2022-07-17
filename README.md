# bobcatpy

A Python library to interact with the Bobcat Helium miner diagnostics API.

BobcatPy provides an alternative way to interact with the Bobcat diagnoser interface and includes some additional functionality for easy troubleshooting and maintenance.


## Installation

`bobcatpy` is available through PyPi.

```
pip install bobcatpy
```

## Usage

```python
import bobcatpy

# Define your Bobcat instance. Replace with your actual hotspot IP
b = Bobcat("192.168.1.150")

# Get statuses
b.temps()
b.miner_status()

# Reboot the hotspot
b.reboot()

# Reset the hotspot
b.reset()
```
