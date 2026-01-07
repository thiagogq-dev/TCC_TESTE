from collections import defaultdict
import json
import requests
import glob
from pydriller import Git, Repository
from datetime import timedelta
from bisect import bisect_right
from utils.queries import COMMIT_REFERENCES_PR, COMMIT_REFERENCES_ISSUE

def get_commit_that_references_issue(repo_path, issue_number, headers):
    owner, name = repo_path.split("/")
    graphql_url = 'https://api.github.com/graphql'

    query = {
        "query": COMMIT_REFERENCES_ISSUE,
        "variables": {
            "owner": owner,
            "name": name,
            "issueNumber": issue_number
        }
    }
    response = requests.post(graphql_url, json=query, headers=headers)
    data = response.json()

    if 'data' in data and data['data']['repository']['issue']['timelineItems']['nodes'] != []:
        return data['data']['repository']['issue']['timelineItems']['nodes'][0]['commit']['oid']
    return None


def get_commit_that_references_pr(repo_path, pr_number, headers):
    owner, name = repo_path.split("/")
    graphql_url = 'https://api.github.com/graphql'

    query = {
        "query": COMMIT_REFERENCES_PR,
        "variables": {
            "owner": owner,
            "name": name,
            "prNumber": pr_number
        }
    }

    response = requests.post(graphql_url, json=query, headers=headers)
    data = response.json()

    if 'errors' in data:
        return None
    if 'data' in data and data['data']['repository']['pullRequest']['timelineItems']['nodes'] != []:
        commit_node = data['data']['repository']['pullRequest']['timelineItems']['nodes'][0]['commit']
        if commit_node:
            return commit_node['oid']
        # return data['data']['repository']['pullRequest']['timelineItems']['nodes'][0]['commit']['oid']
    return None

def get_commit_pr(repo_path, commit_hash, headers):
    url = f"https://api.github.com/repos/{repo_path}/commits/{commit_hash}/pulls"
    response = requests.get(url, headers=headers)
    data = response.json()

    prs = []

    for pr in data:
        if pr["state"] == "closed":
            prs.append({
                "merged_at": pr["merged_at"],
                "merge_commit_sha": pr["merge_commit_sha"]
            })

    if len(prs) == 0:
        return None
    
    pr = max(prs, key=lambda x: x["merged_at"]) 
    return pr["merge_commit_sha"]


def get_pr_that_mentions_issue(repo_path, issue_number, headers):
    owner, name = repo_path.split("/")
    graphql_url = 'https://api.github.com/graphql'

    query = f'''
    {{
        repository(name: "{name}", owner: "{owner}") {{
            issue(number: {issue_number}) {{
                timelineItems(itemTypes: MENTIONED_EVENT, last: 1) {{
                    nodes {{
                        ... on ReferencedEvent {{
                            subject {{
                                __typename
                                ... on PullRequest {{
                                    number
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}
    '''

    response = requests.post(graphql_url, json={'query': query}, headers=headers)
    data = response.json()
    return data["data"]["repository"]["issue"]["timelineItems"]["nodes"][0]["subject"]["number"]

