from pydriller import Git, Repository
import json
import os

def commit_data(commit_type, repo, commit_hash1, commit_hash2, folder_path):

    if commit_type == "fix":
        for commit in Repository(repo, single=commit_hash1).traverse_commits():

            if not os.path.exists(f"{folder_path}/{commit_type}/{commit_hash1}"):
                os.makedirs(f"{folder_path}/{commit_type}/{commit_hash1}")

            with open(f"{folder_path}/{commit_type}/{commit_hash1}/data.txt", "w") as f:
                f.write(f"Author: {commit.author.name} - {commit.author.email}\n")
                f.write(f"Message: {commit.msg}\n\n")
                f.write(f"Commit date: {commit.committer_date}\n")

                mod_names = [mod.filename for mod in commit.modified_files]
                
                f.write(f"Modified files: {mod_names}\n")
                f.write(f"Number of deleted lines: {commit.deletions}\n")
                f.write(f"Number of added lines: {commit.insertions}\n")
                f.write(f"Number of modified lines: {commit.lines}\n")
                f.write(f"Number of modified files: {commit.files}\n")

                for mf in commit.modified_files:
                    with open(f"{folder_path}/{commit_type}/{commit_hash1}/{mf.filename}.txt", "w") as f:
                        f.write(f"Change type: {mf.change_type}\n\n")
                        f.write(f"Diff:\n {mf.diff}\n\n")
                        f.write(f"Source code:\n {mf.source_code}\n\n")
                        f.write(f"Source code before:\n {mf.source_code_before}\n\n")
    else:   

        if commit_hash1 != []:
            for commit in Repository(repo, only_commits=commit_hash1).traverse_commits():

                if not os.path.exists(f"{folder_path}/{commit_type}/pydriller/{commit.hash}"):
                    os.makedirs(f"{folder_path}/{commit_type}/pydriller/{commit.hash}")

                with open(f"{folder_path}/{commit_type}/pydriller/{commit.hash}/data.txt", "w") as f:
                    f.write(f"Author: {commit.author.name} - {commit.author.email}\n")
                    f.write(f"Message: {commit.msg}\n\n")
                    f.write(f"Commit date: {commit.committer_date}\n")

                    mod_names = [mod.filename for mod in commit.modified_files]
                    
                    f.write(f"Modified files: {mod_names}\n")
                    f.write(f"Number of deleted lines: {commit.deletions}\n")
                    f.write(f"Number of added lines: {commit.insertions}\n")
                    f.write(f"Number of modified lines: {commit.lines}\n")
                    f.write(f"Number of modified files: {commit.files}\n")

                    for mf in commit.modified_files:
                        with open(f"{folder_path}/{commit_type}/pydriller/{commit.hash}/{mf.filename}.txt", "w") as f:
                            f.write(f"Change type: {mf.change_type}\n\n")
                            f.write(f"Diff:\n {mf.diff}\n\n")
                            f.write(f"Source code:\n {mf.source_code}\n\n")
                            f.write(f"Source code before:\n {mf.source_code_before}\n\n")

        if commit_hash2 != []:
            for commit in Repository(repo, only_commits=commit_hash2).traverse_commits():

                if not os.path.exists(f"{folder_path}/{commit_type}/pyszz/{commit.hash}"):
                    os.makedirs(f"{folder_path}/{commit_type}/pyszz/{commit.hash}")

                with open(f"{folder_path}/{commit_type}/pyszz/{commit.hash}/data.txt", "w") as f:
                    f.write(f"Author: {commit.author.name} - {commit.author.email}\n")
                    f.write(f"Message: {commit.msg}\n\n")
                    f.write(f"Commit date: {commit.committer_date}\n")

                    mod_names = [mod.filename for mod in commit.modified_files]
                    
                    f.write(f"Modified files: {mod_names}\n")
                    f.write(f"Number of deleted lines: {commit.deletions}\n")
                    f.write(f"Number of added lines: {commit.insertions}\n")
                    f.write(f"Number of modified lines: {commit.lines}\n")

                    for mf in commit.modified_files:
                        with open(f"{folder_path}/{commit_type}/pyszz/{commit.hash}/{mf.filename}.txt", "w") as f:
                            f.write(f"Change type: {mf.change_type}\n\n")
                            f.write(f"Diff:\n {mf.diff}\n\n")
                            f.write(f"Source code:\n {mf.source_code}\n\n")
                            f.write(f"Source code before:\n {mf.source_code_before}\n\n")

with open("bug_fix_commits/bics.json") as f:
    data = json.load(f)
    seen = 0
    for d in data:
        fix_commit = d["fix_commit_hash"]
        # bic_pyszz = d["inducing_commit_hash_pyszz"]
        # bic_pd= d["inducing_commit_hash_pd"]

        bic = d["matched"]

        if os.path.exists(f"{d['repo_name']}/{fix_commit}"):
            continue
        else:
            os.makedirs(f"{d['repo_name']}/{fix_commit}")

        commit_data("fix", "pyszz_v2/repos_dir/jabref", fix_commit, [], folder_path=f"{d['repo_name']}/{fix_commit}")
        commit_data("bic", "pyszz_v2/repos_dir/jabref", bic, [], folder_path=f"{d['repo_name']}/{fix_commit}")
