import os
import json
import dotenv
from utils.utils import split_json_file

dotenv.load_dotenv()

REPO_NAME = 'jabref'
BICS_FOLDER = './bics'
DESTINATION_FILE = f'./data/data.json'
    
print(f'Getting usable BICs for {REPO_NAME}...')

data_file = []
for file in os.listdir(BICS_FOLDER):
    if file.endswith('.json'):
        with open(os.path.join(BICS_FOLDER, file), 'r') as f:
            data = json.load(f)
        
            for d in data:
                if len(d.get('bic')) > 0:
                    repo_name = d.get('repo_name').split('/')[-1]
                    fix_commit_hash = d.get('bic')[-1]
                    usable_bic = {
                        'repo_name': d.get('repo_name'),
                        'fix_commit_hash': fix_commit_hash,
                    }
                    data_file.append(usable_bic)

        with open(DESTINATION_FILE, 'w') as f:
            json.dump(data_file, f, indent=4)


split_json_file(DESTINATION_FILE, f'data/{REPO_NAME}', max_items_per_file=40)
os.remove(DESTINATION_FILE)