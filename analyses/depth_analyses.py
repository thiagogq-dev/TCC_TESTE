import os
import numpy as np
from collections import defaultdict, deque
import matplotlib.pyplot as plt
from utils.utils import load_data, Reporter
from utils.stats import teste_mann_whitney, teste_kruskal, teste_spearman
# ==========================================================
# UTIL
# ==========================================================

def build_commit_to_fix(data):
    commit_to_fix = defaultdict(list)
    for record in data:
        commit = record.get("commit")
        fixed_by = record.get("fixed_by") or []
        commit_to_fix[commit].extend(fixed_by)
    return commit_to_fix

def compute_dynamic_threshold(data):
    activities = [rec.get("contributor_activity") for rec in data]
    return float(np.median(activities))

def build_has_tests_map(data):
    return {rec.get("commit"): (rec.get("has_tests") == "Yes") for rec in data}

# ==========================================================
# NÚCLEO DE TRAVESSIA
# ==========================================================

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

def precompute_bfs(data, graph_dict):
    """
    Executa o BFS uma única vez para cada BIC único e armazena em cache.
    Todas as funções de análise consomem este cache — nenhum BFS é refeito.
    """
    cache = {}
    seen = set()
    for rec in data:
        bic = rec.get("commit")
        if bic and bic not in seen:
            seen.add(bic)
            cache[bic] = bfs_unique(graph_dict, bic)
    return cache

def summarize_bic_from_cache(visited):
    """Calcula métricas de propagação a partir do dict `visited` já computado."""
    depths = list(visited.values())
    return {
        "n_commits":    len(depths),
        "max_depth":    max(depths),
        "avg_depth":    float(np.mean(depths)),
        "median_depth": float(np.median(depths)),
    }

def iter_unique_bics(data):
    """Itera sobre os registros retornando apenas BICs únicos (commit, rec)."""
    seen = set()
    for rec in data:
        bic = rec.get("commit")
        if bic and bic not in seen:
            seen.add(bic)
            yield bic, rec

# ==========================================================
# LOOP ÚNICO: coleta todas as métricas por BIC de uma vez
# ==========================================================

def collect_all_bic_metrics(data, bfs_cache, graph_dict, has_tests_map, threshold):
    """
    Percorre os BICs únicos uma única vez e coleta simultaneamente
    todos os dados necessários para as análises 1–4.

    Retorna um dict com os acumuladores prontos para cada análise.
    """
    # — análise 1: propagação geral
    overall    = defaultdict(int)
    with_fix   = defaultdict(int)

    # — análises 2 e 3: experiência (± testes) x profundidade
    expert_depths      = []
    non_expert_depths  = []
    activities         = []
    avg_depths         = []
    exp_groups = {
        "expert_with_tests":        [],
        "expert_without_tests":     [],
        "non_expert_with_tests":    [],
        "non_expert_without_tests": [],
    }

    # — análise 4: commits com testes vs sem testes
    prop_with_tests    = defaultdict(int)
    prop_without_tests = defaultdict(int)
    depths_with        = []
    depths_without     = []

    for bic, rec in iter_unique_bics(data):
        visited   = bfs_cache[bic]
        summary   = summarize_bic_from_cache(visited)
        avg_depth = summary["avg_depth"]
        activity  = rec.get("contributor_activity")
        has_tests = rec.get("has_tests") == "Yes"

        # — análise 1
        for commit, depth in visited.items():
            overall[depth] += 1
            if graph_dict.get(commit):
                with_fix[depth] += 1

        # — análises 2 e 3
        activities.append(activity)
        avg_depths.append(avg_depth)

        if activity > threshold:
            expert_depths.append(avg_depth)
            key = "expert_with_tests" if has_tests else "expert_without_tests"
        else:
            non_expert_depths.append(avg_depth)
            key = "non_expert_with_tests" if has_tests else "non_expert_without_tests"
        exp_groups[key].append(avg_depth)

        # — análise 4
        for commit, depth in visited.items():
            if has_tests_map.get(commit, False):
                prop_with_tests[depth] += 1
                depths_with.append(depth)
            else:
                prop_without_tests[depth] += 1
                depths_without.append(depth)

    return {
        "overall":            overall,
        "with_fix":           with_fix,
        "expert_depths":      expert_depths,
        "non_expert_depths":  non_expert_depths,
        "activities":         activities,
        "avg_depths":         avg_depths,
        "exp_groups":         exp_groups,
        "prop_with_tests":    prop_with_tests,
        "prop_without_tests": prop_without_tests,
        "depths_with":        depths_with,
        "depths_without":     depths_without,
    }


