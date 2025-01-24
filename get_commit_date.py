import json
from pydriller import Git, Repository
from utils.utils import match_bics, remove_empty_bug_hashs, update_matched_v2
import sys
import os
from datetime import timedelta

def get_commit_date(json_file, repo):
    with open(json_file) as f:
        data = json.load(f)
        for d in data:
           commit_hash = d["fix_commit_hash"]
           for commit in Repository("repos_dir/elasticsearch", single=commit_hash).traverse_commits():
                new_date = commit.author_date + timedelta(seconds=60)
                d["best_scenario_issue_date"] = new_date.isoformat()  # Salva como string em ISO 8601

    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_pd.py <json_file>")
        sys.exit(1)

    json_file = sys.argv[1]

    with open("repos_name.txt") as f:
        repos = f.readlines()
        repos = [x.strip() for x in repos]

        for repo in repos:
            repo_name = repo.split("/")[1]
            get_commit_date(json_file, f"repos_dir/{repo_name}")
