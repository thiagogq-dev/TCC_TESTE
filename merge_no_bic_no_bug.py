"""
Este script combina os arquivos JSON de "no_bug" e "no_bic" em um único arquivo JSON para cada repositório, garantindo que não haja duplicatas com base no campo "fix_commit_hash". O resultado é salvo na pasta "./dataset/4-metricas/without_bic/".
Esta lista conterá os commits de "não correção", pos combina commits de issues não classificadas como bugs e commits que não possuem BICs.
"""
import os
import json

filenames = [
    "elasticsearch.json",
    "jabref.json",
    "junit-framework.json",
    "keycloak.json",
    "pulsar.json",
    "spring-boot.json"
]

def load_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f: # Adicionado encoding utf-8 por segurança
        data = json.load(f)
    return data

# Opcional: Garante que a pasta de saída exista antes de tentar salvar
os.makedirs("./dataset/4-metricas/without_bic/", exist_ok=True)

for file in filenames:
    new_data = []
    
    # Carrega os dados
    no_bug = load_data(f"./dataset/2-classificados_llm/no_bug_issues/{file}")
    no_bic = load_data(f"./dataset/3-szz/without_bic/{file}")
    
    # Adiciona os dados do no_bic
    new_data.extend(no_bic)
    new_data.extend(no_bug)

    seen_fix_commit_hashes = set()
    final_result = []
    for entry in new_data:
        fix_commit_hash = entry.get("fix_commit_hash")
        if fix_commit_hash not in seen_fix_commit_hashes:
            seen_fix_commit_hashes.add(fix_commit_hash)
            final_result.append(entry)
    with open(f"./dataset/4-metricas/without_bic/{file}", "w", encoding="utf-8") as n:
        json.dump(final_result, n, indent=4)