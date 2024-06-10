import subprocess
import json

def match_bics(bics, bics2):
    matched = []

    for bic in bics:
       if bic in bics2:
           matched.append(bic)

    return matched

# with open("bug_fix_commits/bics_copy.json") as f:
#     data = json.load(f)

#     for d in data:
#         bics = data["inducing_commit_hash_pyszz"]
#         bics2 = data["inducing_commit_hash_pd"]
#         d["matched"] = match_bics(bics, bics2)
#         matched = match_bics(bics, bics2)
#         print(matched)


def format(filename):
    with open(filename, 'r') as f:
        data = json.load(f)

    formatted_data = []
    for item in data:  
        if "inducing_commit_hash_pyszz" not in item:
            print(f"Skipping {item['repo_name']} - {item['issue_title']}")
            item["inducing_commit_hash_pyszz"] = "-"
        formatted_item = {
            "repo_name": item["repo_name"],
            "repo_url": item["repo_url"],
            "Issue Title": item["issue_title"],
            "Issue Created By": item["issue_created_by"],
            "Issue Number": item["issue_number"],
            "Issue URL": item["issue_html_url"],
            "Issue Creation Date": item["issue_created_at"],
            "Issue Closing Date": item["issue_closed_at"],
            "PR Title": item["pr_title"],
            "PR Created By": item["pr_created_by"],
            "PR Number": item["pr_number"],
            "PR URL": item["pr_html_url"],
            "PR Created At": item["pr_created_at"],
            "PR Merged At": item["pr_merged_at"],
            "PR Last Commit SHA": item["pr_last_commit_sha"],
            "fix_commit_hash": item["fix_commit_hash"],
            "inducing_commit_hash_pyszz": item["inducing_commit_hash_pyszz"]
        }

        formatted_data.append(formatted_item)

    with open(filename, 'w') as f:
        json.dump(formatted_data, f, indent=4)

def remove_null_prs(json_file):
    check_pr_fields = [
        "pr_title",
        "pr_created_at",
        "pr_merged_at",
        "pr_html_url",
        "pr_number",
        "fix_commit_hash"
    ]   

    with open(json_file) as f:
        data = json.load(f)
        to_remove = []
        for d in data:
            if any(d[field] is None for field in check_pr_fields):
                to_remove.append(d)

        for d in to_remove:
            data.remove(d)
            
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

def remove_empty_bug_hashs(json_file):
    with open(json_file) as f:
        data = json.load(f)
        to_remove = []
        for d in data:
            if d["inducing_commit_hash_pyszz"] == [] and d["inducing_commit_hash_pd"] == []:
                to_remove.append(d)

        for d in to_remove:
            data.remove(d)
            
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)


def commit_exists(repo_path, commit_hash):
    try:
        result = subprocess.run(
            ['git', 'cat-file', '-t', commit_hash],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout.strip() == 'commit':
            return True
        else:
            return False
    except Exception as e:
        print(f"Erro ao verificar o commit: {e}")
        return False
    
def remove_non_existing_commits(filename):
    with open(filename) as f:
        data = json.load(f)

    new_data = [item for item in data if item["inducing_commit_hash_pyszz"] != "-"]        

    with open(filename, 'w') as f:
        json.dump(new_data, f, indent=4)

