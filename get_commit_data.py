import requests
import json
import sys
import os
from pydriller import Git, Repository

def get_commit_data(commit_hash):
    for commit in Repository(path_to_repo="repos_dir/jabref", single=commit_hash).traverse_commits():
        commit_author = commit.author.name
        commiter = commit.committer.name 
        commit_date = commit.author_date.isoformat()
        committer_data = commit.committer_date.isoformat()
        modified_files = len(commit.modified_files)
        for mf in commit.modified_files:
            d = mf._complexity
        changed_files = commit.files
        deletions = commit.deletions
        insertions = commit.insertions
        lines = commit.lines
        dmm_unit_size = commit.dmm_unit_size
        dmm_unit_complexity = commit.dmm_unit_complexity
        dmm_unit_interfacing = commit.dmm_unit_interfacing

        return commit_author, commiter, commit_date, committer_data, changed_files, modified_files, deletions, insertions, lines, dmm_unit_size, dmm_unit_complexity, dmm_unit_interfacing

def process_file(file_path):
    print(f"Processing {file_path}")
    with open(file_path) as f:
        data = json.load(f)
        
        for record in data:
            commit_hash = record["fix_commit_hash"]
            commit_author, commiter, commit_date, committer_data, changed_files, modified_files, deletions, insertions, lines, dmm_unit_size, dmm_unit_complexity, dmm_unit_interfacing = get_commit_data(commit_hash)
            record["commit_author"] = commit_author
            record["commiter"] = commiter
            record["commit_date"] = commit_date
            record["committer_data"] = committer_data
            record["modified_files"] = modified_files
            record["changed_files"] = changed_files
            record["deletions"] = deletions
            record["insertions"] = insertions
            record["lines"] = lines
            record["dmm_unit_size"] = dmm_unit_size
            record["dmm_unit_complexity"] = dmm_unit_complexity
            record["dmm_unit_interfacing"] = dmm_unit_interfacing

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
           

for file in os.listdir("./json/jabref/v9"):
    # if file.endswith("11.json") or file.endswith("18.json") or file.endswith("28.json") or file.endswith("31.json") or file.endswith("41.json") or file.endswith("48.json") or file.endswith("51.json") or file.endswith("58.json") or file.endswith("61.json") or file.endswith("68.json") or file.endswith("71.json"):
    process_file(f"./json/jabref/v9/{file}")
# process_file("./json/v1/bics_bics_issues_14.json")
# if __name__ == "__main__":
#     if len(sys.argv) != 2:
#         print("Usage: python get_commit_pr.py <file_path>")
#         sys.exit(1)
    
#     file_path = sys.argv[1]
#     process_file(file_path)
