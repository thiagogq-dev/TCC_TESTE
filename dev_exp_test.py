from pydriller import Git, Repository
import requests
import json
import sys
import os
from datetime import timedelta, datetime
from statistics import mode, mean

def get_commit_date(fix_commit):
    for commit in Repository("repos_dir/jabref", single=fix_commit).traverse_commits():
        data = commit.author_date  # 'data' ainda é um objeto datetime        
        adjusted_data = data - timedelta(days=1)
        return adjusted_data 
    
def get_contributor_activity(author, fix_date):
    since_date = datetime.fromisoformat("2014-03-11T14:48:42").replace(tzinfo=fix_date.tzinfo)
    count = 0
    for commit in Repository("repos_dir/jabref", only_authors=[author], since=since_date, to=fix_date).traverse_commits():
        count += 1
    return count
       

qtde_commits = []
analyses = {}

with open(f"./data/jabref/jabref.json") as f:
    data = json.load(f)
    for record in data:
        if record["test_changes"] == "Yes":
            fix_commit = record["fix_commit_hash"]
            fix_date = get_commit_date(fix_commit)
            author = record["commit_author"]
            activity = get_contributor_activity(author, fix_date)
            if activity not in analyses:
                analyses[activity] = 1
            else:
                analyses[activity] += 1
            qtde_commits.append(activity)

print(qtde_commits)
print(mode(qtde_commits))
print(mean(qtde_commits))

# somar valores de commits com atividade de contribuidor
total = 0
for key, value in analyses.items():
    total += value

print(total)


with open(f"./data/jabref/jabref_contributor_activity.json", "w") as f:
    json.dump(dict(sorted(analyses.items())), f, indent=4)

