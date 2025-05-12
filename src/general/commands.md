#### System

```bash
# see connected usb devices
lsusb

```


#### Freematics emulator

```bash
udevadm info --name=/dev/ttyUSB0 --query=all  # confirm if emulator with name ttyUSB0 is reachable

sudo picocom -b 38400 /dev/ttyUSB0

```