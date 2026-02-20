"""
Script para processar um repositório específico com GitHub Actions.
Recebe como parâmetros: owner, repo_name e version (subfolder).

Uso:
    python process_single_repo.py --owner <owner> --repo <repo_name>
    
Exemplo:
    python process_single_repo.py --owner spring-projects --repo spring-boot 
"""
import argparse
import json
import os
import sys
from pydriller import Git, Repository

def get_commit_data(commit_hash, repo_name):
    for commit in Repository(path_to_repo=f"repos_dir/{repo_name}", single=commit_hash).traverse_commits():        
        data = {
            "commit_author": commit.author.name,
            "committer": commit.committer.name,
            "commit_date": commit.author_date.isoformat(),
            "committer_date": commit.committer_date.isoformat(),
            "changed_files": commit.files,
            "deletions": commit.deletions,
            "insertions": commit.insertions,
            "lines": commit.lines,
            "dmm_unit_size": commit.dmm_unit_size,
            "dmm_unit_complexity": commit.dmm_unit_complexity,
            "dmm_unit_interfacing": commit.dmm_unit_interfacing
        }
        
        return data
    
DATA_FOLDER = "./data"
OUTPUT_FOLDER = "./data_with_metrics"


def process_repo(subfolder: str) -> None:
    """
    Processa um repositório específico.
    
    Args:
        subfolder: Subpasta do repositório (ex: spring-boot)
    """
    # Construir o caminho da pasta
    folder_path = os.path.join(DATA_FOLDER, subfolder)
    
    if not os.path.isdir(folder_path):
        print(f"Erro: Caminho não encontrado: {folder_path}")
        sys.exit(1)
    
    for version_folder in os.listdir(folder_path):
        version_path = os.path.join(folder_path, version_folder)
        print(f"Processando pasta: {version_path}")
        if os.path.isdir(version_path):
            for file in os.listdir(version_path):
                if file.endswith(".json"):
                    file_path = os.path.join(version_path, file)
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        tam = len(data)
                        for index, d in enumerate(data):
                            print(f"Processando issue {index + 1} de {tam} em {subfolder}/{version_folder}/{file} | Commit hash: {d['fix_commit_hash']}")
                            real_repo_name = d["repo_name"].split("/")[-1]
                            new_data = get_commit_data(d["fix_commit_hash"], real_repo_name)
                            if new_data:
                                d.update(new_data)

                    output_path = os.path.join(OUTPUT_FOLDER, subfolder, version_folder)

                    os.makedirs(output_path, exist_ok=True)

                    with open(os.path.join(output_path, file), "w") as f:
                        json.dump(data, f, indent=4)
                    print(f"Arquivo processado e salvo em: {output_path}/{file}")


def main():
    parser = argparse.ArgumentParser(
        description="Processa um repositório específico com GitHub Actions"
    )
    parser.add_argument(
        "--subfolder",
        type=str,
        required=True,
        help="Subpasta do repositório (ex: spring-boot)"
    )
    
    args = parser.parse_args()
    
    try:
        process_repo(args.subfolder)
    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
