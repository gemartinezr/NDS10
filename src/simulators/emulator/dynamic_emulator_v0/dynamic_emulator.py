import time
import can
import signal
import sys
import random
from collections import defaultdict
from datetime import datetime

# Phase-aware stress simulation
pid_names = {
    0x01: "Monitor Status",
    0x0C: "Engine RPM",
    0x0D: "Speed",
    0x1F: "Runtime",
    0x21: "Distance Traveled",
    0x31: "DTC Distance",
    0x42: "Control Voltage",
    0x46: "Air Temp",
    0x4E: "Fuel Rate"
}

# Reference start time to ensure phase consistency across runs
START_TIME = time.time()

last_phase = None

def get_phase():
    elapsed = int(time.time() - START_TIME)
    cycle = elapsed % 90  # 90-second cycle: 30s per phase
    if cycle < 30:
        return 'low'
    elif cycle < 60:
        return 'medium'
    else:
        return 'high'

# Setup CAN bus (adjust channel if needed)
bus = can.interface.Bus(channel='can0', bustype='socketcan')

# VIN configuration
VIN = "WVWZZZE1ZMP018990"
vin_bytes = list(VIN.encode('ascii'))

# Track stats
pid_request_counts = defaultdict(int)
pid_value_ranges = {}

# Emulator fingerprint
ENABLE_EMULATOR_FLAG = False
EMULATOR_FLAG = 0xDD

# Dynamic counters
dynamic_counter = 0

def handle_exit(signum, frame):
    print_summary()
    bus.shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

def update_range(pid, value):
    if pid not in pid_value_ranges:
        pid_value_ranges[pid] = [value, value]
    else:
        pid_value_ranges[pid][0] = min(pid_value_ranges[pid][0], value)
        pid_value_ranges[pid][1] = max(pid_value_ranges[pid][1], value)

def print_summary():
    current_phase = get_phase()
    print(f"\n=== PID REQUEST SUMMARY @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Phase: {current_phase.upper()} ===")
    for pid in sorted(pid_request_counts):
        count = pid_request_counts[pid]
        value_range = pid_value_ranges.get(pid, [float('nan'), float('nan')])
        name = pid_names.get(pid, "Unknown")
        print(f"PID 0x{pid:02X} ({name}): {count} requests, value range = [{value_range[0]}, {value_range[1]}]")

def resp(tag, pid, payload):
    response = [len(payload) + 2, 0x41, pid] + payload
    if len(response) < 8:
        response += [0x00] * (8 - len(response))
        if ENABLE_EMULATOR_FLAG and len(payload) <= 5:
            response[-1] = EMULATOR_FLAG
    return response

# PID Handlers   (Always queried by FMC003)
def pid_01():
    return resp(0xAA, 0x01, [random.randint(0, 1), 0x00, 0x07, 0x0F])

def pid_0C():
    phase = get_phase()
    rpm = {
        'low': random.randint(4000, 6000),
        'medium': random.randint(6000, 12000),
        'high': random.randint(12000, 20000)
    }[phase]
    return resp(0xAA, 0x0C, [(rpm >> 8) & 0xFF, rpm & 0xFF])

def pid_0D():
    phase = get_phase()
    speed = {
        'low': random.randint(0, 20),
        'medium': random.randint(20, 60),
        'high': random.randint(60, 100)
    }[phase]
    return resp(0xAA, 0x0D, [speed])

def pid_1F():
    phase = get_phase()
    runtime = {
        'low': random.randint(16, 200),
        'medium': random.randint(200, 600),
        'high': random.randint(600, 1000)
    }[phase]
    return resp(0xAA, 0x1F, [(runtime >> 8) & 0xFF, runtime & 0xFF])

def pid_21():
    phase = get_phase()
    distance = {
        'low': random.randint(0, 3),
        'medium': random.randint(3, 10),
        'high': random.randint(10, 30)
    }[phase]
    return resp(0xAA, 0x21, [(distance >> 8) & 0xFF, distance & 0xFF])

def pid_31():
    distance = random.randint(1, 20)
    return resp(0xAA, 0x31, [distance])

def pid_42():
    voltage = random.randint(110, 140)
    return resp(0xAA, 0x42, [voltage])

def pid_46():
    phase = get_phase()
    temp = {
        'low': random.randint(90, 100),
        'medium': random.randint(60, 90),
        'high': random.randint(40, 60)
    }[phase]
    return resp(0xAA, 0x46, [temp])

def pid_4E():
    rate = random.randint(0, 400)
    return resp(0xAA, 0x4E, [(rate >> 8) & 0xFF, rate & 0xFF])

def pid_2C():
    global dynamic_counter
    dynamic_counter = (dynamic_counter + 1) % 256
    return resp(0xAA, 0x2C, [dynamic_counter])


