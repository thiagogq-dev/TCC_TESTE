import os
import numpy as np
from utils.utils import safe_float, load_data, get_activity_bucket, Reporter, ACTIVITY_BUCKETS
from utils.stats import (
    teste_chi2, teste_mann_whitney, teste_spearman, aplicar_correcao_bh,
)
import matplotlib.pyplot as plt
from collections import defaultdict

def calculate_avg_metrics_by_tests(data, reporter):
    """
    Calcula a média de complexidade, interfacing e size, comparando commits com e sem testes.

    Retorna lista de dicts {"label", "p"} para correção BH.
    """
    asserts_complexity = []
    no_asserts_complexity = []

    asserts_interfacing = []
    no_asserts_interfacing = []

    asserts_size = []
    no_asserts_size = []

    metrics = {
        "complexity": ("dmm_unit_complexity", asserts_complexity, no_asserts_complexity),
        "interfacing": ("dmm_unit_interfacing", asserts_interfacing, no_asserts_interfacing),
        "size": ("dmm_unit_size", asserts_size, no_asserts_size),
    }

    for record in data:
        has_asserts = record.get("test_files_with_asserts_changes") > 0
        for _, (field, with_asserts_list, without_asserts_list) in metrics.items():
            value = safe_float(record.get(field))
            if value is None:
                continue
            target_list = with_asserts_list if has_asserts else without_asserts_list
            target_list.append(value)
            
    results = []

    reporter.write("=== MÉDIA DAS MÉTRICAS X ASSERTS ===")
    reporter.write("= COMPLEXIDADE MÉDIA =")
    if asserts_complexity:
        reporter.write(f"Com asserts:  {np.mean(asserts_complexity):.4f}")
    if no_asserts_complexity:
        reporter.write(f"Sem asserts:  {np.mean(no_asserts_complexity):.4f}")
    results.append(teste_mann_whitney(asserts_complexity, no_asserts_complexity, "Complexidade com vs sem asserts", reporter))

    reporter.write("\n= INTERFACING MÉDIO =")
    if asserts_interfacing:
        reporter.write(f"Com asserts:  {np.mean(asserts_interfacing):.4f}")
    if no_asserts_interfacing:
        reporter.write(f"Sem asserts:  {np.mean(no_asserts_interfacing):.4f}")
    results.append(teste_mann_whitney(asserts_interfacing, no_asserts_interfacing, "Interfacing com vs sem asserts", reporter))

    reporter.write("\n= SIZE MÉDIO =")
    if asserts_size:
        reporter.write(f"Com asserts:  {np.mean(asserts_size):.4f}")
    if no_asserts_size:
        reporter.write(f"Sem asserts:  {np.mean(no_asserts_size):.4f}")
    results.append(teste_mann_whitney(asserts_size, no_asserts_size, "Size com vs sem asserts", reporter))

    reporter.write("")
    return results


def calculate_added_asserts_churn(data, reporter):
    """
    Calcula a correlação entre a quantidade de asserts adicionados e o churn.

    Retorna dict {"label", "p"} para correção BH.
    """
    asserts_growth_list, asserts_churn_list, lines_changed = [], [], []

    for record in data:
        added_asserts = record.get("added_asserts")
        removed_asserts = record.get("removed_asserts")
        lines = record.get("java_lines_changed")

        if added_asserts is None or lines is None:
            continue

        asserts_churn = added_asserts + removed_asserts
        asserts_growth = added_asserts - removed_asserts
        
        asserts_growth_list.append(asserts_growth)
        asserts_churn_list.append(asserts_churn)
        lines_changed.append(lines)

    reporter.write("=== ATIVIDADE EM ASSERTS X CHURN (LINES) ===")
    reporter.write("Nota: 'assert churn' mede movimento total; 'assert growth' mede mudança líquida")
    reporter.write("")

    reporter.write("=== ADIÇÃO DE ASSERTS X CHURN (LINES) ===")
    if not asserts_growth_list:
        reporter.write("Sem dados suficientes para análise.")
        reporter.write("")
        return {"label": "asserts adicionados × linhas alteradas", "p": None}
    
    reporter.write("=== ASSERT CHURN (ADD+DEL) X CHURN (LINES) ===")
    r1 = teste_spearman(
        asserts_churn_list,
        lines_changed,
        "assert churn × linhas alteradas",
        reporter
    )

    reporter.write("\n=== ASSERT GROWTH (ADD-DEL) X CHURN (LINES) ===")
    r2 = teste_spearman(
        asserts_growth_list,
        lines_changed,
        "crescimento de asserts × linhas alteradas",
        reporter
    )

    # reporter.write(f"Média de asserts adicionados: {np.mean(asserts_growth_list):.4f}")
    # reporter.write(f"Média de linhas alteradas: {np.mean(lines_changed):.2f}")
    reporter.write("")
    return r1, r2

