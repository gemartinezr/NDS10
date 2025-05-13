import time
import can
import signal
import sys
from collections import defaultdict
from datetime import datetime

# Setup CAN bus (adjust channel if needed)
bus = can.interface.Bus(channel='can0', bustype='socketcan')

# VIN configuration
VIN = "WVWZZZE1ZMP018990"
vin_bytes = list(VIN.encode('ascii'))

# Track stats
pid_request_counts = defaultdict(int)
pid_value_ranges = {}

# Emulator fingerprint
EMULATOR_FLAG = 0xDD

# Simulated state
rpm = 1000
speed = 0
temp = 85
dynamic_counter = 0

# Print summary helper
def print_summary():
    print(f"\n=== PID REQUEST SUMMARY @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    for pid in sorted(pid_request_counts):
        count = pid_request_counts[pid]
        value_range = pid_value_ranges.get(pid, [float('nan'), float('nan')])
        print(f"PID 0x{pid:02X}: {count} requests, value range = [{value_range[0]}, {value_range[1]}]")

# Graceful shutdown
def handle_exit(signum, frame):
    print_summary()
    bus.shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

# Helpers
def update_range(pid, value):
    if pid not in pid_value_ranges:
        pid_value_ranges[pid] = [value, value]
    else:
        pid_value_ranges[pid][0] = min(pid_value_ranges[pid][0], value)
        pid_value_ranges[pid][1] = max(pid_value_ranges[pid][1], value)

def resp(tag, pid, payload):
    response = [len(payload) + 2, 0x41, pid] + payload
    response += [0x00] * (8 - len(response))
    response[-1] = EMULATOR_FLAG
    return response

# Supported PID maps
def pid_00(): return resp(0xAA, 0x00, [0b10111110, 0b11100000, 0x00, 0x18])
def pid_20(): return resp(0xAA, 0x20, [0b11000000, 0x00, 0x00, 0x00])
def pid_40(): return resp(0xAA, 0x40, [0b00110000, 0b00110000, 0x00, 0x00])

# PID encoder functions with reset logic
def pid_01(): return resp(0xAA, 0x01, [0x80, 0x07, 0xE0, 0x00])
def pid_03(): return [0x02, 0x43, 0x00, 0x00, 0, 0, 0, 0]
def pid_04(): return resp(0xAA, 0x04, [30])
def pid_05():
    global temp
    temp = (temp + 1) % 100
    return resp(0xAA, 0x05, [temp])
def pid_06(): return resp(0xAA, 0x06, [0x00])
def pid_0A(): return resp(0xAA, 0x0A, [0x0C])
def pid_0B(): return resp(0xAA, 0x0B, [0x3C])
def pid_0C():
    global rpm
    rpm = (rpm + 25) % 8000
    val = int(rpm * 4)
    return resp(0xAA, 0x0C, [(val >> 8) & 0xFF, val & 0xFF])
def pid_0D():
    global speed
    speed = (speed + 2) % 200
    return resp(0xAA, 0x0D, [speed])
def pid_0E(): return resp(0xAA, 0x0E, [0x1E])
def pid_0F(): return resp(0xAA, 0x0F, [70])
def pid_10():
    maf = 1050  # constant for now
    return resp(0xAA, 0x10, [(maf >> 8) & 0xFF, maf & 0xFF])
def pid_11(): return resp(0xAA, 0x11, [90])
def pid_1F():
    runtime = 1500
    return resp(0xAA, 0x1F, [(runtime >> 8) & 0xFF, runtime & 0xFF])
def pid_21(): return resp(0xAA, 0x21, [0x10, 0x00])
def pid_22(): return resp(0xAA, 0x22, [0x01, 0x02])
def pid_23(): return resp(0xAA, 0x23, [0x55, 0x55])
def pid_2C():
    global dynamic_counter
    dynamic_counter = (dynamic_counter + 1) % 256
    return resp(0xAA, 0x2C, [dynamic_counter])
def pid_2D(): return resp(0xAA, 0x2D, [0x20])
def pid_2F(): return resp(0xAA, 0x2F, [57])
def pid_31(): return resp(0xAA, 0x31, [0x01])
def pid_33(): return resp(0xAA, 0x33, [0x00, 0x01])
def pid_42(): return resp(0xAA, 0x42, [0x0F, 0xA0])
def pid_43(): return resp(0xAA, 0x43, [dynamic_counter % 128])
def pid_44(): return resp(0xAA, 0x44, [0x00, 0xC8])
def pid_46(): return resp(0xAA, 0x46, [0x20])
def pid_47(): return resp(0xAA, 0x47, [28])
def pid_4B(): return resp(0xAA, 0x4B, [0x00, 0x00])
def pid_4D(): return resp(0xAA, 0x4D, [0x10])
def pid_4E(): return resp(0xAA, 0x4E, [0x10])
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
summary_interval = 120  # seconds

while True:
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
                # Update value range if possible
                if len(frame) >= 5:
                    value = frame[3]
                    if len(frame) >= 6 and pid in [0x0C, 0x10, 0x1F, 0x59]:
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

    # Periodic summary print
    if time.time() - last_summary_time >= summary_interval:
        print_summary()
        last_summary_time = time.time()



"""    
To see logs from FMC003:
    sudo picocom -b 9600 /dev/ttyUSB0


To capture logs from FMC003: 
    sudo cat /dev/ttyUSB0 > fmc003_raw_startTime.txt


To capture logs from FMC003 with a timeout :
    timeout 10s sudo cat /dev/ttyUSB0 > fmc003_raw_startTime.txt  
    
To read logs: 
    cat -A fmc003_log_raw.txt


To capture communication in CAN:      
    candump -tz can0 > fmc003_startTime_freematics_.txt



    
To find Teltonika device on Linux 

    lsusb  (Look out for a record similar to Bus 003 Device 063: ID 10c4:ea60 Silicon Labs CP210x UART Bridge)
    sudo dmesg -w | grep -i '0e8d\|0023'
    sudo dmesg -w | grep -i 'meditek\|ttyUSB\|usb 3-9' 

"""


"""Example to implement dynamic values for PIDs

def pid_2C():
    global dynamic_counter
    dynamic_counter = (dynamic_counter + 1) % 256
    return resp(0xAA, 0x2C, [dynamic_counter])

dynamic_counter = 0  (initialize at top)

"""