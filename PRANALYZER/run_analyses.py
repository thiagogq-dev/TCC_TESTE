import json
import os
import csv
from PRAnalizer import PRAnalizer
import sys
import requests

API_TOKENS = [
    os.getenv('API_TOKEN_1'),
    os.getenv('API_TOKEN_2'),
    os.getenv('API_TOKEN_3'),
    os.getenv('API_TOKEN_4'),
    os.getenv('API_TOKEN_5'),
    os.getenv('API_TOKEN_6'),
    os.getenv('API_TOKEN_7'),
    os.getenv('API_TOKEN_8'),
    os.getenv('API_TOKEN_9'),
    os.getenv('API_TOKEN_10')
]

token_index = 0
attempted_tokens = 0

def get_headers():
    return {
        'Authorization': f'token {API_TOKENS[token_index]}'
    }

def switch_token():
    global token_index
    token_index = (token_index + 1) % len(API_TOKENS)

repo_url = "repos_dir/jabref"

def check_test_changes(tests):
    test_changes = tests['removed'] + tests['added'] + tests['others']
    if test_changes > 0:
        return "Yes"
    return "No"

def run_pr_analizer(data, file_type):
    analizer = PRAnalizer(file_type)
    dadosDoPR  = analizer.retornaEstrutura();
    print(data)
    for file in data['files']:
        itensAlterados = file['patch']
        aux = itensAlterados.split("\n")

        for item in aux:
            if(analizer.checkIfModifier(item.strip())):
                result 			= analizer.verify(item.strip())
                # print(item.strip() + "    "+ result)
                modifierType 	= analizer.checkModifierType(item.strip())
                dadosDoPR[result][modifierType] += 1
                dadosDoPR['all'][modifierType] += 1
                
    return dadosDoPR


def process_file(file_path):
    global attempted_tokens
    with open(file_path) as f:
        data = json.load(f)
        
        for record in data: 
            while attempted_tokens < len(API_TOKENS):
                header = get_headers()
                commit_hash = record["fix_commit_hash"]
                response = requests.get(f'https://api.github.com/repos/JabRef/jabref/commits/{commit_hash}', headers=header)

                if response.status_code == 403:
                    switch_token()
                    attempted_tokens += 1
                    header = get_headers()
                    response = requests.get(f'https://api.github.com/repos/JabRef/jabref/commits/{commit_hash}', headers=header)

            data = response.json()
            fix_analyses = run_pr_analizer(data, "JAVA")
            test_changes = fix_analyses['tests']
            record["test_changes"] = check_test_changes(test_changes)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_commit_pr.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    process_file(file_path)