# ==========================================================
# 1 - PROPAGAÇÃO GERAL
# ==========================================================

def aggregate_propagation(metrics, title, reporter):
    overall  = metrics["overall"]
    with_fix = metrics["with_fix"]

    reporter.write(f"=== {title} ===")
    for depth in sorted(overall.keys()):
        total = overall[depth]
        fix   = with_fix.get(depth, 0)
        pct   = (fix / total * 100) if total else 0
        reporter.write(f"Level {depth}: total={total} | with_fix={fix} ({pct:.1f}%)")
    reporter.write("")

    return overall, with_fix


# ==========================================================
# 2 - EXPERIÊNCIA X PROFUNDIDADE DA CADEIA
# ==========================================================

def aggregate_by_experience(metrics, threshold, reporter):
    expert_depths     = metrics["expert_depths"]
    non_expert_depths = metrics["non_expert_depths"]
    activities        = metrics["activities"]
    avg_depths        = metrics["avg_depths"]

    avg_exp = float(np.mean(expert_depths))     if expert_depths     else 0.0
    avg_non = float(np.mean(non_expert_depths)) if non_expert_depths else 0.0

    reporter.write("=== EXPERIENCIA X PROFUNDIDADE DA CADEIA (UNIDADE = BIC) ===")
    reporter.write(f"Threshold (mediana atividade): {threshold:.1f}")
    reporter.write(f"Experientes:     avg depth={avg_exp:.4f}  n_bics={len(expert_depths)}")
    reporter.write(f"Nao experientes: avg depth={avg_non:.4f}  n_bics={len(non_expert_depths)}")

    teste_mann_whitney(expert_depths, non_expert_depths, "avg_depth por BIC: experientes vs nao experientes", reporter)
    teste_spearman(activities, avg_depths, "atividade do contribuidor x avg_depth por BIC", reporter)
    reporter.write("")

    return avg_exp, avg_non


# ==========================================================
# 3 - EXPERIÊNCIA + TESTES X PROFUNDIDADE
# ==========================================================

def aggregate_by_experience_and_tests(metrics, reporter):
    groups = metrics["exp_groups"]
    avgs   = {k: (float(np.mean(v)) if v else 0.0) for k, v in groups.items()}

    reporter.write("=== EXPERIENCIA + TESTES X PROFUNDIDADE (UNIDADE = BIC) ===")
    for k, v in avgs.items():
        reporter.write(f"  {k}: avg depth={v:.4f}  n_bics={len(groups[k])}")

    teste_kruskal(groups, "4 grupos (exp x testes) x avg_depth por BIC", reporter)
    reporter.write("")

    return avgs


# ==========================================================
# 4 - PROPAGAÇÃO: COMMITS COM TESTES vs SEM TESTES
# ==========================================================

def aggregate_tests_vs_no_tests(metrics, reporter):
    prop_with    = metrics["prop_with_tests"]
    prop_without = metrics["prop_without_tests"]
    depths_with  = metrics["depths_with"]
    depths_without = metrics["depths_without"]

    reporter.write("=== PROPAGACAO: COMMITS COM TESTES vs SEM TESTES ===")
    for d, c in sorted(prop_with.items()):
        reporter.write(f"  [Com testes]  Level {d}: {c}")
    reporter.write("")
    for d, c in sorted(prop_without.items()):
        reporter.write(f"  [Sem testes]  Level {d}: {c}")

    teste_mann_whitney(depths_with, depths_without, "profundidade: commits com vs sem testes", reporter)
    reporter.write("")

    return prop_with, prop_without, depths_with


# ==========================================================
# 5 - LOCALIZAÇÃO DOS TESTES NA CADEIA
# ==========================================================

def tests_location(all_depths, reporter):
    if not all_depths:
        return {}

    p33 = np.percentile(all_depths, 33.33)
    p66 = np.percentile(all_depths, 66.66)

    counts = {"inicio": 0, "meio": 0, "fim": 0}
    for d in all_depths:
        if d <= p33:
            counts["inicio"] += 1
        elif d <= p66:
            counts["meio"] += 1
        else:
            counts["fim"] += 1

    reporter.write("=== LOCALIZACAO DOS TESTES NA CADEIA ===")
    total = len(all_depths)
    for k, v in counts.items():
        pct = v / total * 100 if total else 0
        reporter.write(f"  {k}: {v} ({pct:.1f}%)")
    reporter.write("")

    return counts