# Less frequent PID Requests
def pid_00(): return resp(0xAA, 0x00, [0b10111110, 0b11100000, 0x00, 0x18])
def pid_20(): return resp(0xAA, 0x20, [0b11000000, 0x00, 0x00, 0x00])
def pid_40(): return resp(0xAA, 0x40, [0b00110000, 0b00110000, 0x00, 0x00])
def pid_03(): return [0x02, 0x43, 0x00, 0x00, 0, 0, 0, 0]
def pid_04(): return resp(0xAA, 0x04, [30])
def pid_05():
    temp = random.randint(50,90)
    temp = (temp + 1) % 100
    return resp(0xAA, 0x05, [temp])
def pid_06(): return resp(0xAA, 0x06, [0x00])
def pid_0A(): return resp(0xAA, 0x0A, [0x0C])
def pid_0B(): return resp(0xAA, 0x0B, [0x3C])
def pid_0E(): return resp(0xAA, 0x0E, [0x1E])
def pid_0F(): return resp(0xAA, 0x0F, [70])
def pid_10():
    maf = 1050  # constant for now
    return resp(0xAA, 0x10, [(maf >> 8) & 0xFF, maf & 0xFF])
def pid_11(): return resp(0xAA, 0x11, [90])
def pid_22(): return resp(0xAA, 0x22, [0x01, 0x02])
def pid_23(): return resp(0xAA, 0x23, [0x55, 0x55])
def pid_2D(): return resp(0xAA, 0x2D, [0x20])
def pid_2F(): return resp(0xAA, 0x2F, [57])
def pid_33(): return resp(0xAA, 0x33, [0x00, 0x01])
def pid_43(): return resp(0xAA, 0x43, [dynamic_counter % 128])
def pid_44(): return resp(0xAA, 0x44, [0x00, 0xC8])
def pid_47(): return resp(0xAA, 0x47, [28])
def pid_4B(): return resp(0xAA, 0x4B, [0x00, 0x00])
def pid_4D(): return resp(0xAA, 0x4D, [0x10])
def pid_51(): return resp(0xAA, 0x51, [0x40])
def pid_52(): return resp(0xAA, 0x52, [0x01, 0x00])
def pid_59(): return resp(0xAA, 0x59, [0x00, 0x01])
def pid_5B(): return resp(0xAA, 0x5B, [0x00])
def pid_5C(): return resp(0xAA, 0x5C, [0x00])
def pid_5D(): return resp(0xAA, 0x5D, [0x00])
def pid_5E(): return resp(0xAA, 0x5E, [0x00])
def pid_60(): return resp(0xAA, 0x60, [0x00, 0x00, 0x00, 0x00])
def pid_80(): return resp(0xAA, 0x80, [0x00, 0x00, 0x00, 0x00])
def pid_A0(): return resp(0xAA, 0xA0, [0x00, 0x00, 0x00, 0x00])




print("OBD-II Emulator started. Press Ctrl+C to stop.")
last_summary_time = time.time()
summary_interval = 120

while True:
    current_phase = get_phase()
    if current_phase != last_phase:
        pid_request_counts.clear()
        pid_value_ranges.clear()
        last_phase = current_phase
    msg = bus.recv(timeout=1.0)
    if msg and msg.arbitration_id == 0x7DF:
        data = msg.data
        mode = data[1]
        pid = data[2]

        if mode == 0x01:
            pid_request_counts[pid] += 1
            handler = globals().get(f"pid_{pid:02X}")
            if handler:
                frame = handler()
                bus.send(can.Message(arbitration_id=0x7E8, data=frame[:8], is_extended_id=False))
                if len(frame) >= 5:
                    value = frame[3]
                    if len(frame) >= 6 and pid in [0x0C, 0x1F, 0x21, 0x4E]:
                        value = (frame[3] << 8) + frame[4]
                    update_range(pid, value)
            else:
                print(f"[!] Unsupported PID 0x{pid:02X}")
                bus.send(can.Message(arbitration_id=0x7E8, data=resp(0xAA, pid, [0x00]), is_extended_id=False))

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

    if time.time() - last_summary_time >= summary_interval:
        print_summary()
        last_summary_time = time.time()




"""    
Find Teltonika device on Linux 
    lsusb  (Look out for a record similar to Bus 003 Device 063: ID 10c4:ea60 Silicon Labs CP210x UART Bridge)
    sudo dmesg -w | grep -i '0e8d\|0023'
    sudo dmesg -w | grep -i 'meditek\|ttyUSB\|usb 3-9' 

See logs from FMC003:
    sudo cat -A /dev/ttyUSB0

Capture logs from FMC003: 
    timeout 5m sudo cat -A /dev/ttyUSB0 > fmc003_raw_$(date -u +"%Y-%m-%dT%H-%M-%SZ").txt
    
Capture communication in CAN:      
    candump -tz can0 > fmc003_startTime_freematics_.txt
    timeout 5m candump -tz can0,7DF:7FF > canlogs_$(date -u +"%Y-%m-%dT%H-%M-%SZ").txt
"""


"""Example to implement dynamic values for PIDs

def pid_2C():
    global dynamic_counter
    dynamic_counter = (dynamic_counter + 1) % 256
    return resp(0xAA, 0x2C, [dynamic_counter])

dynamic_counter = 0  (initialize at top)
"""