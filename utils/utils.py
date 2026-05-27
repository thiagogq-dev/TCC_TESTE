from collections import defaultdict
import json
import os
import requests
import glob
from pydriller import Git, Repository
from datetime import timedelta
from bisect import bisect_right
from utils.queries import COMMIT_REFERENCES_PR, COMMIT_REFERENCES_ISSUE

ACTIVITY_BUCKETS = ["0", "1-5", "6-20", "21-100", "100+"]

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
    try:
        response = requests.post(graphql_url, json=query, headers=headers)
        data = response.json()
    except Exception:
        return None

    # caminho conciso até nodes; usa listas/dicts vazios como fallback
    nodes = data.get('data', {}).get('repository', {}).get('issue', {}).get('timelineItems', {}).get('nodes') or []
    if not nodes:
        return None

    commit = nodes[0].get('commit') or {}
    return commit.get('oid')


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

def split_json_file(input_data, file_prefix, max_items_per_file=10, output_folder='data/'):
    if not isinstance(input_data, list):
        raise ValueError("The input data does not contain a JSON list.")

    chunks = [input_data[i:i + max_items_per_file] for i in range(0, len(input_data), max_items_per_file)]

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    for idx, chunk in enumerate(chunks):
        output_file = os.path.join(output_folder, f"{file_prefix}_{idx + 1}.json")
        with open(output_file, 'w') as f:
            json.dump(chunk, f, indent=4)
        print(f"File {output_file} created with {len(chunk)} items.")
              
def merge_files(folder_path, output_path):
    json_files = glob.glob(folder_path + "/**/*.json", recursive=True)
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

def get_commit_data(commit_hash, repo_name, commit_date_map, author_commits_map):
    has_test_files = False
    for commit in Repository(path_to_repo=f"repos_dir/{repo_name}", single=commit_hash).traverse_commits():    
        real_lines_changed = 0
        for mf in commit.modified_files:
            if mf.filename.endswith(".java"):
                real_lines_changed += mf.added_lines + mf.deleted_lines
                
            if "test" in mf.filename.lower() or (mf.new_path and "test" in mf.new_path.lower()) or (mf.old_path and "test" in mf.old_path.lower()):
                has_test_files = True

        # Calcula contributor_activity para o autor até a data do commit - 1 dia
        author = commit.author.name
        commit_date = commit.author_date
        contributor_activity = get_contributor_activity_from_index(author, commit_date - timedelta(days=1), author_commits_map)

        data = {
            "commit_author": author,
            "committer": commit.committer.name,
            "commit_date": commit_date.isoformat(),
            "committer_date": commit.committer_date.isoformat(),
            "changed_files": commit.files,
            "deletions": commit.deletions,
            "insertions": commit.insertions,
            "lines": commit.lines,
            "has_test_files": has_test_files,
            "real_lines_changed": real_lines_changed,
            "dmm_unit_size": commit.dmm_unit_size,
            "dmm_unit_complexity": commit.dmm_unit_complexity,
            "dmm_unit_interfacing": commit.dmm_unit_interfacing,
            "contributor_activity": contributor_activity
        }
        return data


def preload_commits_index(repo_path):
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

def safe_float(value):
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None
    
def load_data(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)
    
class Reporter:
    def __init__(self, path):
        self.path = path

    def write(self, text):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(text + "\n")

def get_activity_bucket(activity):
    if activity is None: return None
    if activity == 0:    return "0"
    if activity <= 5:    return "1-5"
    if activity <= 20:   return "6-20"
    if activity <= 100:  return "21-100"
    return "100+"