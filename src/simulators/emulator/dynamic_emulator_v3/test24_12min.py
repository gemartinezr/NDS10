
import time
import can
from datetime import datetime

# Setup
channel = "can0"
bus = can.interface.Bus(channel=channel, bustype="socketcan")

# PID config
PID_RPM = 0x0C
PID_SPEED = 0x0D
PID_AIR_TEMP = 0x46
PID_FUEL_RATE = 0x4E
PID_DTC_DISTANCE = 0x31
PID_ENGINE_LOAD = 0x04
PID_COOLANT_TEMP = 0x05
PID_OIL_TEMP = 0x5C
PID_FUEL_LEVEL = 0x2F
BLOCKED_PIDS = {0x52}
RESPONSE_ID = 0x7E8
EMULATOR_FLAG = 0xDD

# Timing
cycle_duration_sec = 0.08
max_runtime_sec = 12 * 60  # changed from 40 to 12 minutes
cycles_per_minute = int(60 / cycle_duration_sec)
cycle_12min = 12 * cycles_per_minute
accel_duration = 6 * cycles_per_minute   # half of 12 minutes
decel_duration = 6 * cycles_per_minute   # half of 12 minutes

# Ranges
min_rpm = 1200
max_rpm = 3000
min_speed = 0
max_speed = 100
min_air_temp = 10
max_air_temp = 35
min_fuel_rate = 0
max_fuel_rate = 7
min_engine_load = 10
max_engine_load = 80
min_coolant_temp = 60
max_coolant_temp = 100
min_oil_temp = 70
max_oil_temp = 110
min_fuel_level = 20
max_fuel_level = 80

def build_response(pid, value):
    if pid in BLOCKED_PIDS:
        return None

    if pid == PID_RPM:
        raw = int(value * 4)
        payload = [raw >> 8, raw & 0xFF]
    elif pid == PID_SPEED:
        payload = [int(value)]
    elif pid == PID_AIR_TEMP:
        payload = [int(value) & 0xFF]
    elif pid == PID_FUEL_RATE:
        raw = int(value * 100)
        payload = [raw >> 8, raw & 0xFF]
    elif pid == PID_DTC_DISTANCE:
        raw = int(value)
        payload = [raw >> 8, raw & 0xFF]
    elif pid in [PID_ENGINE_LOAD, PID_FUEL_LEVEL, PID_OIL_TEMP, PID_COOLANT_TEMP]:
        payload = [int(value)]
    else:
        return None

    frame_body = [0x41, pid] + payload
    data = [len(frame_body)] + frame_body

    while len(data) < 8:
        data.append(0x00)

    if len(payload) <= 5 and data[-1] == 0x00:
        data[-1] = EMULATOR_FLAG

    return data

try:
    start_time = time.time()
    start_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Test 24: Starting at {start_str}. Duration: 12 minutes.")

    cycle = 0
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time >= max_runtime_sec:
            end_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"Test 24 completed at {end_str}.")
            break

        batch_index = cycle % cycle_12min

        # Ramp up/down over 20-minute cycle
        if batch_index < accel_duration:
            progress = batch_index / accel_duration
        else:
            decel_index = batch_index - accel_duration
            progress = 1 - (decel_index / decel_duration)

        rpm = min_rpm + (max_rpm - min_rpm) * progress
        speed = min_speed + (max_speed - min_speed) * progress
        air_temp = min_air_temp + (max_air_temp - min_air_temp) * progress
        fuel_rate = min_fuel_rate + (max_fuel_rate - min_fuel_rate) * progress
        engine_load = min_engine_load + (max_engine_load - min_engine_load) * progress
        coolant_temp = min_coolant_temp + (max_coolant_temp - min_coolant_temp) * progress
        oil_temp = min_oil_temp + (max_oil_temp - min_oil_temp) * progress
        fuel_level = max_fuel_level - (max_fuel_level - min_fuel_level) * progress

        dtc_distance = int((elapsed_time / max_runtime_sec) * 10000)

        for pid, value in [
            (PID_RPM, rpm),
            (PID_SPEED, speed),
            (PID_AIR_TEMP, air_temp),
            (PID_FUEL_RATE, fuel_rate),
            (PID_DTC_DISTANCE, dtc_distance),
            (PID_ENGINE_LOAD, engine_load),
            (PID_COOLANT_TEMP, coolant_temp),
            (PID_OIL_TEMP, oil_temp),
            (PID_FUEL_LEVEL, fuel_level)
        ]:
            frame = build_response(pid, value)
            if frame:
                msg = can.Message(arbitration_id=RESPONSE_ID, data=frame, is_extended_id=False)
                bus.send(msg)
                time.sleep(0.015)

        time.sleep(cycle_duration_sec)
        cycle += 1

except KeyboardInterrupt:
    print("Test 24 Emulator stopped manually.")
finally:
    bus.shutdown()
