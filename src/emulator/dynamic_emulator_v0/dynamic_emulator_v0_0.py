import time
import can
import signal
import sys
from collections import defaultdict

# Setup CAN bus (adjust channel if needed)
bus = can.interface.Bus(channel='can0', bustype='socketcan')

# VIN configuration
VIN = "WVWZZZE1ZMP018990"
vin_bytes = list(VIN.encode('ascii'))

# Track stats
pid_request_counts = defaultdict(int)
pid_value_ranges = {}

def update_range(pid, value):
    if pid not in pid_value_ranges:
        pid_value_ranges[pid] = [value, value]
    else:
        pid_value_ranges[pid][0] = min(pid_value_ranges[pid][0], value)
        pid_value_ranges[pid][1] = max(pid_value_ranges[pid][1], value)

# Graceful shutdown
def handle_exit(signum, frame):
    print("\n=== PID REQUEST SUMMARY ===")
    for pid in sorted(pid_request_counts):
        count = pid_request_counts[pid]
        value_range = pid_value_ranges.get(pid, [float('nan'), float('nan')])
        print(f"PID 0x{pid:02X}: {count} requests, value range = [{value_range[0]}, {value_range[1]}]")
    bus.shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

# Encoder helper
def resp(tag, pid, payload):
    return [len(payload) + 2, 0x41, pid] + payload + [0] * (8 - (len(payload) + 3)) + [tag]

# PID encoder functions
def pid_00():
    # Supported PIDs from 0x01 to 0x20 (bitmask)
    return [0x06, 0x41, 0x00, 0b10111110, 0b11100000, 0x00, 0x00, 0xAA]

def pid_01():
    val = 0x80  # MIL off, 0 DTCs, some readiness bits set
    return resp(0xAA, 0x01, [val, 0x07, 0xE0, 0x00])

def pid_03():
    # Return no DTCs
    return [0x02, 0x43, 0x00, 0x00, 0, 0, 0, 0]

def pid_05():
    global temp
    temp = 85 + ((temp + 1) % 15)
    update_range(0x05, temp)
    return resp(0xAA, 0x05, [temp + 40])

def pid_0C():
    global rpm
    val = int(rpm * 4)
    rpm = (rpm + 50) % 8000
    A, B = (val >> 8) & 0xFF, val & 0xFF
    update_range(0x0C, rpm)
    return resp(0xAA, 0x0C, [A, B])

def pid_0D():
    global speed
    speed = (speed + 3) % 200
    update_range(0x0D, speed)
    return resp(0xAA, 0x0D, [int(speed)])

def pid_0F():
    val = 30
    update_range(0x0F, val)
    return resp(0xAA, 0x0F, [val + 40])

def pid_10():
    val = 10.5
    maf = int(val * 100)
    A, B = (maf >> 8) & 0xFF, maf & 0xFF
    update_range(0x10, val)
    return resp(0xAA, 0x10, [A, B])

def pid_11():
    val = 90  # throttle %
    update_range(0x11, val)
    return resp(0xAA, 0x11, [val])

def pid_1F():
    val = 25  # runtime (min)
    runtime = int(val * 60)
    A, B = (runtime >> 8) & 0xFF, runtime & 0xFF
    update_range(0x1F, val)
    return resp(0xAA, 0x1F, [A, B])

def pid_2F():
    val = 57
    update_range(0x2F, val)
    return resp(0xAA, 0x2F, [val])

def pid_44():
    val = 45  # commanded equivalence ratio
    update_range(0x44, val)
    return resp(0xAA, 0x44, [0x00, 0x80])  # lambda = 1.0

def pid_47():
    val = 28  # absolute throttle B
    update_range(0x47, val)
    return resp(0xAA, 0x47, [val])

# Simulated state
rpm = 1000
speed = 0
temp = 85

print("OBD-II Emulator started. Press Ctrl+C to stop.")

while True:
    msg = bus.recv(timeout=1.0)
    if msg and msg.arbitration_id == 0x7DF:
        data = msg.data
        mode = data[1]
        pid = data[2]

        if mode == 0x01:
            pid_request_counts[pid] += 1

            if pid == 0x00:
                frame = pid_00()
            elif pid == 0x01:
                frame = pid_01()
            elif pid == 0x03:
                frame = pid_03()
            elif pid == 0x05:
                frame = pid_05()
            elif pid == 0x0C:
                frame = pid_0C()
            elif pid == 0x0D:
                frame = pid_0D()
            elif pid == 0x0F:
                frame = pid_0F()
            elif pid == 0x10:
                frame = pid_10()
            elif pid == 0x11:
                frame = pid_11()
            elif pid == 0x1F:
                frame = pid_1F()
            elif pid == 0x2F:
                frame = pid_2F()
            elif pid == 0x44:
                frame = pid_44()
            elif pid == 0x47:
                frame = pid_47()
            else:
                continue

            bus.send(can.Message(arbitration_id=0x7E8, data=frame[:8], is_extended_id=False))

        elif mode == 0x09 and pid == 0x02:
            pid_request_counts[pid] += 1
            frame1 = [0x10, 0x14, 0x49, 0x02, 0x01] + vin_bytes[:3]
            frame2 = [0x21] + vin_bytes[3:10]
            frame3 = [0x22] + vin_bytes[10:17]
            bus.send(can.Message(arbitration_id=0x7E8, data=frame1, is_extended_id=False))
            time.sleep(0.01)
            bus.send(can.Message(arbitration_id=0x7E8, data=frame2, is_extended_id=False))
            time.sleep(0.01)
            bus.send(can.Message(arbitration_id=0x7E8, data=frame3, is_extended_id=False))
            update_range(pid, float('nan'))



"""
USB2can needs to be connected, then: 
    sudo ip link set can0 down

    sudo ip link set can0 up type can bitrate 500000  # or sudo ip link set can0 up type can bitrate 500000 loopback on

To see logs from FMC003:
    sudo picocom -b 9600 /dev/ttyUSB0

To capture logs: 
    sudo cat /dev/ttyUSB0 > fmc003_log_raw.txt

    timeout 10s sudo cat /dev/ttyUSB0 > fmc003_log_raw.txt  #(specific time)
    
To read logs: 
    cat -A fmc003_log_raw.txt
"""