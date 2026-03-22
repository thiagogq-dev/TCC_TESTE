import json
import os
import numpy as np
from collections import defaultdict
from utils.utils import safe_float, load_data, get_activity_bucket, Reporter, ACTIVITY_BUCKETS
from utils.stats import teste_mann_whitney, teste_spearman, teste_pointbiserial

# ==========================================================
# 1 - RISCO POR QUARTIL DE CHURN (LINES)
# ==========================================================
def calculate_churn_risk_by_quartile_relations(data, reporter):
    """
    Calcula o risco de introdução de bug por quartil de churn (real_lines_changed).
    Churn é uma métrica de tamanho do commit, e commits maiores tendem a ser mais arriscados.
    """
    valid = []
    for record in data:
        real_lines_changed = record.get("real_lines_changed")
        has_fix = len(record.get("fixed_by", [])) > 0
        if real_lines_changed > 0:
            valid.append((real_lines_changed, has_fix))

    reporter.write("=== RISCO DE INTRODUÇÃO DE BUG POR QUARTIL DE CHURN (LINES) ===")

    if not valid:
        reporter.write("Sem dados válidos de lines.")
        reporter.write("")
        return

    lines_values = [v[0] for v in valid]
    q1, q2, q3 = np.percentile(lines_values, [25, 50, 75])

    bins = {"Q1": [], "Q2": [], "Q3": [], "Q4": []}
    for lines, has_fix in valid:
        if lines <= q1:
            bins["Q1"].append(has_fix)
        elif lines <= q2:
            bins["Q2"].append(has_fix)
        elif lines <= q3:
            bins["Q3"].append(has_fix)
        else:
            bins["Q4"].append(has_fix)

    reporter.write(f"Cortes quartis (lines): Q1={q1:.2f}, Q2={q2:.2f}, Q3={q3:.2f}")
    for quartile in ["Q1", "Q2", "Q3", "Q4"]:
        values = bins[quartile]
        if not values:
            reporter.write(f"[{quartile}] sem dados")
            continue
        bug_rate = sum(1 for v in values if v) / len(values) * 100
        reporter.write(f"[{quartile}] commits={len(values)} | taxa bug-inducing={bug_rate:.2f}%")

    # Spearman: volume de linhas × é bug-inducing?
    all_lines = [v[0] for v in valid]
    all_bugs  = [1 if v[1] else 0 for v in valid]
    teste_pointbiserial(all_bugs, all_lines, "bug-inducing (binário) × real_lines_changed", reporter)
    reporter.write("")


# ==========================================================
# 2 - MÉTRICAS POR QUANTIDADE DE BICs
# ==========================================================
def calculate_avg_for_buggy_fixes(data, reporter):
    stats = defaultdict(lambda: {
        "complexity": [],
        "interfacing": [],
        "size": [],
        "real_lines_changed": [],
        "counter": 0,
    })

    all_complexity = []
    all_fix_counts = []

    complexity_bic = []
    complexity_no_bic = []

    for relation in data:
        fix_counts = len(relation.get("fixed_by", []))

        complexity   = safe_float(relation.get("dmm_unit_complexity"))
        interfacing  = safe_float(relation.get("dmm_unit_interfacing"))
        size         = safe_float(relation.get("dmm_unit_size"))
        real_lines   = relation.get("real_lines_changed")

        if complexity is not None:
            stats[fix_counts]["complexity"].append(complexity)
            all_complexity.append(complexity)
            all_fix_counts.append(fix_counts)

            if fix_counts > 0:
                complexity_bic.append(complexity)
            else:
                complexity_no_bic.append(complexity)

        if interfacing is not None:
            stats[fix_counts]["interfacing"].append(interfacing)
        if size is not None:
            stats[fix_counts]["size"].append(size)
        if real_lines is not None:
            stats[fix_counts]["real_lines_changed"].append(real_lines)
        stats[fix_counts]["counter"] += 1

    reporter.write("=== MÉTRICAS POR QUANTIDADE DE BICs ===")
    for fix_counts in sorted(stats.keys()):
        values = stats[fix_counts]
        if not (values["complexity"] or values["interfacing"] or values["size"]):
            continue

        reporter.write(f"\nCommits de correção diretos gerados: {fix_counts}")
        if values["complexity"]:
            reporter.write(f"  Média complexidade: {np.mean(values['complexity']):.4f}")
        if values["interfacing"]:
            reporter.write(f"  Média interfacing: {np.mean(values['interfacing']):.4f}")
        if values["size"]:
            reporter.write(f"  Média size: {np.mean(values['size']):.4f}")
        if values["real_lines_changed"]:
            reporter.write(f"  Média linhas reais alteradas: {np.mean(values['real_lines_changed']):.2f}")
        reporter.write(f"  Total de commits: {values['counter']}")

    # Correlação: complexidade → número de fixes gerados
    teste_spearman(all_complexity, all_fix_counts, "complexidade × quantidade de BICs", reporter)

    # Mann-Whitney: bug-inducing (fix>0) vs não bug-inducing
    teste_mann_whitney(complexity_bic, complexity_no_bic, "Complexidade: bug-inducing vs não bug-inducing", reporter)

    reporter.write("")

