import os
import numpy as np
from collections import defaultdict, deque
import matplotlib.pyplot as plt
from utils.utils import load_data, Reporter, ACTIVITY_BUCKETS, get_activity_bucket
from utils.stats import (
    teste_mann_whitney, teste_kruskal, teste_spearman,
    aplicar_correcao_bh,
)

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

def build_has_tests_map(data):
    return {rec.get("commit"): (rec.get("test_files_with_asserts_changes") > 0) for rec in data}

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

def collect_all_bic_metrics(data, bfs_cache, graph_dict, has_tests_map):
    """
    Percorre os BICs únicos uma única vez e coleta simultaneamente
    todos os dados necessários para as análises 1–4.

    A experiência é agora categorizada em buckets absolutos (0, 1-5, 6-20,
    21-100, 100+), independente da distribuição da amostra.
    """
    overall  = defaultdict(int)
    with_fix = defaultdict(int)

    # Grupos por bucket: cada bucket armazena lista de avg_depth dos BICs
    bucket_depths = {b: [] for b in ACTIVITY_BUCKETS}

    prop_with_tests    = defaultdict(int)
    prop_without_tests = defaultdict(int)
    depths_with        = []
    depths_without     = []
    avg_depths_with_tests    = []
    avg_depths_without_tests = []

    # Para o Spearman: atividade contínua e avg_depth na mesma ordem
    activities_all = []
    avg_depths_all = []

    for bic, rec in iter_unique_bics(data):
        visited   = bfs_cache[bic]
        summary   = summarize_bic_from_cache(visited)
        avg_depth = summary["avg_depth"]
        activity  = rec.get("contributor_activity")
        has_tests = rec.get("test_files_with_asserts_changes") > 0
        bucket    = get_activity_bucket(activity)

        for commit, depth in visited.items():
            overall[depth] += 1
            if graph_dict.get(commit):
                with_fix[depth] += 1

        # Agrupa avg_depth por bucket (todos os buckets)
        if bucket is not None:
            bucket_depths[bucket].append(avg_depth)

        if has_tests:
            avg_depths_with_tests.append(avg_depth)
        else:
            avg_depths_without_tests.append(avg_depth)

        # Spearman: coleta atividade contínua e avg_depth na mesma ordem
        if activity is not None:
            activities_all.append(activity)
            avg_depths_all.append(avg_depth)

        for commit, depth in visited.items():
            if has_tests_map.get(commit, False):
                prop_with_tests[depth] += 1
                depths_with.append(depth)
            else:
                prop_without_tests[depth] += 1
                depths_without.append(depth)

    return {
        "overall":                  overall,
        "with_fix":                 with_fix,
        "bucket_depths":            bucket_depths,
        "prop_with_tests":          prop_with_tests,
        "prop_without_tests":       prop_without_tests,
        "depths_with":              depths_with,
        "depths_without":           depths_without,
        "avg_depths_with_tests":    avg_depths_with_tests,
        "avg_depths_without_tests": avg_depths_without_tests,
        "activities_all":           activities_all,
        "avg_depths_all":           avg_depths_all,
    }


# ==========================================================
# ANÁLISES
# ==========================================================

# def aggregate_propagation(metrics, title, reporter):
#     overall  = metrics["overall"]
#     with_fix = metrics["with_fix"]

#     reporter.write(f"=== {title} ===")
#     for depth in sorted(overall.keys()):
#         total = overall[depth]
#         fix   = with_fix.get(depth, 0)
#         pct   = (fix / total * 100) if total else 0
#         reporter.write(f"Level {depth}: total={total} | with_fix={fix} ({pct:.1f}%)")
#     reporter.write("")

#     return overall, with_fix


