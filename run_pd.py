import json
from pydriller import Git, Repository
from utils.utils import match_bics, remove_empty_bug_hashs
import sys

def find_pd(json_file, repo):
    with open(json_file) as f:
        data = json.load(f)
        repo_dir_name = repo.split("/")[-1]
        for d in data:
            if d["repo_name"] == repo_dir_name:
                bics = pd_finder(d["fix_commit_hash"], repo)
                d["inducing_commit_hash_pd"] = bics
                d["matched"] = match_bics(d["inducing_commit_hash_pyszz"], bics)

    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

def pd_finder(fix_commit, repo):
    gr = Git(repo)
    commit = gr.get_commit(fix_commit)
    buggy_commits = gr.get_commits_last_modified_lines(commit)

    only_hash = []

    for key, value in buggy_commits.items():
        for val in value:
            only_hash.append(val)

    only_hash = list(set(only_hash))

    return only_hash

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_pd.py <json_file>")
        sys.exit(1)

    json_file = sys.argv[1]

    with open("repos_name.txt") as f:
        repos = f.readlines()
        repos = [x.strip() for x in repos]

        for repo in repos:
            repo_name = repo.split("/")[1]
            find_pd(json_file, f"repos_dir/{repo_name}")

    remove_empty_bug_hashs(json_file)