import requests
import json
import sys
import os
from pydriller import Git, Repository

def get_commit_data(commit_hash):
    for commit in Repository("repos_dir/jabref", single=commit_hash).traverse_commits():
        commit_author = commit.author.name
        commiter = commit.committer.name 
        commit_date = commit.author_date.isoformat()
        committer_data = commit.committer_date.isoformat()
        modified_files = len(commit.modified_files)
        changed_files = commit.files
        deletions = commit.deletions
        insertions = commit.insertions
        lines = commit.lines
        dmm_unit_size = commit.dmm_unit_size
        dmm_unit_complexity = commit.dmm_unit_complexity
        dmm_unit_interfacing = commit.dmm_unit_interfacing

        return commit_author, commiter, commit_date, committer_data, changed_files, modified_files, deletions, insertions, lines, dmm_unit_size, dmm_unit_complexity, dmm_unit_interfacing

def process_file(file_path):
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
           
    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_commit_pr.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    process_file(file_path)
