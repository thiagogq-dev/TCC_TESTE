import os
import numpy as np
from utils.utils import safe_float, load_data, get_activity_bucket, Reporter, ACTIVITY_BUCKETS
from utils.stats import (
    teste_chi2, teste_spearman,
    aplicar_correcao_bh, teste_pointbiserial
)

def calculate_proportion_bugs_asserts_types(data, reporter):
    """
    Calcula a proporção de commits que introduziram bugs, comparando tipos de mudança nos asserts (adição, remoção, sem mudança).

    Retorna lista de dicts {"label", "p"} para correção BH.
    """
    no_caused_bug_with_weaker_tests = 0
    no_caused_bug_with_stronger_tests = 0
    no_caused_bug_with_equal_tests = 0
    no_caused_bug_with_no_tests = 0

    caused_bug_with_weaker_tests = 0
    caused_bug_with_stronger_tests = 0
    caused_bug_with_equal_tests = 0
    caused_bug_with_no_tests = 0

    for relation in data:
        has_fix = len(relation.get("fixed_by", [])) > 0

        if has_fix:
            if relation.get("asserts_changes_type") == "Removed":
                caused_bug_with_weaker_tests += 1
            elif relation.get("asserts_changes_type") == "Added":
                caused_bug_with_stronger_tests += 1
            elif relation.get("asserts_changes_type") == "Maintained":
                caused_bug_with_equal_tests += 1
            elif relation.get("asserts_changes_type") == "None":
                caused_bug_with_no_tests += 1
        else:
            if relation.get("asserts_changes_type") == "Removed":
                no_caused_bug_with_weaker_tests += 1
            elif relation.get("asserts_changes_type") == "Added":
                no_caused_bug_with_stronger_tests += 1
            elif relation.get("asserts_changes_type") == "Maintained":
                no_caused_bug_with_equal_tests += 1
            elif relation.get("asserts_changes_type") == "None":
                no_caused_bug_with_no_tests += 1

    reporter.write("=== BUGS INTRODUZIDOS ===")
    reporter.write(f"Com asserts enfraquecidos que introduziram bugs {caused_bug_with_weaker_tests}")
    reporter.write(f"Com asserts fortalecidos que introduziram bugs {caused_bug_with_stronger_tests}")
    reporter.write(f"Com manutenção de asserts que introduziram bugs: {caused_bug_with_equal_tests}")
    reporter.write(f"Com ausência de asserts que introduziram bugs: {caused_bug_with_no_tests}")

    reporter.write(f"Com asserts enfraquecidos que NÃO introduziram bugs {no_caused_bug_with_weaker_tests}")
    reporter.write(f"Com asserts fortalecidos que NÃO introduziram bugs {no_caused_bug_with_stronger_tests}")
    reporter.write(f"Com manutenção de asserts que NÃO introduziram bugs {no_caused_bug_with_equal_tests}")
    reporter.write(f"Com ausência de asserts que NÃO introduziram bugs {no_caused_bug_with_no_tests}")

    tabela = [
        [caused_bug_with_weaker_tests, no_caused_bug_with_weaker_tests],
        [caused_bug_with_stronger_tests, no_caused_bug_with_stronger_tests],
        [caused_bug_with_equal_tests, no_caused_bug_with_equal_tests],
        [caused_bug_with_no_tests, no_caused_bug_with_no_tests]
    ]

    result = teste_chi2(tabela, "tipo de mudança de assert × introdução de bug", reporter)
    reporter.write("")
    return result

def calculate_experience_vs_recurrence(data, reporter):
    """
    Analisa a taxa de recorrência de bugs por faixa de experiência do contribuidor.

    Retorna dict {"label", "p"} do teste Spearman para correção BH.
    """
    bins = {b: [] for b in ACTIVITY_BUCKETS}
    activities, fix_counts_all = [], []

    for relation in data:
        activity = relation.get("contributor_activity")
        count = len(relation.get("fixed_by", []))
        activities.append(activity)
        bucket = get_activity_bucket(activity)
        fix_counts_all.append(count)
        bins[bucket].append(count)

    reporter.write("=== EXPERIÊNCIA X NECESSIDADE DE CORREÇÃO ===")
    for bucket in ACTIVITY_BUCKETS:
        values = bins[bucket]
        if not values:
            reporter.write(f"[{bucket}] sem dados")
            continue
        recurrence = sum(1 for v in values if v > 1) / len(values) * 100
        reporter.write(
            f"[{bucket}] commits={len(values)} | taxa recorrência={recurrence:.2f}% | média fixed_by={np.mean(values):.3f}"
        )

    result = teste_spearman(activities, fix_counts_all, "experiência do contribuidor × fixed_by", reporter)
    reporter.write("")
    return result


def code_complexity_vs_contributor_experience(data, reporter):
    """
    Correlaciona experiência do contribuidor com complexidade do código.

    Retorna dict {"label", "p"} do teste Spearman para correção BH.
    """
    activities, complexities = [], []

    for relation in data:
        activity   = relation.get("contributor_activity")
        complexity = safe_float(relation.get("dmm_unit_complexity"))
        if activity is not None and complexity is not None:
            activities.append(activity)
            complexities.append(complexity)

    reporter.write("=== EXPERIÊNCIA DO CONTRIBUIDOR X COMPLEXIDADE ===")
    result = teste_spearman(activities, complexities, "experiência do contribuidor × complexidade", reporter)
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
        OUTPUT_PATH     = f"{RESULTS_FOLDER}/rq5_i.txt"

        data = load_data(INPUT_PATH)

        if os.path.exists(OUTPUT_PATH):
            open(OUTPUT_PATH, "w").close()

        reporter = Reporter(OUTPUT_PATH)

        reporter.write(f"{FOLDER_REPO_PATH}")
        reporter.write("RQ5 (i): Análise de fatores que pssam a presenã de bugs\n")

        pvalores = []

        r = calculate_proportion_bugs_asserts_types(data, reporter)
        pvalores.append(r)

        r = calculate_experience_vs_recurrence(data, reporter)
        pvalores.append(r)

        r = code_complexity_vs_contributor_experience(data, reporter)
        pvalores.append(r)

        # --- correção BH sobre toda a família tests_analyses ---
        aplicar_correcao_bh(pvalores, reporter, label="RQ5 (i)")

        print(f"Análises concluídas: {file} -> {OUTPUT_PATH}")