import json
import os
import csv
from PRAnalizer import PRAnalizer
import sys
import requests
from github import Github
from github import Auth

API_TOKENS = [
]


token_pygithub = ""

g = Github(token_pygithub)

repo = g.get_repo("elastic/elasticsearch")
token_index = 0
attempted_tokens = 0

def get_headers():
    return {
        'Authorization': f'token {API_TOKENS[token_index]}'
    }

def switch_token():
    global token_index
    token_index = (token_index + 1) % len(API_TOKENS)

def check_test_changes(tests):
    test_changes = tests['removed'] + tests['added'] + tests['others']
    if test_changes > 0:
        return "Yes"
    return "No"

def run_pr_analizer(data, file_type, commit_hash):
    analizer = PRAnalizer(file_type)

    files_with_test = 0
    for file in data['files']:
        if 'patch' not in file:
            continue
        
        dadosDoPR  = analizer.retornaEstrutura();
        itensAlterados = file['patch']
        aux = itensAlterados.split("\n")

        for item in aux:
            if(analizer.checkIfModifier(item.strip())):
                result 			= analizer.verify(item.strip())
                # print(item.strip() + "    "+ result)
                modifierType 	= analizer.checkModifierType(item.strip())
                dadosDoPR[result][modifierType] += 1
                dadosDoPR['all'][modifierType] += 1
        
        if check_test_changes(dadosDoPR['tests']) == "Yes":
            files_with_test += 1
                
    return files_with_test

def run_pr_analizer_bigger(commit_sha, file_type):
    analizer = PRAnalizer(file_type)
    files_with_test = 0
    commit = repo.get_commit(sha=commit_sha)
    files = list(commit.files)
    
    for file in commit.files:
        if  file.patch is None:
            continue
        dadosDoPR  = analizer.retornaEstrutura();
        diff = file.patch.split("\n")
        for line in diff:
            if analizer.checkIfModifier(line.strip()):
                result = analizer.verify(line.strip())
                modifierType = analizer.checkModifierType(line.strip())
                dadosDoPR[result][modifierType] += 1
                dadosDoPR['all'][modifierType] += 1

        if check_test_changes(dadosDoPR['tests']) == "Yes":
            files_with_test += 1

    return files_with_test, len(files)

for folder in os.listdir('./json/elastic/'):
    for file in os.listdir(f'./json/elastic/{folder}'):
        with open(f'./json/elastic/{folder}/{file}') as f:
            print(f'Processing ./json/elastic/{folder}/{file}')
            data = json.load(f)
            for record in data:
                if record["changed_files"] > 300:
                    commit_hash = record["fix_commit_hash"]
                    files_with_tests, files = run_pr_analizer_bigger(commit_hash, "JAVA")
                    record["files_with_tests"] = files_with_tests
                    print(f"Files Lib: {files} - Files PD: {record['changed_files']}")
                else:

                    header = get_headers()
                    commit_hash = record["fix_commit_hash"]
                    response = requests.get(f'https://api.github.com/repos/elastic/elasticsearch/commits/{commit_hash}', headers=get_headers())
                    print(response.status_code)

                    if response.status_code == 403:
                        switch_token()
                        attempted_tokens += 1
                        header = get_headers()
                        response = requests.get(f'https://api.github.com/repos/elastic/elasticsearch/commits/{commit_hash}', headers=header)

                    response_data = response.json()
                    files_with_tests = run_pr_analizer(response_data, "JAVA", commit_hash)
                    record["files_with_tests"] = files_with_tests

        with open(f'./json/elastic/{folder}/{file}', "w") as f:
            json.dump(data, f, indent=4)

# def process_file(file_path):
#     global attempted_tokens
#     with open(file_path) as f:
#         data = json.load(f)
        
#         for record in data: 
#             while attempted_tokens < len(API_TOKENS):
#                 header = get_headers()
#                 commit_hash = record["fix_commit_hash"]
#                 response = requests.get(f'https://api.github.com/repos/JabRef/jabref/commits/{commit_hash}', headers=header)

#                 if response.status_code == 403:
#                     switch_token()
#                     attempted_tokens += 1
#                     header = get_headers()
#                     response = requests.get(f'https://api.github.com/repos/JabRef/jabref/commits/{commit_hash}', headers=header)

#             data = response.json()
#             fix_analyses = run_pr_analizer(data, "JAVA")
#             test_changes = fix_analyses['tests']
#             record["test_changes"] = check_test_changes(test_changes)

#     with open(file_path, "w") as f:
#         json.dump(data, f, indent=4)

# if __name__ == "__main__":
#     if len(sys.argv) != 2:
#         print("Usage: python get_commit_pr.py <file_path>")
#         sys.exit(1)
    
#     file_path = sys.argv[1]
#     process_file(file_path)
