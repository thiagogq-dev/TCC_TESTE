import json
import os

for file in os.listdir('./json/bics/'):
    with open(f'./json/bics/{file}', 'r') as f:
        data = json.load(f)
        for item in data:
            item.pop("inducing_commit_hash_pyszz", None)
            item.pop("inducing_commit_hash_pd", None)

    with open(f'./json/bics/{file}', 'w') as f:
        json.dump(data, f, indent=4)

# for file in os.listdir('./json/bics/'):
#     data_file = []
#     with open(f'./json/bics/{file}', 'r') as f:
#         data = json.load(f)
#         for record in data:
#             if len(record['matched']) > 0:
#                 spec_data = {
#                     "repo_name": record['repo_name'],
#                     "fix_commit_hash": record['matched'][0],
#                 }
#                 data_file.append(spec_data)

#     with open(f'./json/raw_data/{file}', 'w') as f:
#         json.dump(data_file, f, indent=4)

