import os
import json
from utils.utils import get_commit_date_v2
import dotenv
from utils.utils import split_json_file

dotenv.load_dotenv()

REPO_NAME = 'junit-framework'

print(f'Getting usable BICs for {REPO_NAME}...')

data_file = []
for file in os.listdir('./bics'):
    if file.endswith('.json'):
        with open(os.path.join('./bics', file), 'r') as f:
            data = json.load(f)
        
            for d in data:
                if len(d.get('bic')) > 0:
                    repo_name = d.get('repo_name').split('/')[-1]
                    fix_commit_hash = d.get('bic')[-1]
                    best_scenario_issue_date = get_commit_date_v2(fix_commit_hash, REPO_NAME)
                    usable_bic = {
                        'repo_name': d.get('repo_name'),
                        'fix_commit_hash': fix_commit_hash,
                        'best_scenario_issue_date': best_scenario_issue_date
                    }
                    data_file.append(usable_bic)

        with open(f'data/data.json', 'w') as f:
            json.dump(data_file, f, indent=4)


split_json_file('data/data.json', f'data/{REPO_NAME}', max_items_per_file=40)