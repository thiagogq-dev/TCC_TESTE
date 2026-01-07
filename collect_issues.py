import requests
import json
import os
import time
import dotenv

from utils.queries import REPO_CLOSED_ISSUES_AND_CLOSED_EVENTS_QUERY
from utils.logger_config import setup_loggers, log_message
from utils.utils import is_commit_valid, get_commit_date, get_commit_that_references_pr, get_commit_that_references_issue

dotenv.load_dotenv()

setup_loggers()

API_TOKENS = [v for k, v in os.environ.items() if k.startswith("API_TOKEN_") and v]

if not API_TOKENS:
    log_message("Nenhum token de API encontrado nas variáveis de ambiente.", "error")
    exit(1)

token_index = 0
graph_ql_url = os.getenv('GRAPHQL_URL')

if not graph_ql_url:
    graph_ql_url = "https://api.github.com/graphql"

after_cursor = None

repo_name = os.getenv('REPO_NAME')
repo_owner = os.getenv('REPO_OWNER')

query = {
    "query": REPO_CLOSED_ISSUES_AND_CLOSED_EVENTS_QUERY,
    "variables": {
        "owner": repo_owner,
        "name": repo_name,
        "after": after_cursor
    }
}

def get_headers():
    return {
        'Authorization': f'token {API_TOKENS[token_index]}'
    }

def switch_token():
    global token_index
    token_index = (token_index + 1) % len(API_TOKENS)
    log_message(f"Trocando token. Novo index: {token_index}", "info")

def execute_query(query, headers):
    log_message(f"Executando query com token index: {token_index}", "info")
    response = requests.post(graph_ql_url, headers=headers, json=query)

    if response.status_code == 403:
        switch_token()
        headers = get_headers()
        response = requests.post(graph_ql_url, headers=headers, json=query)

    return response.json()

def resolve_fix_commit(issue, repo_owner, repo_name):
    node = issue["timelineItems"]["nodes"][0]["closer"]
    if not node:
        return None

    closer_type = node.get("__typename", "")

    if closer_type == "PullRequest":
        pr_number = node.get("number")
        merge_commit = node.get("mergeCommit", {}).get("oid") if node.get("mergeCommit") else None
        if merge_commit:
            valid, _ = is_commit_valid(f"./repos_dir/{repo_name}", merge_commit)
            if valid:
                return merge_commit
            
        fix_commit = get_commit_that_references_pr(f"{repo_owner}/{repo_name}", pr_number, get_headers())
        if fix_commit:
            valid, _ = is_commit_valid(f"./repos_dir/{repo_name}", fix_commit)
            if valid:
                return fix_commit

        issue_number = issue.get("number")
        fix_commit = get_commit_that_references_issue(f"{repo_owner}/{repo_name}", issue_number, get_headers())
        if fix_commit:
            valid, _ = is_commit_valid(f"./repos_dir/{repo_name}", fix_commit)
            if valid:
                return fix_commit
            
        last_commit = node.get("commits", {}).get("nodes", [{}])[-1].get("commit", {}).get("oid", None)
        return last_commit
    else:
        fix_commit = node.get("oid", None)
        if fix_commit:
            valid, _ = is_commit_valid(f"./repos_dir/{repo_name}", fix_commit)
            if valid:
                return fix_commit
            
        issue_number = issue.get("number")
        fix_commit = get_commit_that_references_issue(f"{repo_owner}/{repo_name}", issue_number, get_headers())
        return fix_commit

def check_data(data):
    if "errors" in data:
        return True
    return False

def check_rate_limit(headers):
    response = requests.post(graph_ql_url, headers=headers, json={"query": "{ rateLimit { remaining resetAt } }"})
    data = response.json()
    remaining = data.get("data", {}).get("rateLimit", {}).get("remaining", 0)

    if remaining == 0:
        switch_token()

def get_data():
    all_data = []
    after_cursor = None

    read_issues = 0

    while True:
        query["variables"]["after"] = after_cursor
        headers = get_headers()
        check_rate_limit(headers)
        data = execute_query(query, headers)

        if check_data(data):
            log_message(f"Erro na requisição: {json.dumps(data['errors'], indent=2)}", "error")
            break
        
        issues_data = data.get("data", {}).get("repository", {}).get("issues", {})
        page_info = issues_data.get("pageInfo", {})
        nodes = issues_data.get("nodes", [])

        for issue in nodes:
            log_message(f"Lendo issue {read_issues + 1} de {issues_data.get('totalCount', 0)}", "info")
            read_issues += 1
            if issue["timelineItems"]["nodes"] and issue["timelineItems"]["nodes"][0]["closer"] is not None:
                issue_number = issue.get("number", "N/A")
                issue_title = issue.get("title", "N/A")
                issue_url = issue.get("url", "N/A")
                issue_author = issue.get("author", {}).get("login", "N/A") if issue.get("author") else "N/A"
                issue_creation_date = issue.get("createdAt", "N/A")
                issue_closure_date = issue.get("closedAt", "N/A")
                closed_by = issue["timelineItems"]["nodes"][0]["closer"].get("__typename", "N/A")
                closer_url = issue["timelineItems"]["nodes"][0]["closer"].get("url", "N/A")

                fix_commit = resolve_fix_commit(issue, repo_owner, repo_name)
                valid, status = is_commit_valid(f"./repos_dir/{repo_name}", fix_commit)
                if not valid:
                    log_message(f"Commit {fix_commit} da issue #{issue_number} é INVÁLIDO - {status}. Pulando...", "warning")
                    continue

                issue_data = {
                    "repo_name": repo_name,
                    "repo_url": f"https://github.com/{repo_owner}/{repo_name}",
                    "issue_number": issue_number,
                    "issue_title": issue_title,
                    "issue_url": issue_url,
                    "issue_author": issue_author,
                    "issue_creation_date": issue_creation_date,
                    "issue_closure_date": issue_closure_date,
                    "closed_by": closed_by,
                    "closer_url": closer_url,
                    "fix_commit_hash": fix_commit
                }

                all_data.append(issue_data)

        if not page_info.get("hasNextPage"):
            break

        after_cursor = page_info.get("endCursor")

        time.sleep(2)  # To avoid hitting rate limits

    log_message(f"Total issues fetched: {len(all_data)}", "info")
    return all_data

if __name__ == "__main__":
    data = get_data()
    if not os.path.exists("data"):
        os.makedirs("data")
    with open("data/issues.json", "w") as f:
        json.dump(data, f, indent=2)

    get_commit_date("data/issues.json", repo_name)