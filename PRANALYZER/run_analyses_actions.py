import json
from PRAnalizer import PRAnalizer
from github import Github, Auth
import os
import argparse
from pathlib import Path

github_token = os.getenv("GITHUB_TOKEN", "").strip()
if not github_token:
    raise RuntimeError("Defina a variável de ambiente GITHUB_TOKEN antes de executar o script.")

auth = Auth.Token(github_token)
g = Github(auth=auth)

allowed_extensions = {
    'java': 'JAVA'
}

def check_test_changes(tests):
    test_changes = tests['removed'] + tests['added'] + tests['others']
    if test_changes > 0:
        return "Yes"
    return "No"

def run_pr_analizer(repo_name, commit_sha):
    files_with_test = 0
    real_code_files = 0
    added_asserts = 0
    removed_asserts = 0


    repo = g.get_repo(repo_name)
    commit = repo.get_commit(commit_sha)
    files = list(commit.files)

    for file in files:
        if file.patch is None:
            continue
        file_extension = file.filename.split(".")[-1]
        if file_extension not in allowed_extensions:
            continue

        real_code_files += 1

        language = allowed_extensions.get(file_extension)
        analizer = PRAnalizer(language)
        dadosDoPR  = analizer.retornaEstrutura();
        diff = file.patch.split("\n")
        for line in diff:
            if analizer.checkIfModifier(line.strip()):
                    result = analizer.verify(line.strip())
                    modifierType = analizer.checkModifierType(line.strip())
                    dadosDoPR[result][modifierType] += 1
                    dadosDoPR['all'][modifierType] += 1

        if check_test_changes(dadosDoPR['tests']) == "Yes":
            files_with_test += 1

        added_asserts += dadosDoPR['tests']['added']
        removed_asserts += dadosDoPR['tests']['removed']

    return files_with_test, real_code_files, added_asserts, removed_asserts


def save_json_atomic(file_path, data):
    temp_path = f"{file_path}.tmp"
    with open(temp_path, "w") as f:
        json.dump(data, f, indent=4)
    os.replace(temp_path, file_path)


def process_file(file_path):
    with open(file_path) as f:
        data = json.load(f)
        total = len(data)
        for index, record in enumerate(data, start=1):
            if "files_with_test" in record:
                continue  # Pula registros já processados

            fix = record["fix_commit_hash"]
            repo_name = record["repo_name"]
            files_with_test, real_code_files, added_asserts, removed_asserts = run_pr_analizer(repo_name, fix)
            record["files_with_test"] = files_with_test
            record["has_tests"] = "Yes" if files_with_test > 0 else "No"
            record["real_code_files"] = real_code_files
            record["test_file_ratio"] = files_with_test / real_code_files if real_code_files > 0 else 0
            record["added_asserts"] = added_asserts
            record["removed_asserts"] = removed_asserts
            save_json_atomic(file_path, data)
            print(f"[{index}/{total}] Registro salvo: {repo_name} @ {fix}", flush=True)

def get_analysis_files(analysis_file=None):
    project_root = Path(__file__).resolve().parent.parent
    analysis_root = (project_root / "analysis").resolve()

    if analysis_file:
        target = (analysis_root / analysis_file).resolve()
        if not str(target).startswith(str(analysis_root)):
            raise ValueError("analysis_file deve estar dentro de analysis/")
    else:
        return sorted(analysis_root.glob("*.json"))

    if not target.exists() or not target.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado em analysis/: {analysis_file}")

    if target.suffix != ".json":
        raise ValueError("O arquivo alvo precisa ter extensão .json")

    return [target]


def main():
    parser = argparse.ArgumentParser(description="Executa análise de PRs em arquivos JSON")
    parser.add_argument(
        "--analysis-file",
        default="",
        help="Arquivo dentro de analysis/ (ex: spring_boot_merged.json)",
    )
    args = parser.parse_args()

    files = get_analysis_files(args.analysis_file.strip())
    for file_path in files:
        print(f"Processando arquivo: {file_path}")
        process_file(file_path)


if __name__ == "__main__":
    main()