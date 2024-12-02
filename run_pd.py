import json
from pydriller import Git, Repository
from utils.utils import match_bics, remove_empty_bug_hashs, update_matched_v2
import sys
import os

def find_pd(json_file, repo):
    with open(json_file) as f:
        data = json.load(f)
        repo_dir_name = repo.split("/")[-1]
        for d in data:
            if d["repo_name"] == repo_dir_name:
                bics = pd_finder(d["fix_commit_hash"], repo)
                d["inducing_commit_hash_pd"] = bics
                if bics == "-":
                    d["matched"] = []
                else:
                    d["matched"] = match_bics(d["inducing_commit_hash_pyszz"], bics)

            d["matched"] = update_matched_v2(d["inducing_commit_hash_pyszz"], d["inducing_commit_hash_pd"], d["matched"])

            d.pop("inducing_commit_hash_pyszz", None)
            d.pop("inducing_commit_hash_pd", None)


    # os.makedirs("./json/final_processed", exist_ok=True)
    # file_name = json_file.split("/")[-1]    
    # with open(f"./json/final_processed/{file_name}", 'w') as f:
    #     json.dump(data, f, indent=4)
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

def pd_finder(fix_commit, repo):
    gr = Git(repo)
    try:
        commit = gr.get_commit(fix_commit)
    except Exception as e:
        print(f"Error: {e}")
        return "-"
    # commit = gr.get_commit(fix_commit)
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

    # remove_empty_bug_hashs(json_file)