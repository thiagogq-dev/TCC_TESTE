import os
import json
import dotenv
from utils.utils import split_json_file
from pydriller import Repository

dotenv.load_dotenv()

REPO_NAME = ''
BICS_FOLDER = './bics' # Path to the folder containing the BICs JSON files from the SZZ execution
DESTINATION_FILE = f'./data/data.json' # Path to the file where the usable BICs will be stored before splitting into multiple files
    
print(f'Getting usable BICs for {REPO_NAME}...')

data_file = []
for file in os.listdir(BICS_FOLDER):
    if file.endswith('.json'):
        original_file_path = os.path.join(BICS_FOLDER, file)
        with open(original_file_path, 'r') as f:
            data = json.load(f)
        
            repo_name = data[0].get('repo_name').split('/')[-1]
            for d in data:
                if len(d.get('bic')) > 0:
                    commit_sha = d['fix_commit_hash']
                    bic = d.get('bic')[-1]
                    for commit in Repository(f'./repos_dir/{repo_name}', single=commit_sha).traverse_commits():
                        if commit.merge:
                            d['bic'] = []
                            continue
                    usable_bic = {
                        'repo_name': d.get('repo_name'),
                        'fix_commit_hash': bic,
                    }
                    data_file.append(usable_bic)

        with open(original_file_path, 'w') as f:
            json.dump(data, f, indent=4)

with open(DESTINATION_FILE, 'w') as f:
    json.dump(data_file, f, indent=4)
split_json_file(DESTINATION_FILE, f'data/{REPO_NAME}', max_items_per_file=40)
os.remove(DESTINATION_FILE)