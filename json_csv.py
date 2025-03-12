import json
import csv

# Read the file content from a text file
with open("free_data.txt", "r") as f:
    file_contents = f.read()

# Parse the outer JSON from the text file
outer_data = json.loads(file_contents)

csv_rows = []

# Loop over each key in the outer JSON
for key, inner_json_str in outer_data.items():
    try:
        # Parse the inner JSON string
        inner_data = json.loads(inner_json_str)
        # Extract the keyboard_data list
        keyboard_data = inner_data.get("keyboard_data", [])

        # Append each record to the CSV rows
        for record in keyboard_data:
            csv_rows.append(record)
    except Exception as e:
        print(f"Error processing key {key}: {e}")

# Write the data to a CSV file with headers
with open("free_data.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    # You can adjust the headers as needed
    writer.writerow(["Event", "Key", "Timestamp"])
    writer.writerows(csv_rows)

print("CSV conversion complete!")
