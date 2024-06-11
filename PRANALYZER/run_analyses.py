import json
import os
import requests
import csv
from PRAnalizer import PRAnalizer

if not os.path.exists("../csv"):
    os.makedirs("../csv")

if os.path.exists("../csv/commit_analizer.csv"):
    os.remove("../csv/commit_analizer.csv")

API_TOKEN = os.getenv("API_TOKEN")

def check_test_changes(tests):
    test_changes = tests['removed'] + tests['added'] + tests['others']
    if test_changes > 0:
        return "Yes"
    return "No"

def run_pr_analizer(commit_sha, file_type, repo_url):
    headers = {
        'Authorization': f'token {API_TOKEN}',
    }
    link = f"https://api.github.com/repos/{repo_url}/commits/{commit_sha}"
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

with open("../json/consolidated_data.json") as f:
    data = json.load(f)

    data_size = len(data)

    for d in data:
        repo_url = d["repo_url"]
        fix_commit_hash = d["fix_commit_hash"]

        bic_analyses = {}
        bic_commit_hash = "-"
        bic_changes = "-"
        
        fix_analyses = run_pr_analizer(fix_commit_hash, "JAVA", repo_url)
        teste_fix = fix_analyses['tests']
        fix_changes = check_test_changes(teste_fix)

        if len(d["matched"]) >= 1:
            bic_commit_hash = d["matched"][0]
            bic_analyses = run_pr_analizer(bic_commit_hash, "JAVA", repo_url)
            teste_bic = bic_analyses['tests']
            bic_changes = check_test_changes(teste_bic)

        mode = 'a' if os.path.exists("../csv/commit_analizer.csv") else 'w'

        with open("../csv/commit_analizer.csv", mode, newline='') as csvfile:
            fieldnames = ['Repository', 'Fix Commit SHA', 'Tests Changes in Fix', 'BIC Commit SHA', 'Tests Changes in BIC']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if mode == 'w':
                writer.writeheader()

            writer.writerow({'Repository': repo_url, 'Fix Commit SHA': fix_commit_hash, 'Tests Changes in Fix': fix_changes, 'BIC Commit SHA': bic_commit_hash, 'Tests Changes in BIC': bic_changes})
