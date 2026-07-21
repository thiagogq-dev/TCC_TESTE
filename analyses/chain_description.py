import json
import os
import numpy as np
from collections import defaultdict, deque
import matplotlib.pyplot as plt
from utils.utils import load_data, preprocess_raw_data
import openpyxl

OUTPUT_FOLDER = "./results/chain_description"
INPUT_FILE = "./dataset/4-metricas/pair_bic_fix"

def build_commit_to_fix(data):
    """
    Constrói um dicionário que mapeia cada commit para a lista de commits que o corrigem (fixed_by).
    Args:
        data (list): Lista de registros de commits.
    Returns:
        defaultdict(list): Dicionário onde a chave é o commit e o valor é uma lista
    """
    commit_to_fix = defaultdict(list)
    for record in data:
        commit = record.get("commit")
        fixed_by = record.get("fixed_by") or []
        commit_to_fix[commit].extend(fixed_by)
    return commit_to_fix

def bfs_unique(graph_dict, start_commit):
    """
    Percorre o grafo via BFS garantindo que cada commit seja visitado uma vez.
    Args:
        graph_dict (dict): Dicionário representando o grafo de commits.
        start_commit (str): Commit inicial para a travessia.
    Returns:
        dict: Dicionário com commits visitados e suas respectivas profundidades.
    """
    visited = {}
    queue = deque([(start_commit, 1)])
    while queue:
        commit, depth = queue.popleft()
        if commit in visited:
            continue
        visited[commit] = depth
        for child in graph_dict.get(commit, []):
            if child not in visited:
                queue.append((child, depth + 1))
    return visited

def compute_global_all_depths(graph_dict):
    """
    Calcula TODAS as profundidades absolutas em que um commit aparece,
    partindo das raízes reais do repositório (nível 1).
    Args:
        graph_dict (dict): Dicionário representando o grafo de commits.
    Returns:
        dict: Dicionário onde a chave é o commit e o valor é um conjunto de profundidades em que ele aparece.
    """
    if not graph_dict:
        return {}

    indegree = defaultdict(int)
    all_nodes = set()
    for parent, children in graph_dict.items():
        all_nodes.add(parent)
        for child in children:
            if child:
                all_nodes.add(child)
                indegree[child] += 1

    # Começamos APENAS com as raízes absolutas (não corrigem ninguém) -> Nível 1
    queue = deque([(node, 1) for node in all_nodes if indegree[node] == 0])
    
    depths = defaultdict(set)

    while queue:
        u, current_depth = queue.popleft()
        depths[u].add(current_depth)
        
        for v in graph_dict.get(u, []):
            if v is None: continue
            if (current_depth + 1) not in depths[v]:
                queue.append((v, current_depth + 1))

    return depths

# ==========================================================
# 1 - PROPAGAÇÃO GERAL
# ==========================================================

def aggregate_propagation(graph_dict):
    """
    Agrega métricas de propagação para todos os BICs no grafo.
    Args:
        graph_dict (dict): Dicionário representando o grafo de commits.
    Returns:
        tuple: Dois dicionários (overall, with_fix) com contagens de profundidade
    """
    overall = defaultdict(int)
    with_fix = defaultdict(int)
    all_depths_map = compute_global_all_depths(graph_dict)

    for commit, depths_set in all_depths_map.items():
        for depth in depths_set:
            overall[depth] += 1
            if graph_dict.get(commit):
                with_fix[depth] += 1

    return overall, with_fix

# ==========================================================
# 2 - ANÁLISE DE PROFUNDIDADE MÁXIMA
# ==========================================================