def aggregate_by_experience(metrics, reporter):
    """
    Análise de experiência × profundidade usando buckets absolutos.

    Estratégia estatística:
      1. Kruskal-Wallis sobre todos os 5 buckets → verifica se há diferença global
      2. Spearman entre atividade contínua e avg_depth → direção e força da
         relação ao longo de toda a escala, sem dicotomização

    Retorna lista de dicts {"label", "p"} para correção BH.
    """
    bucket_depths  = metrics["bucket_depths"]
    activities_all = metrics["activities_all"]
    avg_depths_all = metrics["avg_depths_all"]

    reporter.write("=== EXPERIENCIA X PROFUNDIDADE DA CADEIA (BUCKETS) ===")
    reporter.write("Métrica de experiência: commits do autor até 24h anteriores ao BIC")
    reporter.write("")

    for b in ACTIVITY_BUCKETS:
        depths = bucket_depths[b]
        avg    = float(np.mean(depths)) if depths else 0.0
        reporter.write(f"  [{b}] n_bics={len(depths)}  avg_depth={avg:.4f}")
    reporter.write("")

    # 1 — Kruskal-Wallis global (todos os buckets com pelo menos 2 obs.)
    r_kw = teste_kruskal(
        bucket_depths,
        "avg_depth por BIC: todos os buckets de experiência",
        reporter
    )

    # 2 — Spearman: atividade contínua × avg_depth (todos os BICs)
    #     Complementa o MW mostrando se a relação é gradual ao longo da escala
    reporter.write("")
    reporter.write("  [Spearman] Atividade contínua × avg_depth (todos os BICs)")
    r_sp = teste_spearman(
        activities_all, avg_depths_all,
        "atividade contínua do contribuidor x avg_depth por BIC",
        reporter
    )

    reporter.write("")
    return [r_kw, r_sp]

def aggregate_tests_vs_no_tests(metrics, reporter):
    """
    Retorna dict {"label", "p"} do Mann-Whitney para correção BH.
    """
    avg_depths_with    = metrics["avg_depths_with_tests"]
    avg_depths_without = metrics["avg_depths_without_tests"]
    prop_with          = metrics["prop_with_tests"]
    prop_without       = metrics["prop_without_tests"]
    depths_with        = metrics["depths_with"]

    reporter.write("=== PROPAGACAO: COMMITS COM TESTES vs SEM TESTES (UNIDADE = BIC) ===")
    reporter.write(f"  BICs com testes:    n={len(avg_depths_with)}  avg_depth={float(np.mean(avg_depths_with)):.4f}" if avg_depths_with else "  BICs com testes: sem dados")
    reporter.write(f"  BICs sem testes:    n={len(avg_depths_without)}  avg_depth={float(np.mean(avg_depths_without)):.4f}" if avg_depths_without else "  BICs sem testes: sem dados")
    reporter.write("")

    reporter.write("  [Descritivo] Commits com testes por nível:")
    for d, c in sorted(prop_with.items()):
        reporter.write(f"    Level {d}: {c}")
    reporter.write("")
    reporter.write("  [Descritivo] Commits sem testes por nível:")
    for d, c in sorted(prop_without.items()):
        reporter.write(f"    Level {d}: {c}")
    reporter.write("")

    result = teste_mann_whitney(avg_depths_with, avg_depths_without,
                                "avg_depth por BIC: com testes vs sem testes", reporter)
    reporter.write("")
    return result, prop_with, prop_without, depths_with

# ==========================================================
# PLOTS
# ==========================================================

# def save_bar(labels, values, filename, title="", xlabel="", ylabel=""):
#     plt.figure(figsize=(8, 4))
#     plt.bar(labels, values, color="#1f77b4", alpha=0.8)
#     if xlabel: plt.xlabel(xlabel)
#     if ylabel: plt.ylabel(ylabel)
#     plt.title(title)
#     if labels and isinstance(labels[0], str):
#         plt.xticks(rotation=20)
#     else:
#         plt.xticks(labels)
#     plt.grid(axis="y", linestyle="--", alpha=0.5)
#     plt.tight_layout()
#     plt.savefig(filename)
#     plt.close()


