import json
import os
import csv
from PRAnalizer import PRAnalizer
import sys
from pydriller import Git, Repository

repo_url = "repos_dir/jabref"

def check_test_changes(tests):
    test_changes = tests['removed'] + tests['added'] + tests['others']
    if test_changes > 0:
        return "Yes"
    return "No"

def run_pr_analizer(commit_sha, file_type):
    analizer = PRAnalizer(file_type)
    dadosDoPR  = analizer.retornaEstrutura();

    for commit in Repository(repo_url, single=commit_sha).traverse_commits():
        for modified_file in commit.modified_files:
            if modified_file is None:
               continue
            diff = modified_file.diff.split("\n")
            for line in diff:
                if analizer.checkIfModifier(line.strip()):
                     result = analizer.verify(line.strip())
                     modifierType = analizer.checkModifierType(line.strip())
                     dadosDoPR[result][modifierType] += 1
                     dadosDoPR['all'][modifierType] += 1

    print(dadosDoPR)
    return dadosDoPR


def process_file(file_path):
    with open(file_path) as f:
        data = json.load(f)
        
        for record in data:
            fix = record["fix_commit_hash"]
            fix_analyses = run_pr_analizer(fix, "JAVA")
            test_changes = fix_analyses['tests']
            record.pop("modified_files", None)
            record["test_changes"] = check_test_changes(test_changes)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

for file in os.listdir("../json_check/"):
    process_file(f"../json_check/{file}")