import json
import os
import csv
import sys
import requests
from github import Github
from github import Auth

API_TOKENS = [
]


token_pygithub = ""
g = Github(token_pygithub)

repo = g.get_repo("JabRef/jabref")

token_index = 0
attempted_tokens = 0

def get_headers():
    return {
        'Authorization': f'token {API_TOKENS[token_index]}'
    }

def switch_token():
    global token_index
    token_index = (token_index + 1) % len(API_TOKENS)


def run_pr_analizer(data):
    java_files = 0
    for file in data['files']:
        if file['filename'].endswith('.java'):
            java_files += 1

    return java_files
   

def run_pr_analizer_bigger(commit_sha):
    commit = repo.get_commit(sha=commit_sha)
    java_files = 0
    for file in commit.files:
        if file.filename.endswith('.java'):
            java_files += 1

    return java_files


def process_file(file_path):
    with open(file_path) as f:
        data = json.load(f)
        
        for record in data: 
            if 'checked' not in record:
                if record["changed_files"] > 300:
                    commit_hash = record["fix_commit_hash"]
                    changed_files = run_pr_analizer_bigger(commit_hash)
                    record["changed_files"] = changed_files
                    record["checked"] = True
                else:
                    header = get_headers()
                    commit_hash = record["fix_commit_hash"]
                    response = requests.get(f'https://api.github.com/repos/JabREf/jabref/commits/{commit_hash}', headers=header)

                    if response.status_code == 403:
                        switch_token()
                        header = get_headers()
                        response = requests.get(f'https://api.github.com/repos/JabREf/jabref/commits/{commit_hash}', headers=header)
                        print(response.status_code)
                    commit_data = response.json()
                    changed_files = run_pr_analizer(commit_data)
                    record["changed_files"] = changed_files
                    record["checked"] = True

            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)

    # with open(file_path, "w") as f:
    #     json.dump(data, f, indent=4)


process_file("./data/jabref/jabref.json")