def calculate_experience_vs_tests(data, reporter, results_folder):
    """
    Analisa a proporção de commits com testes por faixa de experiência do contribuidor.

    Retorna dict {"label", "p"} do Chi² para correção BH.
    """
    bucket_with  = defaultdict(int)
    bucket_total = defaultdict(int)

    repo_name = data[0].get("Repository", "desconhecido").split("/")[-1]

    for relation in data:
        activity = relation.get("contributor_activity")
        bucket   = get_activity_bucket(activity)
        if bucket is None:
            continue
        bucket_total[bucket] += 1
        if relation.get("test_files_with_asserts_changes") > 0:
            bucket_with[bucket] += 1

    total_tests_global = sum(bucket_with.values())

    reporter.write("=== EXPERIÊNCIA X TESTES ===")

    tabela, proportions, totals = [], [], []

    for bucket in ACTIVITY_BUCKETS:
        total      = bucket_total[bucket]
        with_count = bucket_with[bucket]

        prop_bucket = (with_count / total * 100) if total > 0 else 0
        prop_global = (with_count / total_tests_global * 100) if total_tests_global > 0 else 0

        proportions.append(prop_bucket)
        totals.append(total)
        tabela.append([with_count, total - with_count])

        reporter.write(
            f"[{bucket}] commits={total} | "
            f"com testes={with_count} | "
            f"sem testes={total - with_count} | "
            f"proporção por bucket={prop_bucket:.2f}% | "
            f"proporção geral={prop_global:.2f}%"
        )

    result = {"label": "experiência × presença de testes", "p": None}
    if len(tabela) >= 2:
        result = teste_chi2(tabela, "experiência × presença de testes", reporter)

    reporter.write("")

    return result


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    os.makedirs("./results", exist_ok=True)

    for file in sorted(os.listdir("./relations")):
        if not file.endswith(".json"):
            continue

        FOLDER_REPO_PATH = file.replace(".json", "")
        os.makedirs(f"./results/{FOLDER_REPO_PATH}", exist_ok=True)

        INPUT_PATH      = f"./relations/{file}"
        RESULTS_FOLDER  = f"./results/{FOLDER_REPO_PATH}"
        OUTPUT_PATH     = f"{RESULTS_FOLDER}/rq4.txt"

        data = load_data(INPUT_PATH)

        if os.path.exists(OUTPUT_PATH):
            open(OUTPUT_PATH, "w").close()

        reporter = Reporter(OUTPUT_PATH)

        reporter.write(f"{FOLDER_REPO_PATH}")
        reporter.write("R4: Quais fatores estão associados à presença de alterações em testes?\n")

        pvalores = []
        
        rs = calculate_avg_metrics_by_tests(data, reporter)
        pvalores.extend(rs)

        r1, r2 = calculate_added_asserts_churn(data, reporter)
        pvalores.append(r1)
        pvalores.append(r2)

        r = calculate_experience_vs_tests(data, reporter, RESULTS_FOLDER)
        pvalores.append(r)

        # --- correção BH sobre toda a família tests_analyses ---
        aplicar_correcao_bh(pvalores, reporter, label="RQ4")

        print(f"Análises de RQ4 concluídas: {file} -> {OUTPUT_PATH}")