import json
from PRAnalizer import PRAnalizer
from pydriller import Repository

repo_url = "../repos_dir/jabref"

allowed_extensions = {
    'py': 'Python',
    'java': 'JAVA'
}

def check_test_changes(tests):
    test_changes = tests['removed'] + tests['added'] + tests['others']
    if test_changes > 0:
        return "Yes"
    return "No"

def run_pr_analizer(commit_sha):
    files_with_test = 0
    real_code_files = 0
    
    for commit in Repository(repo_url, single=commit_sha).traverse_commits():
        for modified_file in commit.modified_files:
            if modified_file is None:
               continue
            file_extension = modified_file.filename.split(".")[-1]
            print(file_extension)
            if file_extension not in allowed_extensions:
                continue
            real_code_files += 1
            language = allowed_extensions.get(file_extension)
            analizer = PRAnalizer(language)
            dadosDoPR  = analizer.retornaEstrutura();
            diff = modified_file.diff.split("\n")
            for line in diff:
                if analizer.checkIfModifier(line.strip()):
                     result = analizer.verify(line.strip())
                     modifierType = analizer.checkModifierType(line.strip())
                     dadosDoPR[result][modifierType] += 1
                     dadosDoPR['all'][modifierType] += 1

            if check_test_changes(dadosDoPR['tests']) == "Yes":
                files_with_test += 1

    return files_with_test, real_code_files


def process_file(file_path):
    with open(file_path) as f:
        data = json.load(f)
        for record in data:
            fix = record["fix_commit_hash"]
            files_with_test, real_code_files = run_pr_analizer(fix)
            record["files_with_test"] = files_with_test
            record["has_tests"] = "Yes" if files_with_test > 0 else "No"
            record["real_code_files"] = real_code_files

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

process_file("../data/issues.json")