import json
import csv
import sys

# Check for the command-line argument
if len(sys.argv) < 3:
    print("Usage: python script.py <input_json> <filter_value>")
    sys.exit(1)

input_json = sys.argv[1]
filter_value = sys.argv[2]
file_name = input_json.replace('customer_data/', '')
output_csv = f"customer_data/filtered_data_{file_name.replace('response_', '').replace('.json','')}.csv"

# Load JSON data
with open(input_json, "r") as json_file:
    data = json.load(json_file)

# Extract the relevant records from the JSON
records = data["results"]

# Collect unique keys in `data` to define CSV header dynamically
data_keys = set()
for record in records:
    data_keys.update(record["data"].keys())

# Define the CSV header fields
header = ["rec", "ts", "t"] + list(data_keys)

# Write to CSV with filtering
with open(output_csv, "w", newline="") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=header)
    writer.writeheader()

    # Write only the rows where `t` matches the filter value
    for record in records:
        if record.get("t") == filter_value:
            row = {
                "rec": record.get("rec"),
                "ts": record.get("ts"),
                "t": record.get("t"),
                **{key: record["data"].get(key, None) for key in data_keys}
            }
            writer.writerow(row)

print(f"Filtered CSV has been created as {output_csv} with t = '{filter_value}'")
