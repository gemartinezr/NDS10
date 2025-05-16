import time
import can

# Setup
channel = "can0"
bus = can.interface.Bus(channel=channel, bustype="socketcan")

# Constants
PID_RPM = 0x0C
PID_SPEED = 0x0D
BLOCKED_PIDS = {0x52}
RESPONSE_ID = 0x7E8
EMULATOR_FLAG = 0xDD

# Timing
cycle_duration_sec = 0.07  # ~70ms per cycle
cycles_per_minute = int(60 / cycle_duration_sec)
total_minutes = 30
total_cycles = total_minutes * cycles_per_minute

# Phases
accel_duration = 10 * cycles_per_minute
cruise_duration = 15 * cycles_per_minute
decel_duration = 5 * cycles_per_minute

# Ranges
min_rpm = 1200
max_rpm = 4000
min_speed = 0
max_speed = 110

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
    while len(data) < 8:
        data.append(0x00)

    if len(payload) <= 5:
        data[-1] = EMULATOR_FLAG

    return data

try:
    print("Test 10: Long-run RPM/Speed pattern. Press Ctrl+C to stop.")
    for cycle in range(total_cycles):
        if cycle < accel_duration:
            rpm = min_rpm + ((max_rpm - min_rpm) * cycle / accel_duration)
            speed = min_speed + ((max_speed - min_speed) * cycle / accel_duration)
        elif cycle < accel_duration + cruise_duration:
            rpm = max_rpm
            speed = max_speed
        else:
            decel_cycle = cycle - (accel_duration + cruise_duration)
            rpm = max_rpm - ((max_rpm - min_rpm) * decel_cycle / decel_duration)
            speed = max_speed - ((max_speed - min_speed) * decel_cycle / decel_duration)

        for pid, value in [(PID_RPM, rpm), (PID_SPEED, speed)]:
            frame = build_response(pid, value)
            if frame:
                msg = can.Message(arbitration_id=RESPONSE_ID, data=frame, is_extended_id=False)
                bus.send(msg)
                time.sleep(0.01)

        time.sleep(cycle_duration_sec)

except KeyboardInterrupt:
    print("Emulator stopped by user.")
finally:
    bus.shutdown()
