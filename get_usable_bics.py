from pathlib import Path
from typing import Any
from utils.utils import is_commit_valid, split_json_file
import argparse
import json
import re
import sys

def build_szz_data(repo_name: str, commit_hash: str, path_id: Any) -> dict:
    return {
        "repo_name": repo_name,
        "fix_commit_hash": commit_hash,
        "path_id": path_id,
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
        return None

    return build_szz_data(
        repo_name=repo_name,
        commit_hash=candidate_bic,
        path_id=entry.get("path_id"),
    )


def process_retry(entry: dict) -> dict:
    return build_szz_data(
        repo_name=entry["repo_name"],
        commit_hash=entry["fix_commit_hash"],
        path_id=entry.get("path_id"),
    )


def prepare_data(input_folder: str, first_actions_attempt: bool = False) -> list[dict]:
    if first_actions_attempt:
        print(
            "Primeira tentativa usando GitHub Actions para os BICs. "
            "Verificando merge commits..."
        )
    else:
        print(
            "Processamento anterior falhou no GitHub Actions "
            "(tempo ou memória). Reduzindo tamanho dos chunks..."
        )

    results: list[dict] = []

    for json_file in Path(input_folder).glob("*.json"):
        with json_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            if first_actions_attempt:
                result = process_first_attempt(entry)
            else:
                result = process_retry(entry)

            if result:
                results.append(result)

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
        "--input_folder",
        required=True,
        help="Folder containing input JSON files",
    )

    parser.add_argument(
        "--output_folder",
        required=True,
        help="Folder where output JSON files will be saved",
    )

    parser.add_argument(
        "--file_prefix",
        required=True,
        help="Prefix for output files",
    )

    parser.add_argument(
        "--batch_size",
        type=int,
        default=50,
        help="Number of entries per output file",
    )

    parser.add_argument(
        "--first_actions_attempt",
        action="store_true",
        help="Indicates first GitHub Actions attempt for BIC processing",
    )

    args = parser.parse_args()

    input_folder = Path(args.input_folder)
    first_actions_attempt = args.first_actions_attempt
    
    if not input_folder.exists():
        raise FileNotFoundError(
            f"Input folder '{input_folder}' does not exist."
        )
    
    if not first_actions_attempt and "out/v" in str(input_folder):
        print(
            f"Aviso: o input_folder '{input_folder}' parece ser uma pasta de versão. "
            "Certifique-se de que está usando a pasta correta para a primeira tentativa."
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

    data = prepare_data(
        input_folder=str(input_folder),
        first_actions_attempt=first_actions_attempt,
    )

    split_json_file(
        data,
        args.output_folder,
        args.file_prefix,
        args.batch_size,
    )


if __name__ == "__main__":
    main()
    
