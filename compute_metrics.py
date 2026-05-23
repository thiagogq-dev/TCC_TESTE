from utils.utils import get_commit_data, preload_commits_index
import json
import os

DATA_FOLDER = "./data"
for file in os.listdir(DATA_FOLDER):
    if not file.endswith(".json"):
        continue
    folder_path = os.path.join(DATA_FOLDER, file)
    with open(folder_path, "r") as f:
        data = json.load(f)
        tam = len(data)
        # Descobre o nome do repositório real (assume que todos os registros do arquivo são do mesmo repo)
        if len(data) == 0:
            continue
        real_repo_name = data[0]["repo_name"].split("/")[-1]
        commit_date_map, author_commits_map = preload_commits_index(f"repos_dir/{real_repo_name}")
        for index, d in enumerate(data):
            print(f"Processando issue {index + 1} de {tam} em {file} | Commit hash: {d['fix_commit_hash']}")
            new_data = get_commit_data(d["fix_commit_hash"], real_repo_name, commit_date_map, author_commits_map)
            if new_data:
                d.update(new_data)
    with open(folder_path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Arquivo processado e salvo em: {folder_path}")