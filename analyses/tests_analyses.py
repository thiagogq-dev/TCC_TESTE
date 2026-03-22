import os
import numpy as np
from utils.utils import safe_float, load_data, get_activity_bucket, Reporter, ACTIVITY_BUCKETS
from utils.stats import teste_chi2, teste_mann_whitney, teste_spearman, describe_distribution
import matplotlib.pyplot as plt
from collections import defaultdict
# ==========================================================
# 1 - PROPORÇÃO DE TESTES
# ==========================================================
def calculate_test_changes(data, reporter):
    """Calcula a proporção de commits com e sem testes."""
    total = len(data)
    tests = sum(1 for d in data if d.get("has_tests") == "Yes")
    no_tests = total - tests

    reporter.write("=== PROPORÇÃO DE TESTES NOS COMMITS ===")
    reporter.write(f"Com testes: {tests} ({tests/total*100:.2f}%)")
    reporter.write(f"Sem testes: {no_tests} ({no_tests/total*100:.2f}%)")
    reporter.write("")

# ==========================================================
# 2 - BUG COMMIT X TESTES
# ==========================================================
def calculate_proportion_bugs_tests(data, reporter):
    """Calcula a proporção de commits que introduziram bugs, comparando com e sem testes."""
    caused_bug_with_tests = 0 # commits com testes que introduziram bugs
    caused_bug_without_tests = 0 # commits sem testes que introduziram bugs

    no_caused_bug_with_tests = 0 # commits com testes que NÃO introduziram bugs
    no_caused_bug_without_tests = 0 # commits sem testes que NÃO introduziram bugs

    for relation in data:
        has_tests = relation.get("has_tests") == "Yes"
        has_fix = len(relation.get("fixed_by", [])) > 0

        if has_fix:
            if has_tests:
                caused_bug_with_tests += 1
            else:
                caused_bug_without_tests += 1
        else:
            if has_tests:
                no_caused_bug_with_tests += 1
            else:
                no_caused_bug_without_tests += 1

    reporter.write("=== BUGS INTRODUZIDOS ===")
    reporter.write(f"Com testes que introduziram bugs:      {caused_bug_with_tests}")
    reporter.write(f"Sem testes que introduziram bugs:      {caused_bug_without_tests}")
    reporter.write(f"Com testes que NÃO introduziram bugs:  {no_caused_bug_with_tests}")
    reporter.write(f"Sem testes que NÃO introduziram bugs:  {no_caused_bug_without_tests}")

    # --- Teste estatístico ---
    # H0: presença de testes é independente de introduzir bugs
    tabela = [
        [caused_bug_with_tests,    caused_bug_without_tests],
        [no_caused_bug_with_tests, no_caused_bug_without_tests],
    ]
    teste_chi2(tabela, "testes × introdução de bug", reporter)

    # Odds Ratio como medida de efeito
    try:
        or_value = (caused_bug_with_tests * no_caused_bug_without_tests) / \
                   (caused_bug_without_tests * no_caused_bug_with_tests)
        reporter.write(f"  [Odds Ratio] OR={or_value:.4f}  "
                       f"({'commits com testes têm MENOR risco' if or_value < 1 else 'commits com testes têm MAIOR risco'})")
    except ZeroDivisionError:
        reporter.write("  [Odds Ratio] Divisão por zero — célula com valor 0.")

    reporter.write("")

