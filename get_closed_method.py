import os
import json

closed_records = []

for file in os.listdir('./json/raw_data'):
    with open(f'./json/raw_data/{file}', 'r') as f:
        data = json.load(f)
        for record in data:
            if record['search_type'] == 'CLOSED':
                closed_records.append(record)

with open('./json/raw_data/closed_issues.json', 'w') as f:
    json.dump(closed_records, f, indent=4)

print('Total closed issues:', len(closed_records))


    