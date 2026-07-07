import requests
import json
import os
import time
from datetime import datetime
import dotenv
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.queries import REPO_CLOSED_ISSUES_AND_CLOSED_EVENTS_QUERY
from utils.logger_config import setup_loggers, log_message
from utils.utils import is_commit_valid, get_commit_that_references_pr, get_commit_that_references_issue, split_json_file

dotenv.load_dotenv()

setup_loggers()

repo_name = os.getenv('REPO_NAME')
repo_owner = os.getenv('REPO_OWNER')

API_TOKENS = [v for k, v in os.environ.items() if k.startswith("API_TOKEN_") and v]
OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"{repo_name}.json")
CLOSED_UNTIL = "2026-05-13"
GRAPHQL_URL="https://api.github.com/graphql"

if not API_TOKENS:
    log_message("Nenhum token de API encontrado nas variáveis de ambiente.", "error")
    exit(1)

token_index = 0

try:
    closed_until_date = datetime.strptime(CLOSED_UNTIL, "%Y-%m-%d").date()
except ValueError:
    log_message(
        f"Data inválida em CLOSED_UNTIL: {CLOSED_UNTIL}. Use o formato YYYY-MM-DD.",
        "error"
    )
    exit(1)

query = {
    "query": REPO_CLOSED_ISSUES_AND_CLOSED_EVENTS_QUERY,
    "variables": {
        "owner": repo_owner,
        "name": repo_name,
        "after": None
    }
}

# Configure a session with retries and backoff to handle transient network errors
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=frozenset(["GET", "POST"])
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)

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
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            response = session.post(GRAPHQL_URL, headers=headers, json=query, timeout=30)

            if response.status_code == 403:
                log_message(f"Status 403 received. Switching token and retrying (attempt {attempt}).", "warning")
                switch_token()
                headers = get_headers()
                continue

            return response.json()

        except requests.exceptions.RequestException as e:
            log_message(f"Request error on attempt {attempt}/{max_attempts}: {e}", "warning")
            switch_token()
            headers = get_headers()
            # exponential backoff
            sleep_time = min(60, 2 ** attempt)
            time.sleep(sleep_time)

    log_message("Máximo de tentativas atingido ao executar a query.", "error")
    return {"errors": [{"message": "Max retries exceeded"}]}

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
    else:
        fix_commit = node.get("oid", None)
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
            
    return None

def check_data(data):
    if "errors" in data:
        return True
    return False

def check_rate_limit(headers):
    try:
        response = session.post(GRAPHQL_URL, headers=headers, json={"query": "{ rateLimit { remaining resetAt } }"}, timeout=10)
        data = response.json()
        remaining = data.get("data", {}).get("rateLimit", {}).get("remaining", 0)

        if remaining == 0:
            switch_token()
    except requests.exceptions.RequestException as e:
        log_message(f"Erro ao checar rate limit: {e}", "warning")
        switch_token()

def _ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def save_progress(all_data, after_cursor, total_count, read_issues):
    _ensure_output_dir()
    try:
        with open(OUTPUT_FILE, "w") as f:
            json.dump(all_data, f, indent=2)
        log_message(f" ({repo_name}) Progresso salvo. after={after_cursor} total_count={total_count} read_issues={read_issues}", "info")
    except Exception as e:
        log_message(f" ({repo_name}) Erro ao salvar progresso: {e} - ", "error")

    return None

def get_data():
    _ensure_output_dir()

    # restore previous data if exists
    all_data = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r") as f:
                all_data = json.load(f)
        except Exception:
            all_data = []

    after_cursor = os.getenv('START_CURSOR') or None
    read_issues = len(all_data)
    total_count = None
    progress = None

    while True:
        try:
            query["variables"]["after"] = after_cursor
            headers = get_headers()
            check_rate_limit(headers)
            data = execute_query(query, headers)

            if check_data(data):
                log_message(f"Erro na requisição para {repo_name}: {json.dumps(data['errors'], indent=2)}", "error")
                break
            
            issues_data = data.get("data", {}).get("repository", {}).get("issues", {})
            page_info = issues_data.get("pageInfo", {})
            nodes = issues_data.get("nodes", [])

            if total_count is None:
                total_count = issues_data.get('totalCount', 0)
                if tqdm:
                    progress = tqdm(total=total_count, desc="Processando issues", unit="issue")
                    if read_issues:
                        progress.update(read_issues)

            for issue in nodes:
                if progress:
                    progress.update(1)
                else:
                    log_message(f"Lendo issue {read_issues + 1} de {issues_data.get('totalCount', 0)} | {repo_name}", "info")
                read_issues += 1

                closed_at = issue.get("closedAt")
                if closed_until_date and closed_at:
                    issue_closed_date = datetime.strptime(closed_at[:10], "%Y-%m-%d").date()
                    if issue_closed_date > closed_until_date:
                        log_message(f"Issue #{issue.get('number')} de {repo_name} fechada em {issue_closed_date} é posterior a {closed_until_date}. Pulando...", "info")
                        continue

                if issue["timelineItems"]["nodes"] and issue["timelineItems"]["nodes"][0]["closer"] is not None:
                    issue_number = issue.get("number", "N/A")

                    final_fix_commit = resolve_fix_commit(issue, repo_owner, repo_name)
                    if not final_fix_commit:
                        log_message(f"Nenhum commit válido encontrado para a issue #{issue_number} de {repo_name}. Pulando...", "warning")
                        continue

                    issue_data = {
                        "repo_name": repo_name,
                        "fix_commit_hash": final_fix_commit,
                        "earliest_issue_date": issue.get("createdAt"),
                    }

                    all_data.append(issue_data)

            if not page_info.get("hasNextPage"):
                save_progress(all_data, None, total_count, read_issues)
                break

            after_cursor = page_info.get("endCursor")

            save_progress(all_data, after_cursor, total_count, read_issues)

            time.sleep(2)  # To avoid hitting rate limits

        except KeyboardInterrupt:
            log_message("Interrompido pelo usuário (Ctrl+C). Salvando progresso...", "info")
            save_progress(all_data, after_cursor, total_count, read_issues)
            if progress:
                progress.close()
            return all_data

    log_message(f"Total issues fetched from {repo_name}: {len(all_data)}", "info")
    if progress:
        progress.close()

    return all_data

if __name__ == "__main__":
    data = get_data()
    _ensure_output_dir()
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

    # split_json_file(data, OUTPUT_DIR, f"{repo_name}", max_items_per_file=50)