def analyze_max_chain_depth(graph_dict):
    """
    Analisa a profundidade máxima das cadeias de commits no grafo,
    tratando cada cascata como uma única entidade.
    Args:
        graph_dict (dict): Dicionário representando o grafo de commits.
    Returns:
        dict: Dicionário com métricas de profundidade máxima.
    """
    # 1. Encontrar o grau de entrada (indegree) para saber quem é raiz
    indegree = defaultdict(int)
    for parent, children in graph_dict.items():
        for child in children:
            if child:
                indegree[child] += 1
                
    max_chain_lengths = []
    all_chain_lengths = []
    
    # 2. Iterar apenas sobre os commits que são raízes e possuem filhos
    for commit in graph_dict:
        is_root = (indegree[commit] == 0)
        has_fixes = len(graph_dict.get(commit, [])) > 0
        
        if is_root and has_fixes:
            # Encontra todos os nós desta cadeia usando a função bfs_unique que já existe no seu código
            visited = bfs_unique(graph_dict, commit)
                
            # O tamanho da cadeia é a profundidade máxima alcançada partindo desta raiz
            max_depth = max(visited.values())
            max_chain_lengths.append(max_depth)

            for visited_commit, depth in visited.items(): # Adiciona todas as profundidades absolutas em que cada commit aparece
                if not graph_dict.get(visited_commit):  # Se não tem filhos, é uma folha
                    all_chain_lengths.append(depth)
            
    if not max_chain_lengths:
        return {}
        
    # 3. Calcula as métricas usando apenas o tamanho final de cada cadeia
    longest_chain = max(max_chain_lengths)
    avg_max_depth = np.mean(max_chain_lengths)
    avg_all_depth = np.mean(all_chain_lengths)

    # pct_chains_gt_5 = sum(1 for d in max_chain_lengths if d > 5) / len(max_chain_lengths) * 100
    pct_chains_gt_5 = sum(1 for d in all_chain_lengths if d > 5) / len(all_chain_lengths) * 100
    
    return {
        "longest_chain": longest_chain,
        "avg_max_depth": avg_max_depth,
        "avg_all_depth": avg_all_depth,
        "pct_chains_gt_5": pct_chains_gt_5
    }

# ==========================================================
# 3 - ANÁLISE DE BIFURCAÇÃO
# ==========================================================

def analyze_bifurcation_rate(graph_dict):
    """
    Analisa a taxa de bifurcação no grafo, ou seja, quantos commits têm múltiplos filhos (fixes).
    Args:
        graph_dict (dict): Dicionário representando o grafo de commits.
    Returns:
        dict: Dicionário com métricas de bifurcação.
    """
    children_counts = [len(fixes) for fixes in graph_dict.values() if fixes]
    
    if not children_counts:
        return {}
    
    avg_fixes = np.mean(children_counts)
    pct_multiple_fixes = sum(1 for c in children_counts if c > 1) / len(children_counts) * 100
    max_fixes = max(children_counts)
    
    return {
        "avg_fixes_per_bug": avg_fixes,
        "pct_multiple_fixes": pct_multiple_fixes,
        "max_fixes": max_fixes
    }

# ==========================================================
# 4 - ANÁLISE DE VELOCIDADE DE CORREÇÃO
# ==========================================================

