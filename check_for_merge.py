"""
Este script percorre todos os arquivos JSON na pasta "./dataset/3-szz/" e verifica se o commit BIC (Bug Inducing Commit) é um commit de merge. Se for, ele remove o BIC e define o tipo de método como "none". O script utiliza a biblioteca PyDriller para acessar os commits do repositório Git especificado no arquivo JSON.
"""

from pydriller import Repository
import os
import json

INPUT_FOLDER = "./dataset/3-szz/"

for file in os.listdir(INPUT_FOLDER):
    if not file.endswith(".json"):
        continue

    print(f"Processando arquivo: {file}...")
    folder_path = os.path.join(INPUT_FOLDER, file)

    with open(folder_path, "r") as f:
        data = json.load(f)

    repo = f"./repos_dir/{data[0]['repo_name'].split('/')[-1]}"
    for d in data:
        if d.get("bic"): 
            bic = d.get("bic")[0]
            for commit in Repository(repo, single=bic).traverse_commits():
                if commit.merge:
                    d["bic"] = []
                    d["method_type"] = "none"

    with open(os.path.join(INPUT_FOLDER, file), "w") as f:
        json.dump(data, f, indent=4)