# ==========================================================
# 3 - EXPERIÊNCIA X RECORRÊNCIA
# ==========================================================
def calculate_experience_vs_recurrence(data, reporter):
    bins = {b: [] for b in ACTIVITY_BUCKETS}

    activities, fix_counts_all = [], []

    for relation in data:
        activity = relation.get("contributor_activity")
        count    = len(relation.get("fixed_by", []))

        activities.append(activity)
        bucket  = get_activity_bucket(activity)
        fix_counts_all.append(count)

        bins[bucket].append(count)

    reporter.write("=== EXPERIÊNCIA X RECORRÊNCIA (fixed_by > 1) ===")
    for bucket in ACTIVITY_BUCKETS:
        values = bins[bucket]
        if not values:
            reporter.write(f"[{bucket}] sem dados")
            continue
        recurrence = sum(1 for v in values if v > 1) / len(values) * 100
        reporter.write(
            f"[{bucket}] commits={len(values)} | taxa recorrência={recurrence:.2f}% | média fixed_by={np.mean(values):.3f}"
        )

    # Correlação: experiência do contribuidor × número de BICs
    teste_spearman(activities, fix_counts_all, "experiência do contribuidor × fixed_by", reporter)
    reporter.write("")

# ==========================================================
# 4 - COMPLEXIDADE X EXPERIÊNCIA DO CONTRIBUIDOR
# ==========================================================
def code_complexity_vs_contributor_experience(data, reporter):
    activities, complexities = [], []

    for relation in data:
        activity = relation.get("contributor_activity")
        complexity = safe_float(relation.get("dmm_unit_complexity"))

        if activity is not None and complexity is not None:
            activities.append(activity)
            complexities.append(complexity)

    reporter.write("=== EXPERIÊNCIA DO CONTRIBUIDOR X COMPLEXIDADE ===")
    teste_spearman(activities, complexities, "experiência do contribuidor × complexidade", reporter)
    reporter.write("")

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
        OUTPUT_PATH = f"./results/{FOLDER_REPO_PATH}/commit_analyses.txt"

        data = load_data(INPUT_PATH)

        if os.path.exists(OUTPUT_PATH):
            open(OUTPUT_PATH, "w").close()

        reporter = Reporter(OUTPUT_PATH)

        calculate_churn_risk_by_quartile_relations(data, reporter)
        calculate_avg_for_buggy_fixes(data, reporter)
        calculate_experience_vs_recurrence(data, reporter)
        code_complexity_vs_contributor_experience(data, reporter)
        print(f"Análises concluídas: {file} -> {OUTPUT_PATH}")