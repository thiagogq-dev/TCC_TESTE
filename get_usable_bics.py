import os
from pathlib import Path
from typing import Any
from utils.utils import is_commit_valid, split_json_file, merge_files
import argparse
import json
import re
import sys

OUTPUT_FOLDER = "data"

def build_known_results(out_folder: str) -> dict[str, dict]:
    """
    Cria um índice:
        fix_commit_hash -> registro completo
    """
    known_results = {}

    for entry in merge_files(out_folder, "v1"):
        fix_commit = entry.get("fix_commit_hash")

        if fix_commit:
            known_results[fix_commit] = entry

    print(f"Carregados {len(known_results)} commits já processados.")
    return known_results

def build_szz_data(repo_name: str, commit_hash: str) -> dict:
    return {
        "repo_name": repo_name,
        "fix_commit_hash": commit_hash,
    }

def process_first_attempt(entry: dict) -> dict | None:
    bics = entry.get("bic") or []

    if not bics:
        return None

    candidate_bic = bics[-1]

    repo_name = entry["repo_name"]
    repo_path = f'./repos_dir/{repo_name.split("/")[-1]}'

    status, msg = is_commit_valid(repo_path, candidate_bic)
    
    if not status:
        print(f"Skipping commit {candidate_bic} in repo {repo_name}: {msg}")
        entry["bic"] = [] 
        return None

    return build_szz_data(
        repo_name=repo_name,
        commit_hash=candidate_bic,
    )


def process_retry(entry: dict) -> dict:
    return build_szz_data(
        repo_name=entry["repo_name"],
        commit_hash=entry["fix_commit_hash"],
    )


def prepare_data(input_folder: str, first_actions_attempt: bool = False, known_results: dict[str, dict] | None = None, next_version_folder: str | None = None) -> list[dict]:
    results: list[dict] = []
    seen_commits: set[tuple[str, str]] = set()
    already_processed_count = []

    for json_file in Path(input_folder).glob("*.json"):
        with json_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            if first_actions_attempt:
                bics = entry.get("bic") or []
                candidate_bic = bics[-1] if bics else None
                
                if candidate_bic and known_results and candidate_bic in known_results:
                    print(f"Commit {entry['fix_commit_hash']} em repo {entry['repo_name']} já processado, atualizando para não processar novamente.")
                    cached = known_results[candidate_bic]
                    already_processed_count.append({
                        **cached,
                    })
                    continue

                result = process_first_attempt(entry)
            else:
                result = process_retry(entry)

            if result:
                key = (
                    result["repo_name"],
                    result["fix_commit_hash"]
                )

                if key not in seen_commits:
                    seen_commits.add(key)
                    results.append(result)
                else:
                    print(f"Commit {result['fix_commit_hash']} in repo {result['repo_name']} já processado, pulando.")

        with json_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    if next_version_folder and already_processed_count:
        with open(f"out/{next_version_folder}", "w", encoding="utf-8") as f:
            json.dump(already_processed_count, f, indent=4)

    print(f"Total de commits já processados: {len(already_processed_count)}")
    return results

def get_latest_version_folder(input_folder: Path) -> Path | None:
    version_pattern = re.compile(r"^v(\d+)$")
    parent_folder = input_folder.parent

    version_folders = []
    for child in parent_folder.iterdir():
        if not child.is_dir():
            continue

        match = version_pattern.match(child.name)
        if match:
            version_folders.append((int(match.group(1)), child))

    if not version_folders:
        return None

    version_folders.sort(key=lambda item: item[0])
    return version_folders[-1][1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare data for SZZ analysis"
    )   

    parser.add_argument(
        "--already_processed_folder",
        required=False,
        help="Pasta contendo os arquivos de todas as versões anteriores do GitHub Actions, para verificar commits já processados",
    )
    parser.add_argument(
        "--next_version_folder",
        required=False,
        help="A versão referente a próxima tentativa, para salvar os commits já processados",
    )
    parser.add_argument(
        "--input_folder",
        required=True,
        help="Pasta contendo os arquivos de entrada JSON da última execução do GitHub Actions",
    )
    parser.add_argument(
        "--file_prefix",
        required=True,
        help="Prefixo para os arquivos JSON de saída",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=50,
        help="Número de registros por arquivo JSON de saída",
    )
    parser.add_argument(
        "--first_actions_attempt",
        action="store_true",
        help="Indica se esta é a primeira tentativa de processar os arquivos do GitHub Actions. Se ativado, o script tentará extrair o 'bic' diretamente dos arquivos de entrada e verificará se já foi processado anteriormente usando a pasta de versões anteriores.",
    )

    args = parser.parse_args()

    input_folder = Path(args.input_folder)
    first_actions_attempt = args.first_actions_attempt
    
    if args.already_processed_folder:
        if not os.path.exists(args.already_processed_folder):
            confirmation = input(
                f"Aviso: A pasta '{args.already_processed_folder}' não existe. "
                "Deseja continuar mesmo assim? [y/N]: "
                "Caso resposta 'y', o sript não verificará se há commits já processados e todos serão executados no pyszz. "
            ).strip().lower()
            if confirmation not in {"y", "yes", "s", "sim"}:
                print("Execução cancelada pelo usuário.")
                sys.exit(1)
            else:
                args.already_processed_folder = None

    if not input_folder.exists():
        raise FileNotFoundError(
            f"Input folder '{input_folder}' does not exist."
        )
    
    if not first_actions_attempt and "out/v" in str(input_folder):
        print(
            "Aviso: Parece que você está tentando processar arquivos de erro do GitHub Actions, mas o input_folder contém 'out/v', indicando que pode ser a "
            "primeira tentativa. Considere usar a flag --first_actions_attempt "
            "ou verificar se o input_folder está correto."
        )
        confirmation = input(
            "Deseja continuar mesmo assim? [y/N]: "
        ).strip().lower()
        if confirmation not in {"y", "yes", "s", "sim"}:
            print("Execução cancelada pelo usuário.")
            sys.exit(1)


    latest_folder = get_latest_version_folder(input_folder)
    if latest_folder and input_folder.name != latest_folder.name:
        print(
            f"Aviso: o input_folder informado foi '{input_folder}', mas o "
            f"mais recente encontrado é '{latest_folder}'."
        )
        confirmation = input(
            "Deseja continuar mesmo assim? [y/N]: "
        ).strip().lower()
        if confirmation not in {"y", "yes", "s", "sim"}:
            print("Execução cancelada pelo usuário.")
            sys.exit(1)

    known_results = build_known_results(args.already_processed_folder) if args.already_processed_folder else None

    data = prepare_data(
        input_folder=str(input_folder),
        first_actions_attempt=first_actions_attempt,
        known_results=known_results,
        next_version_folder=args.next_version_folder
    )

    split_json_file(
        data,
        OUTPUT_FOLDER,
        args.file_prefix,
        args.batch_size,
    )


if __name__ == "__main__":
    main()
    
