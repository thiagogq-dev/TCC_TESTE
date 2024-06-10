import json
import glob

json_files = glob.glob('./json/bics_issues_data_*.json')

combined_data = []

for file in json_files:
    with open(file, 'r') as f:
        data = json.load(f)
        combined_data.extend(data)

with open('./json/consolidated_data.json', 'w') as f:
    json.dump(combined_data, f, indent=4)
