# bobcatpy

A Python library to interact with the Bobcat Helium miner diagnostics API.

BobcatPy provides an alternative way to interact with the Bobcat diagnoser interface and includes some additional functionality for easy troubleshooting and maintenance.

## Usage

```python
import bobcatpy

# Define your Bobcat instance. Replace with your actual hotspot IP
b = Bobcat("192.168.1.150")

# Get statuses
b.temps()
b.sync_status()
b.miner_status()

# Reboot the hotspot
b.reboot()

# Fastsync the hotspot
b.fastsync()

# Resync the hotspot
b.resync()

# Reset the hotspot
b.reset()

# Run diagnostics
b.diagnose()
```


