import time
import can
import csv
from datetime import datetime

# Setup
channel = "can0"
bus = can.interface.Bus(channel=channel, bustype="socketcan")

# PID config
PID_MAP = {
    0x0C: "RPM",
    0x0D: "Speed",
    0x46: "AirTemp",
    0x4E: "FuelRate",
    0x31: "DTC_Distance",
    0x04: "EngineLoad",
    0x05: "CoolantTemp",
    0x5C: "OilTemp",
    0x2F: "FuelLevel",
}
BLOCKED_PIDS = {0x52}
RESPONSE_ID = 0x7E8
EMULATOR_FLAG = 0xDD

# Timing
cycle_duration_sec = 0.08
max_runtime_sec = 20 * 60  # 20 minutes

# Ranges
RANGES = {
    0x0C: (1200, 3000),
    0x0D: (0, 100),
    0x46: (10, 35),
    0x4E: (0, 7),
    0x31: (0, 10000),
    0x04: (10, 80),
    0x05: (60, 100),
    0x5C: (70, 110),
    0x2F: (20, 80),
}

pid_stats = {pid: {"count": 0, "min": float('inf'), "max": float('-inf')} for pid in PID_MAP}

def build_response(pid, value):
    if pid in BLOCKED_PIDS:
        return None

    if pid == 0x0C:  # RPM
        raw = int(value * 4)
        payload = [raw >> 8, raw & 0xFF]
    elif pid == 0x0D:  # Speed
        payload = [int(value)]
    elif pid == 0x46:  # Air temp
        payload = [int(value) & 0xFF]
    elif pid == 0x4E:  # Fuel rate
        raw = int(value * 100)
        payload = [raw >> 8, raw & 0xFF]
    elif pid == 0x31:  # DTC distance
        raw = int(value)
        payload = [raw >> 8, raw & 0xFF]
    elif pid in [0x04, 0x2F, 0x5C, 0x05]:  # Load, fuel level, temps
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
    timestamp = datetime.now()
    start_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    csv_filename = timestamp.strftime('test_21_%d_%m_%H_%M.csv')
    print(f"Test 21: Starting at {start_str}. Duration: 20 minutes.")

    cycle = 0
    while True:
        elapsed = time.time() - start_time
        if elapsed >= max_runtime_sec:
            print("Test 21 complete.")
            break

        progress = (elapsed / max_runtime_sec)

        values = {
            0x0C: RANGES[0x0C][0] + (RANGES[0x0C][1] - RANGES[0x0C][0]) * progress,
            0x0D: RANGES[0x0D][0] + (RANGES[0x0D][1] - RANGES[0x0D][0]) * progress,
            0x46: RANGES[0x46][0] + (RANGES[0x46][1] - RANGES[0x46][0]) * progress,
            0x4E: RANGES[0x4E][0] + (RANGES[0x4E][1] - RANGES[0x4E][0]) * progress,
            0x31: RANGES[0x31][1] * progress,
            0x04: RANGES[0x04][0] + (RANGES[0x04][1] - RANGES[0x04][0]) * progress,
            0x05: RANGES[0x05][0] + (RANGES[0x05][1] - RANGES[0x05][0]) * progress,
            0x5C: RANGES[0x5C][0] + (RANGES[0x5C][1] - RANGES[0x5C][0]) * progress,
            0x2F: RANGES[0x2F][1] - (RANGES[0x2F][1] - RANGES[0x2F][0]) * progress,
        }

        for pid, value in values.items():
            frame = build_response(pid, value)
            if frame:
                msg = can.Message(arbitration_id=RESPONSE_ID, data=frame, is_extended_id=False)
                bus.send(msg)
                time.sleep(0.015)

                # Update stats
                stat = pid_stats[pid]
                stat["count"] += 1
                stat["min"] = min(stat["min"], value)
                stat["max"] = max(stat["max"], value)

        time.sleep(cycle_duration_sec)
        cycle += 1

except KeyboardInterrupt:
    print("Test 21 Emulator stopped manually.")

finally:
    bus.shutdown()
    print("\n=== PID Query Summary ===")
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["PID", "Name", "Count", "MinValue", "MaxValue"])
        for pid, stats in pid_stats.items():
            name = PID_MAP[pid]
            count = stats["count"]
            min_v = round(stats["min"], 2) if count else 'N/A'
            max_v = round(stats["max"], 2) if count else 'N/A'
            print(f"{pid:02X} ({name}): Count={count}, Range=[{min_v}, {max_v}]")
            writer.writerow([f"{pid:02X}", name, count, min_v, max_v])

    print(f"\nCSV summary written to {csv_filename}")
