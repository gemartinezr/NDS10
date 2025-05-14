import pandas as pd
import requests
from datetime import datetime
import subprocess
import os

def save_response(page_num, response):
    file_name = f"response_{page_num}.json" 
    file_path = 'customer_data/'+file_name
    with open(file_path, 'w') as json_response:
        json_response.write(response.text)
    return file_path

req_url = "https://api.autopi.io/logbook/raw/"

headers_list = {
 "Accept": "*/*",
 "Content-Type": "application/json",
 "Authorization": f"APIToken {os.environ.get('MY_TOKEN')}" 
}

start = "2024-10-29T13:00:00.000Z"
end = "2024-10-30T13:00:00.000Z"
logger = "obd.oem_hv_battery_voltage"

one_day_params = {"device_id":"f884bf8c-e6d1-431c-b449-a2a6e0da44c6",
          "page_num":0,
          "page_size":1000, 
          "data_type": logger,
          "start_utc": start,
          "end_utc": end,
          "upload_time": False }

response = requests.request("GET", req_url, params=one_day_params, headers=headers_list)
new_file = save_response(0, response)
json_files = []
json_files.append(new_file)

total_records = response.json()['count']
print(f"Found {total_records} data points from {start} to {end}")
total_pages = round(total_records / 1000) 

page_num = 0
while page_num < total_pages:
    page_num += 1
    one_day_params["page_num"] = page_num
    response = requests.request("GET", req_url, params=one_day_params, headers=headers_list)
    new_file = save_response(page_num, response)
    json_files.append(new_file)

# Loop through each file in json_files
for file_path in json_files:
    # Run json_to_csv.py with file_path and "obd.oem_hv_battery_voltage" as arguments
    subprocess.run(['python', 'json_to_csv.py', file_path, 'obd.oem_hv_battery_voltage'])

frames = []
for i in range(len(json_files)):
    part_df = pd.read_csv(f'customer_data/filtered_data_{i}.csv')
    frames.append(part_df)
combined_df = pd.concat(frames, ignore_index=True)

combined_df = combined_df.sort_values('ts', ascending=True) # comment this line if you prefer records ordered from most recent to oldest

combined_df.to_csv('customer_data/combined_responses.csv')
