import os
import numpy as np
from collections import defaultdict, deque
import matplotlib.pyplot as plt
from utils.utils import load_data, Reporter, ACTIVITY_BUCKETS, get_activity_bucket, preprocess_raw_data
from utils.stats import (
    teste_mann_whitney, teste_kruskal, teste_spearman,
    aplicar_correcao_bh,
)

def build_commit_to_fix(data):
    """
    Constrói um dicionário que mapeia cada commit para a lista de commits que o corrigem (fixed_by).
    Args:
        data (list): Lista de registros de commits.
    Returns:
        dict: Dicionário onde a chave é o commit e o valor é uma lista de
    """
    commit_to_fix = defaultdict(list)
    for record in data:
        commit = record.get("commit")
        fixed_by = record.get("fixed_by") or []
        commit_to_fix[commit].extend(fixed_by)
    return commit_to_fix

def build_has_tests_map(data):
    """
    Constrói um dicionário que mapeia cada commit para um booleano indicando se ele possui testes com asserts.
    Args:
        data (list): Lista de registros de commits.
    Returns:
        dict: Dicionário onde a chave é o commit e o valor é True se o commit possui testes com asserts, caso contrário False.
    """
    return {rec.get("commit"): (rec.get("test_files_with_asserts_changes") > 0) for rec in data}

# ==========================================================
# NÚCLEO DE TRAVESSIA
# ==========================================================

def bfs_unique(graph_dict, start_commit):
    """
    Realiza uma busca em largura (BFS) a partir de um commit inicial, retornando um dicionário com a profundidade de cada commit visitado.
    Args:
        graph_dict (dict): Dicionário representando o grafo de commits, onde a chave é o commit e o valor é uma lista de commits que ele corrige.
        start_commit (str): Commit inicial para a BFS.
    Returns:
        dict: Dicionário onde a chave é o commit visitado e o valor é a profundidade (nível) do commit em relação ao commit inicial.
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

def precompute_bfs(data, graph_dict):
    """
    Pré-computa a BFS para cada commit único no dataset, armazenando os resultados em um cache.
    Args:
        data (list): Lista de registros de commits.
        graph_dict (dict): Dicionário representando o grafo de commits.
    Returns:
        dict: Dicionário onde a chave é o commit e o valor é o resultado da BFS (dicionário de commits visitados e suas profundidades).
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
    """
    Resume as informações de profundidade de um BIC a partir do cache da BFS.
    Args:
        visited (dict): Dicionário de commits visitados e suas profundidades.
    Returns:
        dict: Dicionário contendo o número total de commits, profundidade máxima, média e mediana das profundidades.
    """
    depths = list(visited.values())
    return {
        "n_commits":    len(depths),
        "max_depth":    max(depths),
        "avg_depth":    float(np.mean(depths)),
        "median_depth": float(np.median(depths)),
    }

def iter_unique_bics(data):
    """
    Itera sobre os commits únicos (BICs) no dataset, garantindo que cada BIC seja processado apenas uma vez.
    Args:
        data (list): Lista de registros de commits.
    Yields:
        tuple: Tupla contendo o commit (BIC) e o registro correspondente.
    """
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
    Coleta todas as métricas relevantes para cada BIC no dataset, incluindo profundidade da cadeia, presença de testes e experiência do contribuidor.
    Args:
        data (list): Lista de registros de commits.
        bfs_cache (dict): Cache da BFS pré-computada para cada commit.
        graph_dict (dict): Dicionário representando o grafo de commits.
        has_tests_map (dict): Dicionário mapeando cada commit para um booleano indicando se possui testes com asserts.
    Returns:
        dict: Dicionário contendo várias métricas agregadas, incluindo profundidade geral, profundidade com FIX, profundidade por bucket de experiência e proporção de commits com/sem testes.
    """
    overall  = defaultdict(int)
    with_fix = defaultdict(int)

    bucket_depths = {b: [] for b in ACTIVITY_BUCKETS}

    prop_with_tests    = defaultdict(int)
    prop_without_tests = defaultdict(int)
    depths_with        = []
    depths_without     = []
    avg_depths_with_tests    = []
    avg_depths_without_tests = []

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

        if bucket is not None:
            bucket_depths[bucket].append(avg_depth)

        if has_tests:
            avg_depths_with_tests.append(avg_depth)
        else:
            avg_depths_without_tests.append(avg_depth)

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

def aggregate_by_experience(metrics, reporter):
    """
    Agrega métricas por bucket de experiência do contribuidor, realizando testes estatísticos (Kruskal-Wallis e Spearman) para verificar diferenças entre os buckets.
    Args:
        metrics (dict): Dicionário contendo métricas coletadas para cada BIC.
        reporter (Reporter): Instância de Reporter para registrar resultados.
    Returns:
        list: Lista de resultados dos testes estatísticos realizados.
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

    r_kw = teste_kruskal(
        bucket_depths,
        "avg_depth por BIC: todos os buckets de experiência",
        reporter
    )

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
# MAIN
# ==========================================================

