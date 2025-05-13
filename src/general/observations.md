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



#### FMC003 test behavior

```
# device goes into protect mode, which blocks the PIDs request loop

TSYNC:^I Last Sync:NTP at 1747129070s, NTP cnt:1, Fails:0$
[2025.05.13 10:03:13]-[SLEEP]^ISleep:0, not allowed! Reason:Disabled by CFG$
[2025.05.13 10:03:13]-[LiPo]^IWARNING @ 877:In Protection mode! Left:350s$    <--------------------
[2025.05.13 10:03:13]-[LiPo]^IBatState: 1 FSMState: PROTECT ChargerIC: OFF ExtV: 15302 BatV: 4119 BatI: 0$
[2025.05.13 10:03:13]-[LiPo]^IBatState: 1 FSMState: PROTECT ChargerIC: OFF ExtV: 15302 BatV: 4119 BatI: 0$
[2025.05.13 10:03:15]-[REC.SEND.1]^IMode: 4/Unknown on Stop. Next periodic data sending: 6 / 120$
[2025.05.13 10:03:18]-[LiPo]^IWARNING @ 877:In Protection mode! Left:345s$
[2025.05.13 10:03:18]-[LiPo]^IBatState: 1 FSMState: PROTECT ChargerIC: OFF ExtV: 15302 BatV: 4119 BatI: 0$
[2025.05.13 10:03:19]-[OVERSPD]^IScenario disabled!$
[2025.05.13 10:03:19]-[OBD.OEM]^I^I*** Vehicle Not supported! Please, contact to support! ***$
[2025.05.13 10:03:23]-[SLEEP]^ISleep:0, not allowed! Reason:Disabled by CFG$
[2025.05.13 10:03:23]-[LiPo]^IWARNING @ 877:In Protection mode! Left:340s$
[2025.05.13 10:03:23]-[LiPo]^IBatState: 1 FSMState: PROTECT ChargerIC: OFF ExtV: 15302 BatV: 4119 BatI: 0$
[2025.05.13 10:03:24]-[TRIP]^IPeriodic info: State -> Moving. Spd:0km/h, Mov:NO, Ign:ON, TripBT:0$
[2025.05.13 10:03:24]-[TRIP]^IDistance driven: 4096 km$
[2025.05.13 10:03:25]-[REC.SEND.1]^IMode: 4/Unknown on Stop. Next periodic data sending: 16 / 120$
[2025.05.13 10:03:25]-[AXL.CLBR]^IAutocalibration check. Iterations left:500$
```












