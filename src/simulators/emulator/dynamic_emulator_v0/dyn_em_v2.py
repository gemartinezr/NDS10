import time
import can
import signal
import sys
from collections import defaultdict
from datetime import datetime

# Phase-aware RPM memoization with prebuilt frames
START_NS = time.monotonic_ns()
RPM_LOOKUP = {
    'low':    [4000 + i * 70 for i in range(30)],
    'medium': [6000 + i * 200 for i in range(30)],
    'high':   [12000 + i * 270 for i in range(30)],
}

PREBUILT_RPM = {
    'low':    [None]*30,
    'medium': [None]*30,
    'high':   [None]*30
}

for phase in RPM_LOOKUP:
    for i, rpm in enumerate(RPM_LOOKUP[phase]):
        PREBUILT_RPM[phase][i] = [4, 0x41, 0x0C, (rpm >> 8) & 0xFF, rpm & 0xFF, 0, 0, 0]

bus = can.interface.Bus(channel='can0', bustype='socketcan')
pid_request_counts = defaultdict(int)
pid_value_ranges = {}

print(f"Dynamic_emulator_v2 started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Press Ctrl+C to stop.")

def update_range(pid, value):
    if pid not in pid_value_ranges:
        pid_value_ranges[pid] = [value, value]
    else:
        pid_value_ranges[pid][0] = min(pid_value_ranges[pid][0], value)
        pid_value_ranges[pid][1] = max(pid_value_ranges[pid][1], value)

def print_summary():
    print(f"\n=== PID REQUEST SUMMARY @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    for pid in sorted(pid_request_counts):
        count = pid_request_counts[pid]
        value_range = pid_value_ranges.get(pid, [float('nan'), float('nan')])
        print(f"PID 0x{pid:02X}: {count} requests, value range = [{value_range[0]}, {value_range[1]}]")

def get_rpm_frame():
    elapsed = (time.monotonic_ns() - START_NS) // 1_000_000_000
    cycle = elapsed % 90
    if cycle < 30:
        return PREBUILT_RPM['low'][cycle]
    elif cycle < 60:
        return PREBUILT_RPM['medium'][cycle - 30]
    else:
        return PREBUILT_RPM['high'][cycle - 60]

def handle_exit(signum, frame):
    print_summary()
    bus.shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

while True:
    msg = bus.recv(timeout=0.01)
    if msg and msg.arbitration_id == 0x7DF:
        data = msg.data
        if len(data) >= 3 and data[1] == 0x01:
            pid = data[2]
            pid_request_counts[pid] += 1
            if pid == 0x0C:
                frame = get_rpm_frame()
            else:
                frame = [4, 0x41, pid, 0x00, 0x00, 0x00, 0x00, 0x00]
            bus.send(can.Message(arbitration_id=0x7E8, data=frame, is_extended_id=False))
            if len(frame) >= 5:
                value = frame[3]
                if len(frame) >= 6:
                    value = (frame[3] << 8) + frame[4]
                update_range(pid, value)
