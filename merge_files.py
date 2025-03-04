from utils.utils import merge_files
import os
import json

merge_files('./json/raw_data', './json/raw_data/pd.json')

# for i in range(1, 31):
# #     merge_files(f'./json/jabref/v{i}', f'./json/raw_data/merged_data_{i}.json')

# read = []
# for file in os.listdir("./json/jabref/v1"):
#     with open(f"./json/jabref/v1/{file}") as f:
#         data = json.load(f)

#         for record in data:
#             if record["fix_commit_hash"] in read:
#                 print(record["fix_commit_hash"])
#             else:
#                 read.append(record["fix_commit_hash"])

#         # with open(f"./json/jabref/v1/{file}", "w") as f:
#         #     json.dump(data, f, indent=4)