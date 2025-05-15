import random
import time
import can

# CAN setup
channel = "can0"
bus = can.interface.Bus(channel=channel, bustype="socketcan")

PID_RPM = 0x0C
PID_SPEED = 0x0D
RESPONSE_ID = 0x7E8
EMULATOR_FLAG = 0xDD

# Initialize increasing variables
current_rpm = 1600  # start > 150 * 4
current_speed = 20

def build_response(pid, value):
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
    print("Test 4 Emulator Running. Press Ctrl+C to stop.")
    while True:
        # Increment slowly and randomly
        current_rpm += random.randint(5, 20)
        current_speed += random.randint(1, 5)

        # Clamp values to reasonable upper limits
        current_rpm = min(current_rpm, 6000)
        current_speed = min(current_speed, 130)

        bus.send(can.Message(arbitration_id=RESPONSE_ID, data=build_response(PID_RPM, current_rpm), is_extended_id=False))
        bus.send(can.Message(arbitration_id=RESPONSE_ID, data=build_response(PID_SPEED, current_speed), is_extended_id=False))

        time.sleep(0.015)  # ~15ms, faster than Freematics

except KeyboardInterrupt:
    print("Shutting down gracefully.")
finally:
    bus.shutdown()