def main():
    os.makedirs("./results/rq5_ii", exist_ok=True)
    import pandas as pd

    OUTPUT_TEXT_PATH = "./results/rq5_ii/relatorio_texto.txt"
    OUTPUT_CSV_PATH = "./results/rq5_ii/tabela_resultados.csv"

    if os.path.exists(OUTPUT_TEXT_PATH):
        open(OUTPUT_TEXT_PATH, "w").close()

    reporter = Reporter(OUTPUT_TEXT_PATH)
    reporter.write("Características das cadeias de propagação")
    dados_tabela = []

    for relations_file in sorted(os.listdir("./dataset/4-metricas/pair_bic_fix/")):
        if not relations_file.endswith(".json"):
            continue

        print(f"\nProcessando: {relations_file}")
        try:
            raw_data = load_data(os.path.join("./dataset/4-metricas/pair_bic_fix/", relations_file))
            data = preprocess_raw_data(raw_data)
        except Exception as e:
            print(f"  Erro ao carregar: {e}")
            continue

        OUTPUT_REPO_FOLDER = relations_file.replace(".json", "")

        reporter.write("\n" + "="*80)
        reporter.write(f"PROJETO: {OUTPUT_REPO_FOLDER}")
        reporter.write("="*80 + "\n")

        linha_projeto = {"Projeto": OUTPUT_REPO_FOLDER}

        commit_to_fix = build_commit_to_fix(data)
        has_tests_map = build_has_tests_map(data)
        bfs_cache     = precompute_bfs(data, commit_to_fix)

        metrics = collect_all_bic_metrics(
            data, bfs_cache, commit_to_fix, has_tests_map
        )

        pvalores = []

        rs = aggregate_by_experience(metrics, reporter)
        pvalores.extend(rs)

        rmw, with_tests, without_tests, depths_with_tests = aggregate_tests_vs_no_tests(metrics, reporter)
        pvalores.append(rmw)

        resultados_corrigidos = aplicar_correcao_bh(pvalores, reporter, label="RQ5 (ii)")

        if resultados_corrigidos:
            label_kw = "avg_depth por BIC: todos os buckets de experiência"
            label_sp = "atividade contínua do contribuidor x avg_depth por BIC"
            label_mw = "avg_depth por BIC: com testes vs sem testes"

            # Kruskal-Wallis (Experiência - Buckets)
            linha_projeto["p_kw"] = resultados_corrigidos.get(label_kw, (None, None))[1]
            linha_projeto["eps2_kw"] = rs[0].get("effect_size") if rs[0] else None

            # Spearman (Experiência - Contínua)
            linha_projeto["p_sp"] = resultados_corrigidos.get(label_sp, (None, None))[1]
            linha_projeto["rho_sp"] = rs[1].get("effect_size") if rs[1] else None

            # Mann-Whitney (Asserts x Extensão)
            linha_projeto["p_mw"] = resultados_corrigidos.get(label_mw, (None, None))[1]
            linha_projeto["r_mw"] = rmw.get("effect_size") if rmw else None

        dados_tabela.append(linha_projeto)
        print(f"  Concluído -> Adicionado à tabela unificada.")

    if dados_tabela:
        df_resultados = pd.DataFrame(dados_tabela)
        
        # Arredondar as colunas numéricas para 4 casas decimais
        colunas_numericas = ["p_kw", "eps2_kw", "p_sp", "rho_sp", "p_mw", "r_mw"]
        for col in colunas_numericas:
            if col in df_resultados.columns:
                df_resultados[col] = df_resultados[col].astype(float).round(4)
                
        # Exportar com separador de vírgula
        df_resultados.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8', sep=',')

if __name__ == "__main__":
    main()