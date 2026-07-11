from utils.utils import extract_metrics_from_commit, preload_commits_index
from pydriller import Git
import json
import os
from PRANALYZER.run_analyses import analyze_diff
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("data_folder", help="Pasta contendo os arquivos JSON a serem processados.")
args = parser.parse_args()

DATA_FOLDER = args.data_folder

for file in os.listdir(DATA_FOLDER):
    if not file.endswith(".json"):
        continue

    folder_path = os.path.join(DATA_FOLDER, file)

    with open(folder_path, "r") as f:
        data = json.load(f)

    if len(data) == 0:
        continue

    real_repo_name = data[0]["repo_name"].split("/")[-1]
    repo_path = f"repos_dir/{real_repo_name}"

    print(f"Precarregando index para {real_repo_name}...")
    commit_date_map, author_commits_map = preload_commits_index(repo_path)

    fix_hashes = [d["fix_commit_hash"] for d in data]

    print(f"Processando {len(fix_hashes)} issues em {file}...")

    metrics_cache = {}

    git_repo = Git(repo_path)

    for commit_hash in set(fix_hashes):
        try:
            commit = git_repo.get_commit(commit_hash)

            metrics_cache[commit_hash] = extract_metrics_from_commit(
                commit,
                author_commits_map,
                pranalyzer_fn=analyze_diff
            )

        except Exception as e:
            print(f"Erro ao processar commit {commit_hash}: {e}")

    for d in data:
        commit_hash = d["fix_commit_hash"]

        if commit_hash in metrics_cache:
            d.update(metrics_cache[commit_hash])
        else:
            print(f"Aviso: Commit {commit_hash} de {d['repo_name']} não encontrado.")

    data = [d for d in data if d.get("java_files", 0) > 0] # Manter apenas registros com arquivos Java modificados

    with open(folder_path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Arquivo processado e salvo em: {folder_path}\n")