def analyze_fix_velocity(data):
    """
    Analisa a velocidade de correção dos bugs, calculando métricas como mediana de dias para correção, percentil 95 e porcentagem de bugs corrigidos em até 7 dias.
    Args:
        data (list): Lista de registros de commits.
    Returns:
        dict: Dicionário com métricas de velocidade de correção.
    """
    from datetime import datetime
    commit_to_date = {}
    for record in data:
        commit = record.get("commit")
        commit_date_str = record.get("commit_date")
        
        if commit and commit_date_str:
            try:
                if isinstance(commit_date_str, str) and len(commit_date_str) >= 10:
                    commit_to_date[commit] = datetime.fromisoformat(commit_date_str[:10])
            except (ValueError, TypeError):
                pass
    
    latencies = []
    valid_records = 0
    
    for record in data:
        try:
            commit = record.get("commit")
            commit_date_str = record.get("commit_date")
            fixed_by = record.get("fixed_by") or []
            
            if not commit or not commit_date_str:
                continue
            
            try:
                if isinstance(commit_date_str, str) and len(commit_date_str) >= 10:
                    bug_date = datetime.fromisoformat(commit_date_str[:10])
                else:
                    continue
            except (ValueError, TypeError):
                continue
            
            for fixed_by_commit in fixed_by:
                if not fixed_by_commit or fixed_by_commit not in commit_to_date:
                    continue
                
                fix_date = commit_to_date[fixed_by_commit]
                latency = (fix_date - bug_date).days
                
                if latency >= 0:
                    latencies.append(latency)
                    valid_records += 1
                
        except Exception:
            continue
    
    if not latencies:
        return {}
    
    median_days = np.median(latencies)
    p95_days = np.percentile(latencies, 95)
    pct_fixed_7days = sum(1 for x in latencies if x <= 7) / len(latencies) * 100
    avg_days = np.mean(latencies)
    
    return {
        "median_days": median_days,
        "avg_days": avg_days,
        "p95_days": p95_days,
        "pct_fixed_7days": pct_fixed_7days
    }


def generate_comparison_table(results_summary):
    if not results_summary:
        print("Sem dados para comparação.")
        return
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resumo"

    headers = ["Projeto", "Máx.", "Média", "> 5 Níveis (%)", "Múltiplas (%)", "Máx. FIX", "Média", "Mediana", "<= 7 dias (%)"]
    ws.append(headers)

    for repo_name in sorted(results_summary.keys()):
        results = results_summary[repo_name]
        
        max_d = results.get("max_depth", {}).get("longest_chain", "N/A")
        avg_max_depth = results.get("max_depth", {}).get("avg_max_depth", "N/A") # Separado de avg_days
        avg_all_depth = results.get("max_depth", {}).get("avg_all_depth", "N/A") # Nova variável para média de todas as profundidades
        pct_chains_gt_5 = results.get("max_depth", {}).get("pct_chains_gt_5", "N/A")
        
        multi_fix = results.get("bifurcation", {}).get("pct_multiple_fixes", "N/A")
        max_fixes = results.get("bifurcation", {}).get("max_fixes", "N/A")
        
        avg_days = results.get("velocity", {}).get("avg_days", "N/A") # Nova variável para média de dias
        median_days = results.get("velocity", {}).get("median_days", "N/A")
        fix_7days = results.get("velocity", {}).get("pct_fixed_7days", "N/A")
        
        ws.append([repo_name, max_d, avg_all_depth, pct_chains_gt_5, multi_fix, max_fixes, avg_days, median_days, fix_7days])

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    summary_excel_path = os.path.join(OUTPUT_FOLDER, "comparison_summary.xlsx")
    wb.save(summary_excel_path)
        
    summary_json_path = os.path.join(OUTPUT_FOLDER, "comparison_summary.json")
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)   
# ==========================================================
# MAIN
# ==========================================================

def main():
    results_summary = {}  
    
    for file in sorted(os.listdir(INPUT_FILE)):
        if not file.endswith(".json"):
            continue

        print(f"\nProcessando: {file}")
        try:
            raw_data = load_data(os.path.join(INPUT_FILE, file))
            data = preprocess_raw_data(raw_data)
        except Exception as e:
            print(f"  Erro ao carregar: {e}")
            continue

        os.makedirs(OUTPUT_FOLDER, exist_ok=True)

        repo_name = file.replace(".json", "")

        commit_to_fix = build_commit_to_fix(data)

        basic_counts, _ = aggregate_propagation(commit_to_fix)
        max_depth_results = analyze_max_chain_depth(commit_to_fix)
        bifurcation_results = analyze_bifurcation_rate(commit_to_fix)
        velocity_results = analyze_fix_velocity(data)

        results_summary[repo_name] = {
            "max_depth": max_depth_results,
            "bifurcation": bifurcation_results,
            "velocity": velocity_results,
        }
    
    generate_comparison_table(results_summary)


if __name__ == "__main__":
    main()