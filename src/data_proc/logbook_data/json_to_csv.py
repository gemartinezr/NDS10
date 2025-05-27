import json
import pandas as pd
from glob import glob
import os

def load_json_results(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)["results"]

# Set this to the path where your JSON files are located
data_dir = "../es_data/vehicle_data/"  # <-- CHANGE THIS

# Create full file patterns
file_map = {
    "obd_rpm": sorted(glob(os.path.join(data_dir, "obd_rpm_*.json"))),
    "obd_speed": sorted(glob(os.path.join(data_dir, "obd_speed_*.json"))),
    "obd_engine_load": sorted(glob(os.path.join(data_dir, "obd_engine_load_*.json"))),
}

print("RPM files found:", file_map["obd_rpm"])

# Build a dictionary indexed by ts
data_by_ts = {}

for key, files in file_map.items():
    for file in files:
        for entry in load_json_results(file):
            ts = entry["ts"]
            rec = entry["rec"]
            val = entry["data"]["value"]
            if ts not in data_by_ts:
                data_by_ts[ts] = {
                    "ts_recorded": ts,
                    "ts_uploaded": rec,
                    "obd_rpm": None,
                    "obd_speed": None,
                    "obd_engine_load": None
                }
            if rec > data_by_ts[ts]["ts_uploaded"]:
                data_by_ts[ts]["ts_uploaded"] = rec
            data_by_ts[ts][key] = val

# Convert to DataFrame
df = pd.DataFrame(data_by_ts.values())
df.sort_values("ts_recorded", inplace=True)

# Save CSV to same directory
csv_output = os.path.join(data_dir, "merged_obd_data.csv")
df.to_csv(csv_output, index=False)
print(f"CSV saved to {csv_output}")
