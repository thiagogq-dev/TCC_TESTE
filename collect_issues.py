import requests
import json
import os
import time
from datetime import datetime, timedelta
import dotenv
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.queries import (
    REPO_CLOSED_ISSUES_AND_CLOSED_EVENTS_QUERY, 
    REPO_CREATION_DATE_QUERY
)
from utils.logger_config import setup_loggers, log_message
from utils.utils import is_commit_valid, get_commit_that_references_pr, get_commit_that_references_issue

dotenv.load_dotenv()
setup_loggers()

API_TOKENS = [v for k, v in os.environ.items() if k.startswith("API_TOKEN_") and v]

END_DATE_STR = "2026-05-13"  
OUTPUT_DIR = "teste_output"
repo_name = os.getenv('REPO_NAME')
repo_owner = os.getenv('REPO_OWNER')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"{repo_name}.json")

if not API_TOKENS:
    log_message("Nenhum token de API encontrado nas variáveis de ambiente.", "error")
    exit(1)

token_index = 0
graph_ql_url = os.getenv('GRAPHQL_URL', "https://api.github.com/graphql")

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
    return {'Authorization': f'token {API_TOKENS[token_index]}'}

def switch_token():
    global token_index
    token_index = (token_index + 1) % len(API_TOKENS)
    log_message(f"Trocando token. Novo index: {token_index}", "info")

def execute_query(query_payload, headers):
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            response = session.post(graph_ql_url, headers=headers, json=query_payload, timeout=30)
            if response.status_code == 403:
                log_message(f"Status 403 recebido. Trocando token e tentando novamente (tentativa {attempt}).", "warning")
                switch_token()
                headers = get_headers()
                continue
            return response.json()
        except requests.exceptions.RequestException as e:
            log_message(f"Erro de requisição na tentativa {attempt}/{max_attempts}: {e}", "warning")
            switch_token()
            headers = get_headers()
            time.sleep(min(60, 2 ** attempt))
    return {"errors": [{"message": "Max retries exceeded"}]}

def check_rate_limit(headers):
    try:
        response = session.post(graph_ql_url, headers=headers, json={"query": "{ rateLimit { remaining } }"}, timeout=10)
        data = response.json()
        remaining = data.get("data", {}).get("rateLimit", {}).get("remaining", 0)
        if remaining == 0:
            switch_token()
    except Exception as e:
        log_message(f"Erro ao checar rate limit: {e}", "warning")
        switch_token()

def get_repo_creation_date(owner, name):
    payload = {
        "query": REPO_CREATION_DATE_QUERY,
        "variables": {"owner": owner, "name": name}
    }
    headers = get_headers()
    data = execute_query(payload, headers)
    
    if "errors" in data or not data.get("data", {}).get("repository"):
        log_message("Não foi possível obter a data de criação do repositório. Usando fallback padrão 2014-01-01.", "warning")
        return "2014-01-01"
        
    creation_date_str = data["data"]["repository"]["createdAt"][:10]
    log_message(f"Data de criação do repositório identificada: {creation_date_str}", "info")
    return creation_date_str

