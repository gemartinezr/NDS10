
import time
import can

# Setup
channel = "can0"
bus = can.interface.Bus(channel=channel, bustype="socketcan")

# PID config
PID_RPM = 0x0C
PID_SPEED = 0x0D
PID_AIR_TEMP = 0x46
PID_FUEL_RATE = 0x4E
BLOCKED_PIDS = {0x52}
RESPONSE_ID = 0x7E8
EMULATOR_FLAG = 0xDD

# Timing
cycle_duration_sec = 0.085
cycles_per_minute = int(60 / cycle_duration_sec)
cycle_10min = 10 * cycles_per_minute
accel_duration = 5 * cycles_per_minute
decel_duration = 5 * cycles_per_minute
num_batches = 18  # 3 hours total
total_cycles = num_batches * cycle_10min

# Ranges
min_rpm = 1200
max_rpm = 3000
min_speed = 0
max_speed = 100
min_air_temp = -10
max_air_temp = 35
min_fuel_rate = 1
max_fuel_rate = 30

def build_response(pid, value):
    if pid in BLOCKED_PIDS:
        return None

    if pid == PID_RPM:
        raw = int(value * 4)
        payload = [raw >> 8, raw & 0xFF]
    elif pid == PID_SPEED:
        payload = [int(value)]
    elif pid == PID_AIR_TEMP:
        signed_byte = int(value) & 0xFF
        payload = [signed_byte]
    elif pid == PID_FUEL_RATE:
        raw = int(value * 100)
        payload = [raw >> 8, raw & 0xFF]
    else:
        return None

    data = [len(payload) + 2, 0x41, pid] + payload
    while len(data) < 8:
        data.append(0x00)

    if len(payload) <= 5:
        data[-1] = EMULATOR_FLAG

    return data

try:
    print("Test 12: 3-hour emulator running in 10-min batches. Press Ctrl+C to stop.")
    for cycle in range(total_cycles):
        batch_index = cycle % cycle_10min

        if batch_index < accel_duration:
            rpm = min_rpm + ((max_rpm - min_rpm) * batch_index / accel_duration)
            speed = min_speed + ((max_speed - min_speed) * batch_index / accel_duration)
        else:
            decel_index = batch_index - accel_duration
            rpm = max_rpm - ((max_rpm - min_rpm) * decel_index / decel_duration)
            speed = max_speed - ((max_speed - min_speed) * decel_index / decel_duration)

        # Update ambient air temp and fuel rate every 3 seconds
        if cycle % int(3 / cycle_duration_sec) == 0:
            air_temp = min_air_temp + ((max_air_temp - min_air_temp) * (cycle % cycle_10min) / cycle_10min)
            fuel_rate = min_fuel_rate + ((max_fuel_rate - min_fuel_rate) * (cycle % cycle_10min) / cycle_10min)

        for pid, value in [
            (PID_RPM, rpm),
            (PID_SPEED, speed),
            (PID_AIR_TEMP, air_temp),
            (PID_FUEL_RATE, fuel_rate)
        ]:
            frame = build_response(pid, value)
            if frame:
                msg = can.Message(arbitration_id=RESPONSE_ID, data=frame, is_extended_id=False)
                bus.send(msg)
                time.sleep(0.01)

        time.sleep(cycle_duration_sec)

except KeyboardInterrupt:
    print("Test 12 Emulator stopped.")
finally:
    bus.shutdown()