def remove_duplicates(input_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    tam = len(data)
    seen = set()
    unique_data = []

    for item in data:
        identifier = json.dumps(item, sort_keys=True)
        if identifier not in seen:
            seen.add(identifier)
            unique_data.append(item)
    
    print(f'Removed {tam - len(unique_data)} duplicate items.')
    with open(input_file, 'w') as f:
        json.dump(unique_data, f, indent=4)


def is_empty_or_dash(value):
    if value == [] or value == "-":
        return True
    return False

def define_bic(rszz, pdszz):
    if not is_empty_or_dash(rszz):
       bic = rszz
    elif not is_empty_or_dash(pdszz):
        value = pdszz[0]
        bic = [value]
    else:
       bic = []

    return bic
    
def remove_non_existing_commits(filename):
    with open(filename) as f:
        data = json.load(f)

    new_data = [item for item in data if item["inducing_commit_hash_pyszz"] != "-"]        

    with open(filename, 'w') as f:
        json.dump(new_data, f, indent=4)


def split_json_file(input_file, output_prefix, max_items_per_file=10):
    with open(input_file, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("The input file does not contain a JSON list.")

    chunks = [data[i:i + max_items_per_file] for i in range(0, len(data), max_items_per_file)]

    for idx, chunk in enumerate(chunks):
        output_file = f"{output_prefix}_{idx + 1}.json"
        with open(output_file, 'w') as f:
            json.dump(chunk, f, indent=4)
        print(f"File {output_file} created with {len(chunk)} items.")
              
def merge_files(folder_path, output_path):
    json_files = glob.glob(folder_path + "/*.json")
    combined_data = []
    for file in json_files:
        with open(file, 'r') as f:
            data = json.load(f)
            print(f'Processing {file} with {len(data)} items')
            combined_data.extend(data)
    print(f'Combined data has {len(combined_data)} items')
    with open(output_path, 'w') as f:
        json.dump(combined_data, f, indent=4)

def group_file_by_fix(input_file, output_file = None):
    """
    Agrupa os registros de um arquivo JSON pelo hash do commit de correção (fix_commit_hash).
    Evita duplicatas de 'bic' para cada commit de correção.
    
    :param input_file: Caminho para o arquivo JSON de entrada.
    :param output_file: Caminho para o arquivo JSON de saída.
    """
    with open(input_file, "r") as f:
        data = json.load(f)

    grouped_data = {}

    for record in data:
        fix_hash = record["fix_commit_hash"]
        
        if fix_hash not in grouped_data:
            grouped_data[fix_hash] = record
            grouped_data[fix_hash]["bic"] = set(record["bic"])
        else:
            grouped_data[fix_hash]["bic"].update(record["bic"])

    result = [
        {**values, "bic": list(values["bic"])}
        for values in grouped_data.values()
    ]
    output_file = output_file or input_file 
    with open(output_file, "w") as f:
        json.dump(result, f, indent=4)

def get_commit_date(json_file, repo_name):
    """Adiciona a data do commit no cenário ideal para cada issue no arquivo JSON.
    
    Args:
        json_file (str): Caminho para o arquivo JSON contendo os dados das issues.
    """
    with open(json_file) as f:
        data = json.load(f)
        for d in data:
           commit_hash = d["fix_commit_hash"]
           for commit in Repository(f"repos_dir/{repo_name}", single=commit_hash).traverse_commits():
                new_date = commit.author_date + timedelta(seconds=60)
                d["best_scenario_issue_date"] = new_date.isoformat()  # Salva como string em ISO 8601

    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

def is_commit_valid(repo_path, commit_hash):
    """
    Verifica se o commit existe no repositório e não é um commit de merge.

    Args:
        repo_path (str): Caminho para o repositório local.
        commit_hash (str): Hash do commit a ser verificado.

    Returns:
        bool: True se o commit existe e não é um merge, False caso contrário.
    """
    gr = Git(repo_path)
    try:
        commit = gr.get_commit(commit_hash)
        if commit.merge:
            return False, "Commit é um merge"
    except Exception:
        return False, "Commit não encontrado"

    return True, "Commit válido"

def get_commit_data(commit_hash):
    for commit in Repository(path_to_repo="repos_dir/jabref", single=commit_hash).traverse_commits():        
        data = {
            "commit_author": commit.author.name,
            "committer": commit.committer.name,
            "commit_date": commit.author_date.isoformat(),
            "committer_date": commit.committer_date.isoformat(),
            "changed_files": commit.files,
            "deletions": commit.deletions,
            "insertions": commit.insertions,
            "lines": commit.lines,
            "dmm_unit_size": commit.dmm_unit_size,
            "dmm_unit_complexity": commit.dmm_unit_complexity,
            "dmm_unit_interfacing": commit.dmm_unit_interfacing
        }
        
        return data


# -----------------------------
# Shared helpers for contributor activity
# -----------------------------
def preload_commits_index(repo_path="repos_dir/jabref"):
    """Return two maps: commit_date and author_commits (sorted lists).

    commit_date: {commit_hash: datetime}
    author_commits: {author_name: [datetime, ...]}
    """
    commit_date = {}
    author_commits = defaultdict(list)

    try:
        for commit in Repository(repo_path).traverse_commits():
            commit_date[commit.hash] = commit.author_date
            author_commits[commit.author.name].append(commit.author_date)
    except Exception:
        # fallback: return empty maps if repo not available or pydriller missing
        return {}, defaultdict(list)

    for author in author_commits:
        author_commits[author].sort()

    return commit_date, author_commits


def get_commit_date_from_index(fix_commit, commit_date_map):
    """Return the date to use as 'fix_date' (one day before author_date) or None."""
    d = commit_date_map.get(fix_commit)
    if not d:
        return None
    return d - timedelta(days=1)


def get_contributor_activity_from_index(author, fix_date, author_commits_map):
    """Return number of commits by `author` up to `fix_date` (inclusive)."""
    if fix_date is None:
        return 0
    dates = author_commits_map.get(author, [])
    return bisect_right(dates, fix_date)