import json
from PRAnalizer import PRAnalizer
import os
from pydriller import Repository

allowed_extensions = {
    'java': 'JAVA'
}

def check_test_changes(tests):
    test_changes = tests['removed'] + tests['added'] + tests['others']
    if test_changes > 0:
        return "Yes"
    return "No"

def analyze_diff(language, patch):
    analizer = PRAnalizer(language)
    dadosDoPR = analizer.retornaEstrutura()
    diff = patch.split("\n")

    for line in diff:
        stripped_line = line.strip() 
        if analizer.checkIfModifier(stripped_line):
            result = analizer.verify(stripped_line)
            modifier_type = analizer.checkModifierType(stripped_line)
            dadosDoPR[result][modifier_type] += 1
            dadosDoPR['all'][modifier_type] += 1

    has_test = check_test_changes(dadosDoPR['tests']) == "Yes"
    added_asserts = dadosDoPR['tests']['added']
    removed_asserts = dadosDoPR['tests']['removed']
    return has_test, added_asserts, removed_asserts


def analyze_files(files):
    files_with_test = 0
    real_code_files = 0
    added_asserts = 0
    removed_asserts = 0

    for file_item in files:
        if file_item is None:
            continue

        filename = getattr(file_item, "filename", None)
        if not filename or "." not in filename:
            continue

        file_extension = filename.split(".")[-1]
        if file_extension not in allowed_extensions:
            continue

        patch = getattr(file_item, "diff", None)
        if patch is None:
            continue

        real_code_files += 1
        language = allowed_extensions[file_extension]
        has_test, file_added_asserts, file_removed_asserts = analyze_diff(language, patch)

        if has_test:
            files_with_test += 1
        added_asserts += file_added_asserts
        removed_asserts += file_removed_asserts
    return files_with_test, real_code_files, added_asserts, removed_asserts

def run_pr_analizer(repo_name, commit_sha):
    repo_folder = repo_name.split("/")[-1]
    local_repo_path = f"../repos_dir/{repo_folder}"

    if os.path.isdir(local_repo_path):
        try:
            for commit in Repository(local_repo_path, single=commit_sha).traverse_commits():
                if commit.modified_files:
                    return analyze_files(commit.modified_files)
                break
        except Exception as error:
            print(f"Falha no PyDriller local para {repo_name} @ {commit_sha}: {error}. Fallback PyGithub.")

    return 0, 0, 0, 0

def save_json_atomic(file_path, data):
    temp_path = f"{file_path}.tmp"
    with open(temp_path, "w") as f:
        json.dump(data, f, indent=4)
    os.replace(temp_path, file_path)


def process_file(file_path):
    with open(file_path) as f:
        data = json.load(f)

    total = len(data)
    new_data = []
    for index, record in enumerate(data, start=1):
        fix = record["fix_commit_hash"]
        print(f"Processando {index}/{total}: {record['repo_name']} @ {fix}", flush=True)
        repo_name = record["repo_name"]
        files_with_test, real_code_files, added_asserts, removed_asserts = run_pr_analizer(repo_name, fix)

        if real_code_files == 0:
            print(f"Aviso: Nenhum arquivo de código real encontrado para {repo_name} @ {fix}. Pulando registro.")
            continue

        record["files_with_test"] = files_with_test
        record["has_asserts_changes"] = True if files_with_test > 0 else False
        record["real_code_files"] = real_code_files
        record["test_file_ratio"] = files_with_test / real_code_files if real_code_files > 0 else 0
        record["added_asserts"] = added_asserts
        record["removed_asserts"] = removed_asserts

        if files_with_test <= 0:
            record["asserts_changes_type"] = "None"
        else:
            record["asserts_changes_type"] = (
                "Added" if added_asserts > removed_asserts
                else "Removed" if removed_asserts > added_asserts
                else "Maintained"
            )

        new_data.append(record)
        save_json_atomic(file_path, new_data)
        print(f"[{index}/{total}] Registro salvo: {repo_name} @ {fix}", flush=True)

for file in os.listdir("../data"):
    if file.endswith(".json"):
        print(f"Processando arquivo: {file}")
        process_file(os.path.join("../data", file))