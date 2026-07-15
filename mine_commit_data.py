from utils.utils import extract_metrics_from_commit, preload_commits_index, group_file_by_fix, remove_duplicates
from pydriller import Git
import json
import os
from PRANALYZER.run_analyses import analyze_diff
import datetime

for folder in os.listdir("./dataset/4-metricas"):
    print(f"\nProcessando pasta: {folder}")
    for file in os.listdir(os.path.join("./dataset/4-metricas", folder)):
        if not file.endswith(".json"):
            continue
        
        folder_path = os.path.join("./dataset/4-metricas", folder, file)

        with open(folder_path, "r") as f:
            data = json.load(f)

        real_repo_name = data[0]["repo_name"].split("/")[-1]
        repo_path = f"repos_dir/{real_repo_name}"

        print(f"Precarregando index para {real_repo_name}...")

        # definir para 13 de maio de 2026
        to_datetime = datetime.datetime(2026, 5, 13, 23, 59, 59)
        commit_date_map, author_commits_map = preload_commits_index(repo_path, to_datetime)

        fix_hashes = [d["fix_commit_hash"] for d in data]

        print(f"Processando {len(fix_hashes)} issues em {file}...")

        metrics_cache = {}

        git_repo = Git(repo_path)

        current_index = 0
        total_commits = len(set(fix_hashes))
        for commit_hash in set(fix_hashes):
            current_index += 1
            print(f"Processando commit {commit_hash}... ({current_index}/{total_commits})")
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

        java_files_data = []
        for d in data:
            if d.get("java_files", 0) == 0:
                print(f"Aviso: Commit {d['fix_commit_hash']} de {d['repo_name']} não contém arquivos Java.")
            else:
                java_files_data.append(d)

        print(f"Arquivos removidos por não conter arquivos Java: {len(data) - len(java_files_data)}")

        with open(folder_path, "w") as f:
            json.dump (java_files_data, f, indent=4)

        print(f"Arquivo processado e salvo em: {folder_path}\n")