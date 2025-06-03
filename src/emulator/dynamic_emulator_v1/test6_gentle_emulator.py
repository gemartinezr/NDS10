import random
import time
import can

channel = "can0"
bus = can.interface.Bus(channel=channel, bustype="socketcan")

PID_RPM = 0x0C
PID_SPEED = 0x0D
RESPONSE_ID = 0x7E8
EMULATOR_FLAG = 0xDD

current_rpm = 1600
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
    print("Gentle Emulator Running — RPM & Speed only. Press Ctrl+C to stop.")
    while True:
        current_rpm = min(current_rpm + random.randint(2, 10), 5000)
        current_speed = min(current_speed + random.randint(0, 3), 130)

        for pid, value in [(PID_RPM, current_rpm), (PID_SPEED, current_speed)]:
            msg = can.Message(
                arbitration_id=RESPONSE_ID,
                data=build_response(pid, value),
                is_extended_id=False
            )
            bus.send(msg)

        time.sleep(0.05)  # ~50ms — Freematics pace

except KeyboardInterrupt:
    print("Stopping emulator...")
finally:
    bus.shutdown()