# ==========================================================
# PLOTS E OUTPUT
# ==========================================================

def save_bar(labels, values, filename, title="", xlabel="", ylabel=""):
    """Salva gráfico de barras genérico reaproveitável."""
    plt.figure(figsize=(8, 4))
    plt.bar(labels, values, color="#1f77b4", alpha=0.8)
    if xlabel: plt.xlabel(xlabel)
    if ylabel: plt.ylabel(ylabel)
    plt.title(title)

    if labels and isinstance(labels[0], str):
        plt.xticks(rotation=20)
    else:
        plt.xticks(labels)

    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def save_histogram(counts, filename, title="Histogram", xlabel="Level", ylabel="Count"):
    """Encapsula chamada do save_bar para formatar dados de dicionário como histograma."""
    if not counts:
        return
    levels = sorted(counts.keys())
    vals   = [counts[l] for l in levels]
    save_bar(levels, vals, filename, title=title, xlabel=xlabel, ylabel=ylabel)


# ==========================================================
# MAIN
# ==========================================================

def main():
    for relations_file in sorted(os.listdir("./relations")):
        if not relations_file.endswith(".json"):
            continue

        print(f"\nProcessando: {relations_file}")
        try:
            data = load_data(os.path.join("./relations", relations_file))
        except Exception as e:
            print(f"  Erro ao carregar: {e}")
            continue

        OUTPUT_REPO_FOLDER = relations_file.replace(".json", "")
        os.makedirs(f"./results/{OUTPUT_REPO_FOLDER}", exist_ok=True)
        output_path = f"./results/{OUTPUT_REPO_FOLDER}/depth_analyses.txt"

        if not os.path.exists(output_path):
            open(output_path, "w").close()

        reporter = Reporter(output_path)

        commit_to_fix = build_commit_to_fix(data)
        has_tests_map = build_has_tests_map(data)          # uma vez só
        threshold     = compute_dynamic_threshold(data)
        bfs_cache     = precompute_bfs(data, commit_to_fix) # BFS único para todos os BICs

        # Loop único: coleta todos os acumuladores de uma vez
        metrics = collect_all_bic_metrics(
            data, bfs_cache, commit_to_fix, has_tests_map, threshold
        )


        # 1 — Propagação geral
        basic_counts, _ = aggregate_propagation(metrics, "PROPAGACAO", reporter)
        save_histogram(basic_counts, f"./results/{OUTPUT_REPO_FOLDER}/histograma_general.png",
                        title="General Propagation Histogram")

        # 2 — Experiência x profundidade
        avg_exp, avg_non = aggregate_by_experience(metrics, threshold, reporter)
        save_bar(
            ["Experienced", "Non-experienced"], [avg_exp, avg_non],
            f"./results/{OUTPUT_REPO_FOLDER}/exp_vs_no_exp.png",
            title="Average chain depth by contributor experience", ylabel="Average depth"
        )

        # 3 — Experiência + testes x profundidade
        groups_avgs = aggregate_by_experience_and_tests(metrics, reporter)
        save_bar(
            list(groups_avgs.keys()), list(groups_avgs.values()),
            f"./results/{OUTPUT_REPO_FOLDER}/exp_vs_no_exp_and_tests.png",
            title="Avg depth: experience vs tests"
        )

        # 4 — Propagação: com testes vs sem testes
        with_tests, without_tests, depths_with_tests = aggregate_tests_vs_no_tests(metrics, reporter)
        save_histogram(with_tests, f"./results/{OUTPUT_REPO_FOLDER}/propagation_with_tests.png",
                        title="Propagation (commits with tests)")
        save_histogram(without_tests, f"./results/{OUTPUT_REPO_FOLDER}/propagation_without_tests.png",
                        title="Propagation (commits without tests)")

        # 5 — Localização dos testes na cadeia
        tests_location(depths_with_tests, reporter)

        print(f"  Concluido -> ./results/{OUTPUT_REPO_FOLDER}/")

if __name__ == "__main__":
    main()