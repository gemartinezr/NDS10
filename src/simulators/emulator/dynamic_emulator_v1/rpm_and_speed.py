import random
import time
import can

# Configure CAN interface
channel = "can0"
bus = can.interface.Bus(channel=channel, bustype="socketcan")

# Constants
PID_RPM = 0x0C
PID_SPEED = 0x0D
RESPONSE_ID = 0x7E8
EMULATOR_FLAG = 0xDD

def build_response(pid, value):
    if pid == PID_RPM:
        raw = int(value * 4)
        payload = [raw >> 8, raw & 0xFF]
    elif pid == PID_SPEED:
        payload = [int(value)]
    else:
        return None

    # Construct response: [length, 0x41, PID, ...payload..., padded to 8 bytes]
    data = [len(payload) + 2, 0x41, pid] + payload
    if len(data) < 8:
        data += [0x00] * (8 - len(data))
    if len(payload) <= 5:
        data[-1] = EMULATOR_FLAG
    return data

print("Fast Emulator Running: varying RPM and Speed")
try:
    while True:
        rpm = random.randint(800, 5500)
        speed = random.randint(0, 130)

        bus.send(can.Message(arbitration_id=RESPONSE_ID, data=build_response(PID_RPM, rpm), is_extended_id=False))
        bus.send(can.Message(arbitration_id=RESPONSE_ID, data=build_response(PID_SPEED, speed), is_extended_id=False))

        # 20ms delay: adjust for higher/lower response frequency
        time.sleep(0.02)

except KeyboardInterrupt:
    print("Stopped by user.")


"""
Test 4

- Close socketcanBus properly
- Adjust frequency so it's slightly higher than Freematics emulator
- Only send increasing random values
- RPM = 150,  Speed = 150   are Freematics constant values. (Only will vary these in a 10+/- to trigger activity)


How can this be done? 
- Introduce delays or jitter in response times to test threshold tolerance of FMC003. (don't include it yet)
"""