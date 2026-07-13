import json
import os
import numpy as np
from collections import defaultdict, deque
import matplotlib.pyplot as plt

from utils.utils import Reporter, load_data, preprocess_raw_data

OUTPUT_FOLDER = "./results/chain_description"

def build_commit_to_fix(data):
    commit_to_fix = defaultdict(list)
    for record in data:
        commit = record.get("commit")
        fixed_by = record.get("fixed_by") or []
        commit_to_fix[commit].extend(fixed_by)
    return commit_to_fix

def bfs_unique(graph_dict, start_commit):
    """Percorre o grafo via BFS garantindo que cada commit seja visitado uma vez."""
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

def summarize_bic(bic, graph_dict, bic_cache):
    """Retorna métricas agregadas de propagação para um único BIC."""
    if not bic:
        return {"n_commits": 0, "max_depth": 1, "avg_depth": 1.0, "median_depth": 1.0}

    if bic in bic_cache:
        return bic_cache[bic]

    visited = bfs_unique(graph_dict, bic)
    depths = list(visited.values())

    result = {
        "n_commits":     len(depths),
        "max_depth":     max(depths),
        "avg_depth":     float(np.mean(depths)),
        "median_depth":  float(np.median(depths)),
    }
    bic_cache[bic] = result
    return result

# ==========================================================
# 1 - PROPAGAÇÃO GERAL
# ==========================================================

def aggregate_propagation(graph_dict, title, reporter):
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

def analyze_max_chain_depth(graph_dict, reporter):
    all_depths = compute_global_all_depths(graph_dict)
    
    max_per_bug = {}
    for commit, depths_set in all_depths.items():
        if depths_set:
            max_per_bug[commit] = max(depths_set)
    
    if not max_per_bug:
        return {}
    
    longest_chain = max(max_per_bug.values())
    avg_max_depth = np.mean(list(max_per_bug.values()))
    pct_chains_gt_5 = sum(1 for d in max_per_bug.values() if d > 5) / len(max_per_bug) * 100
    
    print(f"  Max chain depth: {longest_chain}")
    print(f"  Avg max depth: {avg_max_depth:.2f}")
    print(f"  % chains > 5 levels: {pct_chains_gt_5:.1f}%")
    
    return {
        "longest_chain": longest_chain,
        "avg_max_depth": avg_max_depth,
        "pct_chains_gt_5": pct_chains_gt_5
    }

# ==========================================================
# 3 - ANÁLISE DE BIFURCAÇÃO
# ==========================================================

def analyze_bifurcation_rate(graph_dict, reporter):
    children_counts = [len(fixes) for fixes in graph_dict.values() if fixes]
    
    if not children_counts:
        return {}
    
    avg_fixes = np.mean(children_counts)
    pct_multiple_fixes = sum(1 for c in children_counts if c > 1) / len(children_counts) * 100
    max_fixes = max(children_counts)
    
    print(f"  Avg fixes per bug: {avg_fixes:.2f}")
    print(f"  % bugs with multiple fixes: {pct_multiple_fixes:.1f}%")
    print(f"  Max fixes for single bug: {max_fixes}")
    
    return {
        "avg_fixes_per_bug": avg_fixes,
        "pct_multiple_fixes": pct_multiple_fixes,
        "max_fixes": max_fixes
    }

# ==========================================================
# 4 - ANÁLISE DE VELOCIDADE DE CORREÇÃO
# ==========================================================

def analyze_fix_velocity(data, reporter):
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
    import json
    import os
    try:
        import openpyxl
    except ImportError:
        print("A biblioteca 'openpyxl' não está instalada. Execute: pip install openpyxl")
        return

    if not results_summary:
        print("Sem dados para comparação.")
        return
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resumo"

    headers = ["Repositório", "Max Depth", "Avg Depth", "% Multi-Fix", "Median Dias", "% em 7 dias"]
    ws.append(headers)

    for repo_name in sorted(results_summary.keys()):
        results = results_summary[repo_name]
        
        max_d = results.get("max_depth", {}).get("longest_chain", "N/A")
        avg_d = results.get("max_depth", {}).get("avg_max_depth", "N/A")
        multi_fix = results.get("bifurcation", {}).get("pct_multiple_fixes", "N/A")
        median_days = results.get("velocity", {}).get("median_days", "N/A")
        fix_7days = results.get("velocity", {}).get("pct_fixed_7days", "N/A")
        
        ws.append([repo_name, max_d, avg_d, multi_fix, median_days, fix_7days])

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
    
    for file in sorted(os.listdir("./dataset/4-metricas/with_bic")):
        if not file.endswith(".json"):
            continue

        print(f"\nProcessando: {file}")
        try:
            raw_data = load_data(os.path.join("./dataset/4-metricas/with_bic", file))
            data = preprocess_raw_data(raw_data)
        except Exception as e:
            print(f"  Erro ao carregar: {e}")
            continue

        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        output_path = os.path.join(OUTPUT_FOLDER, "chain_description.txt")

        if not os.path.exists(output_path):
            open(output_path, "w").close()

        repo_name = file.replace(".json", "")

        commit_to_fix = build_commit_to_fix(data)

        basic_counts, _ = aggregate_propagation(commit_to_fix, f"Propagação Geral - {repo_name}", reporter=None)
        max_depth_results = analyze_max_chain_depth(commit_to_fix, reporter=None)
        bifurcation_results = analyze_bifurcation_rate(commit_to_fix, reporter=None)
        velocity_results = analyze_fix_velocity(data, reporter=None)

        results_summary[repo_name] = {
            "max_depth": max_depth_results,
            "bifurcation": bifurcation_results,
            "velocity": velocity_results,
        }
    
    generate_comparison_table(results_summary)


if __name__ == "__main__":
    main()