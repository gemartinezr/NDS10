#### Freematics emulator 

##### Operation modes  
The Freematics OBD-II Emulator can operate in different modes:

1. ELM327 interface mode (accepts AT/01xx commands from a PC).

2. ECU emulation mode (acts like a car ECU, responding to OBD-II requests, not sending them).

From your setup, your emulator is probably configured to act like a car ECU, simulating a real vehicle. This means:
It doesn’t expect you (the PC) to send ATZ. It expects a diagnostic scanner (like the FMC003) to send PID requests, and it will reply.

##### Empty response from `scanner_simulator.py`  
Most Likely Reasons for Empty Response:
1. The emulator is waiting for a full OBD-II request frame, not ASCII text like 010D\r
Freematics emulator, when in ECU emulation mode, may not support the plain ELM327-style ASCII interface. Instead, it might be expecting raw OBD-II CAN frames, like the FMC003 would send.

2. It may expect traffic over a specific CAN ID, format, or protocol
If it’s simulating an ECU over CAN, it likely expects ISO-TP or raw CAN 11-bit frame format, not text strings.

3. The emulator is passive — it doesn’t generate responses unless queried correctly
Some Freematics firmware versions or configurations just wait silently for properly formatted OBD-II frames.


#### FMC003

```
sudo systemctl stop ModemManager # stop ModemManager since it tries to claim ownership of the MiniDevice

sudo picocom -b 115200 /dev/ttyUSB0   # to log out Mini device activity from linux host 
```  

/dev/ttyUSB0 is a diagnostic/logging serial port from the FMC003
- Trip status
- Battery status
- Modem AT command responses
- LTE connection info
- Periodic state logs like speed, motion, sleep status, etc.



#### GPT last useful prompt

I have the following devices linked with an OBD-II splitter:
- Usb2Can Korlan   
- Freematics OBD-II emulator   
- Teltonika FMC003 device  


I have the parameters that conform a baseline configuration
