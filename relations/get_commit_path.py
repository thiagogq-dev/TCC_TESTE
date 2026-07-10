import argparse
import json
import os
import sys
from collections import defaultdict

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RELATIONS_DIR = os.path.join(BASE_DIR, 'relations')
BASE_REPOS_DIR = os.path.join(BASE_DIR, 'repos_dir')

def proccess_data_dir(data_dir):
    """
    Processa todos os arquivos JSON em um diretório específico, extraindo informações de commits e suas relações.
    Args:
        data_dir (str): Caminho para o diretório contendo os arquivos JSON de entrada.
    """
    for file in os.listdir(data_dir):
        file_path = os.path.join(data_dir, file)

        if not file.endswith(".json"):
            continue

        with open(file_path) as f:
            file_name = os.path.splitext(file)[0]
            bics = json.load(f)

        bic_index = defaultdict(list)

        for item in bics:
            for bug_causer in item.get("bic", []):
                bic_index[bug_causer].append(item.get("fix_commit_hash"))

        path = []

        for data in bics:
            possible_bic = data.get('fix_commit_hash')

            path.append({
                "repository": data.get('repo_name'),
                "commit": possible_bic,
                "commit_date": data.get("commit_date"),
                "fixed_by": bic_index.get(possible_bic, []), # Lista de commits que corrigiram o commit atual
                "dmm_unit_size": data.get("dmm_unit_size"),
                "dmm_unit_complexity": data.get("dmm_unit_complexity"),
                "dmm_unit_interfacing": data.get("dmm_unit_interfacing"),
                "java_lines_changed": data.get("java_lines_changed"),
                "contributor_activity": data.get("contributor_activity"),
                "java_files": data.get("java_files"),
                "has_test_files": data.get("has_test_files"),
                "has_asserts_changes": data.get("has_asserts_changes"),
                "files_with_asserts_changes": data.get("files_with_asserts_changes"),
                "test_files_with_asserts_changes": data.get("test_files_with_asserts_changes"),
                "added_asserts": data.get("added_asserts"),
                "removed_asserts": data.get("removed_asserts"),
                "asserts_changes_type": data.get("asserts_changes_type")
            })

        os.makedirs(RELATIONS_DIR, exist_ok=True)

        with open(os.path.join(RELATIONS_DIR, f'{file_name}.json'), 'w') as f:
            json.dump(path, f, indent=4)

def main():
    parser = argparse.ArgumentParser(
        description="Monta os cominhos percorridos da cadeia"
    )
    parser.add_argument(
        "data_dir",
        nargs="?",
        default=".",
        help="Diretório onde estão os arquivos JSON de entrada (default: diretório atual)"
    )

    args = parser.parse_args()

    if not os.path.isdir(args.data_dir):
        raise SystemExit(f"Caminho inválido: {args.data_dir} não é um diretório.")
    
    proccess_data_dir(args.data_dir)

if __name__ == "__main__":
    main()
