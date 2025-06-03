import random
import time
import can

# Setup
channel = "can0"
bus = can.interface.Bus(channel=channel, bustype="socketcan")

# Constants
PID_RPM = 0x0C
PID_SPEED = 0x0D
BLOCKED_PIDS = {0x52}  # silence 0x52
RESPONSE_ID = 0x7E8
EMULATOR_FLAG = 0xDD

# Initial values
current_rpm = 1600
current_speed = 20

def build_response(pid, value):
    if pid in BLOCKED_PIDS:
        return None

    if pid == PID_RPM:
        raw = int(value * 4)
        payload = [raw >> 8, raw & 0xFF]
    elif pid == PID_SPEED:
        payload = [int(value)]
    else:
        return None

    data = [len(payload) + 2, 0x41, pid] + payload
    if len(data) < 8:
        data += [0x00] * (8 - len(data))
    if len(payload) <= 5:
        data[-1] = EMULATOR_FLAG
    return data

try:
    print("Test 7: Gentle Emulator running (PID 0x52 silenced, ~60ms delay)")
    while True:
        current_rpm = min(current_rpm + random.randint(2, 10), 5000)
        current_speed = min(current_speed + random.randint(0, 3), 130)

        for pid, value in [(PID_RPM, current_rpm), (PID_SPEED, current_speed)]:
            frame = build_response(pid, value)
            if frame:
                msg = can.Message(arbitration_id=RESPONSE_ID, data=frame, is_extended_id=False)
                bus.send(msg)

        time.sleep(0.06)  # ~60ms delay

except KeyboardInterrupt:
    print("Stopping emulator.")
finally:
    bus.shutdown()