# ==========================================================
# 3 - MÉDIA DAS MÉTRICAS X TESTES
# ==========================================================
def calculate_avg_metrics_by_tests(data, reporter):
    """Calcula a média de complexidade, interfacing e size, comparando commits com e sem testes."""
    tests_complexity = []
    no_tests_complexity = []

    tests_interfacing = []
    no_tests_interfacing = []

    tests_size = []
    no_tests_size = []

    metrics = {
        "complexity": ("dmm_unit_complexity", tests_complexity, no_tests_complexity),
        "interfacing": ("dmm_unit_interfacing", tests_interfacing, no_tests_interfacing),
        "size": ("dmm_unit_size", tests_size, no_tests_size),
    }  

    for record in data:
        for _, (field, with_tests_list, without_tests_list) in metrics.items():
            value = safe_float(record.get(field))
            if value is None:
                continue
            if record.get("has_tests") == "Yes":
                with_tests_list.append(value)
            else:               
                without_tests_list.append(value)

    reporter.write("=== MÉDIA DAS MÉTRICAS X TESTES ===")
    reporter.write("= COMPLEXIDADE MÉDIA =")
    if tests_complexity:
        reporter.write(f"Com testes:  {np.mean(tests_complexity):.4f}")
    if no_tests_complexity:
        reporter.write(f"Sem testes:  {np.mean(no_tests_complexity):.4f}")
    teste_mann_whitney(tests_complexity, no_tests_complexity, "Complexidade com vs sem testes", reporter)

    reporter.write("\n= INTERFACING MÉDIO =")
    if tests_interfacing:
        reporter.write(f"Com testes:  {np.mean(tests_interfacing):.4f}")
    if no_tests_interfacing:
        reporter.write(f"Sem testes:  {np.mean(no_tests_interfacing):.4f}")
    teste_mann_whitney(tests_interfacing, no_tests_interfacing, "Interfacing com vs sem testes", reporter)

    reporter.write("\n= SIZE MÉDIO =")
    if tests_size:
        reporter.write(f"Com testes:  {np.mean(tests_size):.4f}")
    if no_tests_size:
        reporter.write(f"Sem testes:  {np.mean(no_tests_size):.4f}")
    teste_mann_whitney(tests_size, no_tests_size, "Size com vs sem testes", reporter)

    reporter.write("")

# ==========================================================
# 4 - ADIÇÃO DE ASSERTS X CHURN
# ==========================================================
def calculate_added_asserts_churn(data, reporter):
    """Calcula a correlação entre a quantidade de asserts adicionados e o churn (real_lines_changed)."""
    added_asserts = []
    lines_changed = []
    
    for record in data:
        added = record.get("added_asserts")
        lines = record.get("real_lines_changed")
        if added is None or lines is None:
            continue
        added_asserts.append(added)
        lines_changed.append(lines)

    reporter.write("=== ADIÇÃO DE ASSERTS X CHURN (LINES) ===")
    if not added_asserts or not lines_changed:
        reporter.write("Sem dados suficientes para análise.")
        reporter.write("")
        return
    
    reporter.write(f"Média de asserts adicionados: {np.mean(added_asserts):.4f}")
    reporter.write(f"Média de linhas alteradas: {np.mean(lines_changed):.2f}")
    teste_spearman(added_asserts, lines_changed, "asserts adicionados × linhas alteradas", reporter)
    reporter.write("")

# ==========================================================
# 5 - DISTRIBUIÇÃO DO TAMANHO DE PROPAGAÇÃO (fixed_by)
# ==========================================================
def calculate_fix_count_distribution(data, reporter):
    with_tests = []
    without_tests = []

    for relation in data:
        count = len(relation.get("fixed_by", []))
        if relation.get("has_tests") == "Yes":
            with_tests.append(count)
        else:
            without_tests.append(count)

    reporter.write("=== DISTRIBUIÇÃO DE fixed_by ===")
    for group_name, values in [("Com testes", with_tests), ("Sem testes", without_tests)]:
        dist = describe_distribution(values)
        if not dist:
            reporter.write(f"[{group_name}] sem dados")
            continue
        reporter.write(
            f"[{group_name}] min={dist['min']} max={dist['max']} "
            f"média={dist['mean']:.3f} mediana={dist['median']:.3f} p90={dist['p90']:.3f}"
        )

    teste_mann_whitney(with_tests, without_tests, "fixed_by: com vs sem testes", reporter)
    reporter.write("")

