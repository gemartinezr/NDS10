import json
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# Load your JSONL log
log_file = "mqtt_logs.jsonl"
messages = []

with open(log_file, 'r') as file:
    for line in file:
        try:
            entry = json.loads(line)
            messages.append(entry)
        except json.JSONDecodeError:
            continue

# Convert to DataFrame
df = pd.DataFrame(messages)

# Parse timestamp
df['timestamp'] = pd.to_datetime(df['ts'], unit='ms')
df.set_index('timestamp', inplace=True)

# Simulate MQTT payload size
df['payload_size'] = df.apply(lambda row: len(json.dumps(row.to_dict()).encode('utf-8')), axis=1)

# Resample in 5s windows
interval = '5S'
stats = df['payload_size'].resample(interval).agg(['count', 'sum', 'mean'])
stats.rename(columns={'count': 'packet_count', 'sum': 'total_bytes', 'mean': 'avg_packet_size'}, inplace=True)
stats['bytes_per_sec'] = stats['total_bytes'] / 5

# Plot stats
fig, ax = plt.subplots(figsize=(12, 6))
stats['total_bytes'].plot(label='Total Bytes per 5s', ax=ax)
stats['packet_count'].plot(label='Packet Count per 5s', ax=ax)
stats['bytes_per_sec'].plot(label='Bytes/sec', ax=ax)

ax.set_title('MQTT AVL Payload Traffic Overview (5s Intervals)')
ax.set_xlabel('Time')
ax.set_ylabel('Value')
ax.legend()
ax.grid(True)
plt.tight_layout()
plt.show()
