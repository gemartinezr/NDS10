import serial
import time

# Open the serial connection at 38400 baud
ser = serial.Serial('/dev/ttyUSB0', 38400, timeout=1)

# Send PID request (mode 01, PID 0D = vehicle speed)
ser.write(b'010D\r')

# Small wait for response
time.sleep(0.5)

# Read response
response = ser.read(64)
print("Response:", response.decode(errors='ignore'))

ser.close()