# ==========================================================
# 6 - EXPERIÊNCIA X PRESENÇA DE TESTES
# ==========================================================
def calculate_experience_vs_tests(data, reporter, results_folder):
    bucket_with    = defaultdict(int)
    bucket_total   = defaultdict(int)

    repo_name = data[0].get("Repository", "desconecido").split("/")[-1]

    for relation in data:
        activity = relation.get("contributor_activity")
        bucket   = get_activity_bucket(activity)
        if bucket is None:
            continue
        
        bucket_total[bucket] += 1
        has_tests = relation.get("has_tests") == "Yes"
        if has_tests:
            bucket_with[bucket] += 1

    total_tests_global = sum(bucket_with.values())

    reporter.write("=== EXPERIÊNCIA X TESTES ===")

    tabela = []
    proportions = []
    totals = []

    for bucket in ACTIVITY_BUCKETS:
        total = bucket_total[bucket]
        with_tests = bucket_with[bucket]

        prop_bucket = (with_tests / total * 100) if total > 0 else 0
        prop_global = (with_tests / total_tests_global * 100) if total_tests_global > 0 else 0
        proportions.append(prop_bucket)
        totals.append(total)
        tabela.append([with_tests, total - with_tests])

        reporter.write(
            f"[{bucket}] commits={total} | "
            f"com testes={with_tests} | "
            f"sem testes={total - with_tests} | "
            f"proporção por bucket={prop_bucket:.2f}% | "
            f"proporção geral={prop_global:.2f}%"
        )

    if len(tabela) >= 2:
        teste_chi2(tabela, "experiência × presença de testes", reporter)

    reporter.write("")

    if not any(proportions):
        return
 
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    x = np.arange(len(ACTIVITY_BUCKETS))
    width = 0.35
    # Barras do bucket (proporção por bucket)
    bars1 = ax.bar(x - width/2, proportions, width, color="#1f77b4", alpha=0.85, label="Por bucket")
    # Barras da proporção geral (proporção geral de cada bucket)
    global_props_per_bucket = []
    for bucket in ACTIVITY_BUCKETS:
        with_tests = bucket_with[bucket]
        prop_global = (with_tests / total_tests_global * 100) if total_tests_global > 0 else 0
        global_props_per_bucket.append(prop_global)
    bars2 = ax.bar(x + width/2, global_props_per_bucket, width, color="gray", alpha=0.5, label="Proporção geral (por bucket)")

    for bar, prop, total in zip(bars1, proportions, totals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.8,
            f"{prop:.1f}%\n(n={total})",
            ha="center", va="bottom", fontsize=9,
        )

    for bar, prop in zip(bars2, global_props_per_bucket):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.8,
            f"{prop:.1f}%",
            ha="center", va="bottom", fontsize=9, color="gray"
        )

    ax.set_xticks(x)
    ax.set_xticklabels(ACTIVITY_BUCKETS)
    ax.set_xlabel("Número de commits anteriores do autor (experiência)")
    ax.set_ylabel("% de commits com testes")
    ax.set_title(f"Proporção de commits com testes por faixa de experiência — {repo_name}")
    ax.set_ylim(0, max(proportions + global_props_per_bucket) * 1.2 if proportions else 100)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{results_folder}/contributor_activity_bar.png", dpi=300, bbox_inches="tight")
    plt.close()

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

        INPUT_PATH = f"./relations/{file}"
        RESULTS_FOLDER = f"./results/{FOLDER_REPO_PATH}"
        OUTPUT_PATH = f"{RESULTS_FOLDER}/tests_analyses.txt"

        data = load_data(INPUT_PATH)

        if os.path.exists(OUTPUT_PATH):
            open(OUTPUT_PATH, "w").close()

        reporter = Reporter(OUTPUT_PATH)

        calculate_test_changes(data, reporter)
        calculate_proportion_bugs_tests(data, reporter)
        calculate_avg_metrics_by_tests(data, reporter)
        calculate_added_asserts_churn(data, reporter)
        calculate_fix_count_distribution(data, reporter)
        calculate_experience_vs_tests(data, reporter, RESULTS_FOLDER)
        print(f"Análises concluídas: {file} -> {OUTPUT_PATH}")