# def save_histogram(counts, filename, title="Histogram", xlabel="Level", ylabel="Count"):
#     if not counts:
#         return
#     levels = sorted(counts.keys())
#     vals   = [counts[l] for l in levels]
#     save_bar(levels, vals, filename, title=title, xlabel=xlabel, ylabel=ylabel)


# def save_bucket_depth_plot(bucket_depths, filename, repo_name=""):
#     """
#     Gráfico de barras: avg_depth por bucket de experiência.
#     Inclui anotação com n de BICs por bucket.
#     """
#     avgs   = [float(np.mean(bucket_depths[b])) if bucket_depths[b] else 0.0
#               for b in ACTIVITY_BUCKETS]
#     counts = [len(bucket_depths[b]) for b in ACTIVITY_BUCKETS]

#     fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
#     bars = ax.bar(ACTIVITY_BUCKETS, avgs, color="#1f77b4", alpha=0.85)

#     for bar, avg, n in zip(bars, avgs, counts):
#         ax.text(
#             bar.get_x() + bar.get_width() / 2,
#             bar.get_height() + 0.02,
#             f"{avg:.2f}\n(n={n})",
#             ha="center", va="bottom", fontsize=9
#         )

#     ax.set_xlabel("Commits anteriores do autor (experiência)")
#     ax.set_ylabel("Profundidade média da cadeia (avg_depth)")
#     ax.set_title(f"Profundidade de propagação por faixa de experiência — {repo_name}")
#     ax.grid(axis="y", linestyle="--", alpha=0.4)
#     plt.tight_layout()
#     plt.savefig(filename, dpi=300, bbox_inches="tight")
#     plt.close()


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
        output_path = f"./results/{OUTPUT_REPO_FOLDER}/rq5_ii.txt"

        if not os.path.exists(output_path):
            open(output_path, "w").close()

        reporter = Reporter(output_path)
        repo_name = OUTPUT_REPO_FOLDER

        reporter.write(f"{OUTPUT_REPO_FOLDER}\n")
        reporter.write(f"Características das cadeias de propagação\n")

        commit_to_fix = build_commit_to_fix(data)
        has_tests_map = build_has_tests_map(data)
        bfs_cache     = precompute_bfs(data, commit_to_fix)

        metrics = collect_all_bic_metrics(
            data, bfs_cache, commit_to_fix, has_tests_map
        )

        pvalores = []

        # 1 — Propagação geral (descritivo)
        # basic_counts, _ = aggregate_propagation(metrics, "PROPAGACAO", reporter)
        # save_histogram(basic_counts, f"./results/{OUTPUT_REPO_FOLDER}/histograma_general.png",
                    #    title="General Propagation Histogram")

        # 2 — Experiência (buckets) x profundidade
        rs = aggregate_by_experience(metrics, reporter)
        pvalores.extend(rs)
        # save_bucket_depth_plot(
        #     metrics["bucket_depths"],
        #     f"./results/{OUTPUT_REPO_FOLDER}/exp_buckets_vs_depth.png",
        #     repo_name=repo_name
        # )

        # 3 — Propagação: com testes vs sem testes
        r, with_tests, without_tests, depths_with_tests = aggregate_tests_vs_no_tests(metrics, reporter)
        pvalores.append(r)
        # save_histogram(with_tests,    f"./results/{OUTPUT_REPO_FOLDER}/propagation_with_tests.png",
        #                title="Propagation (commits with tests)")
        # save_histogram(without_tests, f"./results/{OUTPUT_REPO_FOLDER}/propagation_without_tests.png",
        #                title="Propagation (commits without tests)")

        # --- correção BH sobre toda a família depth_analyses ---
        aplicar_correcao_bh(pvalores, reporter, label="RQ5 (ii)")

        print(f"  Concluido -> ./results/{OUTPUT_REPO_FOLDER}/")

if __name__ == "__main__":
    main()