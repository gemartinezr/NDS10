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
EMULATOR_FLAG = None  # Disable custom flag

# Timing
cycle_duration_sec = 0.08
max_runtime_sec = 10 * 60  # 10 minutes
no_request_timeout_sec = 120

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
request_log = []
last_request_time = time.time()

def build_response(pid, value):
    if pid in BLOCKED_PIDS:
        return None

    if pid == 0x0C:
        raw = int(value * 4)
        payload = [raw >> 8, raw & 0xFF]
    elif pid == 0x0D:
        payload = [int(value)]
    elif pid == 0x46:
        payload = [int(value) & 0xFF]
    elif pid == 0x4E:
        raw = int(value * 100)
        payload = [raw >> 8, raw & 0xFF]
    elif pid == 0x31:
        raw = int(value)
        payload = [raw >> 8, raw & 0xFF]
    elif pid in [0x04, 0x2F, 0x5C, 0x05]:
        payload = [int(value)]
    else:
        return None

    frame_body = [0x41, pid] + payload
    data = [len(frame_body)] + frame_body

    while len(data) < 8:
        data.append(0x00)

    return data

try:
    start_time = time.time()
    timestamp = datetime.now()
    start_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    csv_filename = timestamp.strftime('test_21_%d_%m_%H_%M.csv')
    reqlog_filename = timestamp.strftime('test_21_requests_%d_%m_%H_%M.log')
    print(f"Test 21: Starting at {start_str}. Duration: 10 minutes.")

    cycle = 0
    while True:
        elapsed = time.time() - start_time
        if elapsed >= max_runtime_sec:
            print("Test 21 complete.")
            break

        if time.time() - last_request_time > no_request_timeout_sec:
            print("No requests received in the last 2 minutes. Aborting test.")
            break

        progress = elapsed / max_runtime_sec

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

        msg = bus.recv(timeout=0.01)
        if msg and msg.arbitration_id == 0x7DF and len(msg.data) >= 3 and msg.data[1] == 0x01:
            pid = msg.data[2]
            last_request_time = time.time()
            request_log.append((elapsed, pid))
            if pid in values:
                frame = build_response(pid, values[pid])
                if frame:
                    response = can.Message(arbitration_id=RESPONSE_ID, data=frame, is_extended_id=False)
                    bus.send(response)
                    pid_stats[pid]["count"] += 1
                    pid_stats[pid]["min"] = min(pid_stats[pid]["min"], values[pid])
                    pid_stats[pid]["max"] = max(pid_stats[pid]["max"], values[pid])
                    time.sleep(0.03)

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

    with open(reqlog_filename, 'w') as reqfile:
        for timestamp_sec, pid in request_log:
            reqfile.write(f"{timestamp_sec:.2f}s PID=0x{pid:02X} ({PID_MAP.get(pid, 'Unknown')})\n")

    print(f"\nCSV summary written to {csv_filename}")
    print(f"Request log written to {reqlog_filename}")
