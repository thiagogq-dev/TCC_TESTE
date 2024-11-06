import json
import os
import requests
import csv
from PRAnalizer import PRAnalizer
import sys

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

def get_headers():
    return {
        'Authorization': f'token {API_TOKENS[token_index]}'
    }

def switch_token():
    global token_index
    token_index = (token_index + 1) % len(API_TOKENS)


def check_rate_limit(headers):
    response = requests.get('https://api.github.com/rate_limit', headers=headers)
    rate_limit = response.json()["rate"]["remaining"]
    reset_time = response.json()["rate"]["reset"]
    
    if rate_limit == 0:
        switch_token()

# if not os.path.exists("../csv"):
#     os.makedirs("../csv")

# if os.path.exists("../csv/commit_analizer.csv"):
#     os.remove("../csv/commit_analizer.csv")

# API_TOKEN = os.getenv("API_TOKEN")

def check_test_changes(tests):
    test_changes = tests['removed'] + tests['added'] + tests['others']
    if test_changes > 0:
        return "Yes"
    return "No"

def run_pr_analizer(commit_sha, file_type, repo_url):
    # headers = {
    #     'Authorization': f'token {API_TOKEN}',
    # }

    headers = get_headers()
    link = f"https://api.github.com/repos/JabRef/jabref/commits/{commit_sha}"
    response = requests.get(link, headers=headers)
    if response.status_code == 403:
        check_rate_limit(headers)
        headers = get_headers()
        response = requests.get(link, headers=headers)
    analizer = PRAnalizer(file_type)
    dadosDoPR  = analizer.retornaEstrutura();
    arquivos = json.loads(response.text).get('files', [])

    if arquivos:
        for arquivo in arquivos:
            linkDocumentoCompleto = arquivo['raw_url']
            if "patch" not in arquivo:
                continue
            itensAlterados = arquivo['patch']
            aux = itensAlterados.split("\n");

            for item in aux:
                if analizer.checkIfModifier(item.strip()):
                    result = analizer.verify(item.strip())
                    modifierType = analizer.checkModifierType(item.strip())
                    dadosDoPR[result][modifierType] += 1
                    dadosDoPR['all'][modifierType] += 1

    return dadosDoPR

def process_file(file_path):
    with open(file_path) as f:
        data = json.load(f)
        
        for record in data:
            fix = record["fix_commit_hash"]
            fix_analyses = run_pr_analizer(fix, "JAVA", record["repo_url"])
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



# with open("../json/consolidated_data.json") as f:
#     data = json.load(f)

#     data_size = len(data)

#     for d in data:
#         repo_url = d["repo_url"]
#         fix_commit_hash = d["fix_commit_hash"]

#         bic_analyses = {}
#         bic_commit_hash = "-"
#         bic_changes = "-"
        
#         fix_analyses = run_pr_analizer(fix_commit_hash, "JAVA", repo_url)
#         teste_fix = fix_analyses['tests']
#         fix_changes = check_test_changes(teste_fix)

#         if len(d["matched"]) >= 1:
#             bic_commit_hash = d["matched"][0]
#             bic_analyses = run_pr_analizer(bic_commit_hash, "JAVA", repo_url)
#             teste_bic = bic_analyses['tests']
#             bic_changes = check_test_changes(teste_bic)

#         mode = 'a' if os.path.exists("../csv/commit_analizer.csv") else 'w'

#         with open("../csv/commit_analizer.csv", mode, newline='') as csvfile:
#             fieldnames = ['Repository', 'Fix Commit SHA', 'Tests Changes in Fix', 'BIC Commit SHA', 'Tests Changes in BIC']
#             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

#             if mode == 'w':
#                 writer.writeheader()

#             writer.writerow({'Repository': repo_url, 'Fix Commit SHA': fix_commit_hash, 'Tests Changes in Fix': fix_changes, 'BIC Commit SHA': bic_commit_hash, 'Tests Changes in BIC': bic_changes})
