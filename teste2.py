from utils.utils import indent_file, update_matched
import os
import json

# for file in os.listdir('./json/bics/'):
#     indent_file(f'./json/bics/{file}')
# indent_file("./json/raw_data/issues.json")

# for file in os.listdir('./json/raw_data'):
#     with open(f'./json/raw_data/{file}', 'r') as f:
#         data = json.load(f)
#         for item in data:
#             item['earliest_issue_date'] = item.pop('issue_created_at')

#     with open(f'./json/raw_data/{file}', 'w') as f:
#         json.dump(data, f, indent=4)

# for file in os.listdir('./json/bics/'):
#     update_matched(f'./json/bics/{file}')

for file in os.listdir('./json/raw_data/'):
    with open(f'./json/raw_data/{file}', 'r') as f:
        data = json.load(f)
        for item in data:
           item.pop("issues", None)

    with open(f'./json/raw_data/{file}', 'w') as f:
        json.dump(data, f, indent=4)