def generate_date_intervals(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    
    intervals = []
    current_start = start_date
    
    while current_start <= end_date:
        # Fatias de 180 dias garantem não estourar o teto de 1000 itens por busca do GitHub
        current_end = current_start + timedelta(days=180)
        if current_end > end_date:
            current_end = end_date
            
        intervals.append((current_start.isoformat(), current_end.isoformat()))
        current_start = current_end + timedelta(days=1)
        
    return intervals
    

def resolve_fix_commit(issue, repo_owner, repo_name):
    repo_path = f"./repos_dir/{repo_name}"
    issue_number = issue.get("number")
    
    try:
        nodes = issue["timelineItems"]["nodes"]
        node = nodes[0].get("closer") if (nodes and nodes[0]) else None
    except (KeyError, IndexError):
        node = None
        
    if node:
        closer_type = node.get("__typename", "")

        if closer_type == "PullRequest":
            pr_number = node.get("number")
            merge_commit = node.get("mergeCommit", {}).get("oid") if node.get("mergeCommit") else None
            if merge_commit:
                valid, _ = is_commit_valid(repo_path, merge_commit)
                if valid:
                    return merge_commit
                
            fix_commit = get_commit_that_references_pr(f"{repo_owner}/{repo_name}", pr_number, get_headers())
            if fix_commit:
                valid, _ = is_commit_valid(repo_path, fix_commit)
                if valid:
                    return fix_commit
        else:
            fix_commit = node.get("oid")
            if fix_commit:
                valid, _ = is_commit_valid(repo_path, fix_commit)
                if valid:
                    return fix_commit
            
        fix_commit = get_commit_that_references_issue(f"{repo_owner}/{repo_name}", issue_number, get_headers())
        if fix_commit:
            valid, _ = is_commit_valid(repo_path, fix_commit)
            if valid:
                return fix_commit
        
    return None

def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_existing_data():
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_progress(all_data):
    _ensure_output_dir()
    try:
        all_data_sorted = sorted(all_data, key=lambda item: item.get("earliest_issue_date", ""))
        with open(OUTPUT_FILE, "w") as f:
            json.dump(all_data_sorted, f, indent=2)
    except Exception as e:
        log_message(f"Erro ao salvar arquivo final: {e}", "error")

def get_data():
    _ensure_output_dir()
    all_data = load_existing_data()
    
    repo_start_date = get_repo_creation_date(repo_owner, repo_name)
    initial_intervals = generate_date_intervals(repo_start_date, END_DATE_STR)
    
    # Tratamos os intervalos como uma Fila (Queue) para permitir subdivisões dinâmicas
    interval_queue = initial_intervals[:]
    
    log_message(f"Iniciando varredura segmentada. Fila inicial: {len(interval_queue)} intervalos.", "info")

    while interval_queue:
        start_p, end_p = interval_queue.pop(0)
        log_message(f"Processando intervalo: {start_p} a {end_p}", "info")
        
        query_payload = {
            "query": REPO_CLOSED_ISSUES_AND_CLOSED_EVENTS_QUERY,
            "variables": {
                "queryString": f'repo:{repo_owner}/{repo_name} is:issue is:closed closed:{start_p}..{end_p} sort:created-asc',
                "first": 50,
                "after": None
            }
        }

        # --- 1. Primeira requisição para checar o volume (totalCount) ---
        headers = get_headers()
        check_rate_limit(headers)
        data = execute_query(query_payload, headers)

        if "errors" in data:
            print(f"\n[ERRO DA API GITHUB]: {json.dumps(data['errors'], indent=2)}")
            continue
            
        search_data = data.get("data", {}).get("search", {})
        total_count = search_data.get('issueCount', 0)

        # --- 2. Lógica de Divisão Dinâmica (Quebra de Intervalo) ---
        if total_count > 1000:
            log_message(f"Intervalo {start_p}..{end_p} possui {total_count} issues, excedendo o limite de 1000. Iniciando divisão...", "warning")
            # Converte as strings extraindo apenas a parte da data (YYYY-MM-DD)
            start_date = datetime.strptime(start_p[:10], "%Y-%m-%d").date()
            end_date = datetime.strptime(end_p[:10], "%Y-%m-%d").date()
            
            if start_date == end_date:
                # Ocorre apenas se mais de 1000 issues forem fechadas em um ÚNICO dia.
                # Se isso acontecer, seria necessário fatiar por horas (ex: T00:00:00Z..T11:59:59Z).
                # Como é um cenário raríssimo, apenas logamos o teto e coletamos os primeiros 1000.
                log_message(f"AVISO CRÍTICO: O dia {start_date} possui {total_count} issues. Limite de 1000 atingido para um único dia.", "error")
            else:
                log_message(f"Teto excedido ({total_count} issues em {start_p}..{end_p}). Dividindo intervalo pela metade...", "warning")
                
                # Acha a metade exata do intervalo de dias
                delta = (end_date - start_date) // 2
                mid_date = start_date + delta
                
                # Insere os dois novos pedaços no início da fila
                interval_queue.insert(0, ((mid_date + timedelta(days=1)).isoformat(), end_p))
                interval_queue.insert(0, (start_p, mid_date.isoformat()))
                
                # Pula a paginação atual e recomeça o loop com os intervalos menores
                continue 

        # --- 3. Processamento e Paginação Normal (<= 1000 itens) ---
        page_info = search_data.get("pageInfo", {})
        nodes = search_data.get("nodes", [])
        
        progress = tqdm(total=total_count, desc=f"Varrendo [{start_p} ate {end_p}]", unit="issue")
        
        while True:
            try:
                for issue in nodes:
                    if progress:
                        progress.update(1)
                    if not issue: continue

                    timeline_nodes = issue.get("timelineItems", {}).get("nodes", [])
                    if timeline_nodes and timeline_nodes[0]:
                        final_fix_commit = resolve_fix_commit(issue, repo_owner, repo_name)

                        if not final_fix_commit:
                            log_message(f"Nenhum commit válido encontrado para a issue #{issue.get('number')} de {repo_name}. Pulando...", "warning")
                            continue

                        all_data.append({
                            "repo_name": repo_name,
                            "issue_number": issue.get("number"),
                            "fix_commit_hash": final_fix_commit,
                            "earliest_issue_date": issue.get("createdAt"),
                        })

                if not page_info.get("hasNextPage") or not page_info.get("endCursor"):
                    break

                after_cursor = page_info.get("endCursor")
                time.sleep(1.2)
                
                # Prepara e executa a requisição da próxima página
                query_payload["variables"]["after"] = after_cursor
                headers = get_headers()
                check_rate_limit(headers)
                data = execute_query(query_payload, headers)
                
                search_data = data.get("data", {}).get("search", {})
                page_info = search_data.get("pageInfo", {})
                nodes = search_data.get("nodes", [])

            except KeyboardInterrupt:
                log_message("Interrupção manual detectada. Gravando dados consolidados antes de sair...", "info")
                if progress: progress.close()
                save_progress(all_data)
                return all_data

        if progress: 
            progress.close()
        save_progress(all_data)

    log_message(f"Varredura concluída com sucesso! Registros salvos em disco: {len(all_data)}", "info")
    return all_data

if __name__ == "__main__":
    get_data()