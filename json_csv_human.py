import json
import csv
from datetime import datetime


# Function to convert timestamp from milliseconds to human-readable format
def convert_timestamp(timestamp_ms):
    timestamp_s = timestamp_ms / 1000  # Convert milliseconds to seconds
    return datetime.utcfromtimestamp(timestamp_s).strftime("%Y-%m-%d %H:%M:%S.%f UTC")


# Open and load the outer JSON file
with open("data.json", "r") as f:
    outer_data = json.load(f)

csv_rows = []

# Loop over each key in the outer JSON
for key, json_str in outer_data.items():
    try:
        # Parse the inner JSON string
        inner_data = json.loads(json_str)
        # Extract the keyboard_data list
        keyboard_data = inner_data.get("keyboard_data", [])

        # Convert each event record's timestamp
        for record in keyboard_data:
            if len(record) == 3:  # Ensure the record structure is correct
                event, key_pressed, timestamp_ms = record
                timestamp_human = convert_timestamp(timestamp_ms)
                csv_rows.append([event, key_pressed, timestamp_human])
    except Exception as e:
        print(f"Error processing key {key}: {e}")

# Write the data to a CSV file with headers
with open("output.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Event", "Key", "Timestamp (UTC)"])  # Updated header
    writer.writerows(csv_rows)

print("CSV conversion complete!")
