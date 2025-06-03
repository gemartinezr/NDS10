import time
import can

channel = "can0"
bus = can.interface.Bus(channel=channel, bustype="socketcan")

PID_RPM = 0x0C
PID_SPEED = 0x0D
BLOCKED_PIDS = {0x52}
RESPONSE_ID = 0x7E8
EMULATOR_FLAG = 0xDD

# Initial values
current_rpm = 1500
current_speed = 20
cycle_count = 0

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
    print("Test 8: Linear RPM + slow Speed increment. Press Ctrl+C to stop.")
    while True:
        cycle_count += 1

        # Linear growth
        current_rpm = min(current_rpm + 1, 6000)
        if cycle_count % 20 == 0:
            current_speed = min(current_speed + 1, 130)

        # Send frames
        for pid, value in [(PID_RPM, current_rpm), (PID_SPEED, current_speed)]:
            frame = build_response(pid, value)
            if frame:
                msg = can.Message(arbitration_id=RESPONSE_ID, data=frame, is_extended_id=False)
                bus.send(msg)

        time.sleep(0.06)  # ~60 ms delay

except KeyboardInterrupt:
    print("Stopping emulator.")
finally:
    bus.shutdown()
