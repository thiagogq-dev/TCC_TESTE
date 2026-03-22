import json
import os
import sys
from collections import defaultdict

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RELATIONS_DIR = os.path.join(BASE_DIR, 'relations')
BASE_REPOS_DIR = os.path.join(BASE_DIR, 'repos_dir')

for file in os.listdir(DATA_DIR):
    file_path = os.path.join(DATA_DIR, file)

    if not file.endswith(".json"):
        continue

    with open(file_path) as f:
        file_name = os.path.splitext(file)[0]
        bics = json.load(f)
    repo_name = bics[0].get('repo_name').split('/')[-1]

    bic_index = defaultdict(list)

    for item in bics:
        for bug_causer in item.get("bic", []):
            bic_index[bug_causer].append(item.get("fix_commit_hash"))

    path = []

    for data in bics:
        possible_bic = data.get('fix_commit_hash')

        path.append({
            "Repository": data.get('repo_name'),
            "commit": possible_bic,
            "commit_date": data.get("commit_date"),
            "fixed_by": bic_index.get(possible_bic, []),
            "dmm_unit_size": data.get("dmm_unit_size"),
            "dmm_unit_complexity": data.get("dmm_unit_complexity"),
            "dmm_unit_interfacing": data.get("dmm_unit_interfacing"),
            "files_with_test": data.get("files_with_test"),
            "has_test_files": data.get("has_test_files"),
            "has_tests": data.get("has_tests"),
            "real_code_files": data.get("real_code_files"),
            "test_file_ratio": data.get("test_file_ratio"),
            "added_asserts": data.get("added_asserts"),
            "removed_asserts": data.get("removed_asserts"),
            "real_lines_changed": data.get("real_lines_changed"),
            "contributor_activity": data.get("contributor_activity")
        })

    os.makedirs(RELATIONS_DIR, exist_ok=True)

    with open(os.path.join(RELATIONS_DIR, f'{file_name}.json'), 'w') as f:
        json.dump(path, f, indent=4)