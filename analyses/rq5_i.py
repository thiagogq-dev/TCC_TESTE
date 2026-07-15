import os
import numpy as np
from collections import defaultdict # <-- Adicionado
from utils.utils import safe_float, load_data, get_activity_bucket, Reporter, ACTIVITY_BUCKETS, preprocess_raw_data
from utils.stats import (
    teste_chi2, teste_spearman,
    aplicar_correcao_bh, teste_pointbiserial
)

def calculate_proportion_bugs_asserts_types(data, reporter):
    """
    Calcula a proporção de commits que introduziram bugs (fixed_by) em relação aos tipos de alterações em asserts (Added, Removed, Maintained, None).
    Realiza teste estatístico (Chi²) para verificar associação entre tipo de alteração em asserts e introdução de bugs.
    Args:
        data (list): Lista de registros de commits.
        reporter (Reporter): Instância de Reporter para registrar resultados.
    Returns:
        dict: Resultado do teste Chi² com correção BH.
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
    Analisa a proporção de commits que introduziram bugs (fixed_by) em relação à experiência do contribuidor.   
    Realiza teste estatístico (Spearman) para verificar associação entre experiência e recorrência de bugs.
    Args:
        data (list): Lista de registros de commits.
        reporter (Reporter): Instância de Reporter para registrar resultados.
    Returns:
        dict: Resultado do teste Spearman com correção BH.
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
    Analisa a correlação entre a complexidade do código (dmm_unit_complexity) e a experiência do contribuidor (contributor_activity).
    Realiza teste estatístico (Spearman) para verificar associação entre complexidade e experiência.
    Args:
        data (list): Lista de registros de commits.
        reporter (Reporter): Instância de Reporter para registrar resultados.
    Returns:
        dict: Resultado do teste Spearman com correção BH.
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

if __name__ == "__main__":
    os.makedirs("./results/rq5_i", exist_ok=True)
    import pandas as pd 

    OUTPUT_TEXT_PATH = "./results/rq5_i/relatorio_texto.txt"
    OUTPUT_CSV_PATH = "./results/rq5_i/tabela_resultados.csv"

    if os.path.exists(OUTPUT_TEXT_PATH):
        open(OUTPUT_TEXT_PATH, "w").close()

    reporter = Reporter(OUTPUT_TEXT_PATH)
    
    dados_tabela = []

    for file in sorted(os.listdir("./dataset/4-metricas/with_bic")):
        if not file.endswith(".json"):
            continue

        FOLDER_REPO_PATH = file.replace(".json", "")
        INPUT_PATH      = f"./dataset/4-metricas/with_bic/{file}" # MUDANÇA: Caminho corrigido

        # MUDANÇA: Processando os dados nativos
        raw_data = load_data(INPUT_PATH)
        data = preprocess_raw_data(raw_data)

        reporter.write("RQ5 (i): Análise de fatores que afetam a presença de bugs\n")
        reporter.write("\n" + "="*80)
        reporter.write(f"PROJETO: {FOLDER_REPO_PATH}\n\n")
        reporter.write("="*80 + "\n")

        linha_projeto = {"Projeto": FOLDER_REPO_PATH}
        pvalores = []

        r1 = calculate_proportion_bugs_asserts_types(data, reporter)
        pvalores.append(r1)

        r2 = calculate_experience_vs_recurrence(data, reporter)
        pvalores.append(r2)

        r3 = code_complexity_vs_contributor_experience(data, reporter)
        pvalores.append(r3)

        for resultado in pvalores:
            if resultado is not None and "label" in resultado:
                nome_coluna = resultado["label"]
                valor_p = resultado.get("p")
                
                if isinstance(valor_p, float):
                    linha_projeto[f"{nome_coluna} (p-value)"] = round(valor_p, 4)
                else:
                    linha_projeto[f"{nome_coluna} (p-value)"] = valor_p

        aplicar_correcao_bh(pvalores, reporter, label="RQ5 (i)")

        dados_tabela.append(linha_projeto)
        print(f"Processado RQ5_i: {file}")

    if dados_tabela:
        df_resultados = pd.DataFrame(dados_tabela)
        df_resultados.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8')