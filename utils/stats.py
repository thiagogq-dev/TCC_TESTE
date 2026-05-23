from scipy.stats import mannwhitneyu, spearmanr, chi2_contingency, pointbiserialr, kruskal
from statsmodels.stats.multitest import multipletests
import numpy as np
from statistics import median

def aplicar_correcao_bh(resultados, reporter, label=""):
    """
    Aplica a correção de Benjamini-Hochberg (FDR) sobre uma família de testes.

    Parâmetros
    ----------
    resultados : list[dict]
        Lista de dicts com chaves 'label' e 'p'.
        Entradas com p=None (dados insuficientes) são ignoradas.
    reporter : Reporter
        Objeto de saída.
    label : str
        Nome da família de testes (ex: "tests_analyses").
    """
    validos = [r for r in resultados if r.get("p") is not None]

    if not validos:
        reporter.write(f"\n=== CORREÇÃO BH ({label}) === Sem testes válidos.\n")
        return

    labels = [r["label"] for r in validos]
    pvals  = [r["p"]     for r in validos]

    reject, pvals_corrigidos, _, _ = multipletests(pvals, method="fdr_bh", alpha=0.05)

    reporter.write(f"\n=== CORREÇÃO BH — {label} ===")
    reporter.write(
        f"  {len(validos)} testes submetidos à correção FDR (α=0.05, método Benjamini-Hochberg)"
    )
    for lbl, p_orig, p_corr, sig in zip(labels, pvals, pvals_corrigidos, reject):
        status = "SIGNIFICATIVO" if sig else "NÃO significativo"
        reporter.write(
            f"  {lbl}: p_orig={p_orig:.4f} → p_adj={p_corr:.4f} | {status}"
        )
    reporter.write("")


def teste_mann_whitney(grupo_a, grupo_b, label, reporter):
    """
    Testa se dois grupos independentes têm distribuições diferentes.
    Não assume normalidade — ideal para métricas de commits.
    H0: as distribuições são iguais.

    Retorna dict {"label", "p"} para correção BH posterior.
    """
    if len(grupo_a) < 2 or len(grupo_b) < 2:
        reporter.write(f"  [Mann-Whitney | {label}] Dados insuficientes.")
        return {"label": label, "p": None}

    stat, p = mannwhitneyu(grupo_a, grupo_b, alternative="two-sided")
    r, magnitude = rank_biserial(stat, len(grupo_a), len(grupo_b))

    reporter.write(
        f"  [Mann-Whitney | {label}] "
        f"U={stat:.2f} | p={p:.4f} | "
        f"effect size r={r:.4f} ({magnitude})"
    )
    return {"label": label, "p": p}


def rank_biserial(stat, n_a, n_b):
    """
    Effect size para Mann-Whitney.
    r próximo de 0 = efeito pequeno; ±0.3 = médio; ±0.5 = grande.
    """
    if n_a == 0 or n_b == 0:
        return 0.0, "indefinido"
    r = 1 - (2 * stat) / (n_a * n_b)

    magnitude = (
        "efeito pequeno" if abs(r) < 0.3 else
        "efeito médio"   if abs(r) < 0.5 else
        "efeito grande"
    )
    return r, magnitude


def teste_chi2(tabela, label, reporter):
    """
    Testa associação entre duas variáveis categóricas.
    Reporta χ², p bruto e Cramér's V como effect size.

    Retorna dict {"label", "p"} para correção BH posterior.
    """
    try:
        chi2, p, dof, expected = chi2_contingency(tabela)

        n = np.sum(tabela)
        cramers_v = np.sqrt(chi2 / (n * (min(len(tabela), len(tabela[0])) - 1))) if n > 0 else 0

        magnitude = (
            "efeito desprezível" if cramers_v < 0.1 else
            "efeito pequeno"     if cramers_v < 0.3 else
            "efeito médio"       if cramers_v < 0.5 else
            "efeito grande"
        )  

        reporter.write(
            f"  [Chi-quadrado | {label}] "
            f"χ²={chi2:.4f} | gl={dof} | p={p:.4f} | "
            f"Cramér's V={cramers_v:.4f} | {magnitude}"
        )

        return {"label": label, "p": p}
    except Exception as e:
        reporter.write(f"  [Chi-quadrado | {label}] Erro: {e}")
        return {"label": label, "p": None}

def teste_spearman(lista_x, lista_y, label, reporter):
    """
    Mede correlação monotônica entre duas variáveis contínuas/ordinais.
    H0: não há correlação.

    Retorna dict {"label", "p"} para correção BH posterior.
    """
    if len(lista_x) < 3 or len(lista_y) < 3:
        reporter.write(f"  [Spearman | {label}] Dados insuficientes.")
        return {"label": label, "p": None}

    corr, p = spearmanr(lista_x, lista_y)

    magnitude = (
        "correlação fraca"   if abs(corr) < 0.3 else
        "correlação moderada" if abs(corr) < 0.5 else
        "correlação forte"
    )

    reporter.write(
        f"  [Spearman | {label}] "
        f"p={p:.4f} | r={corr:.4f} | {magnitude}"
    )
    return {"label": label, "p": p}


def teste_pointbiserial(lista_binaria, lista_continua, label, reporter):
    """
    Mede correlação entre uma variável binária e uma contínua.
    H0: não há correlação.

    Retorna dict {"label", "p"} para correção BH posterior.
    """
    if len(lista_binaria) < 3 or len(lista_continua) < 3:
        reporter.write(f"  [Point-Biserial | {label}] Dados insuficientes.")
        return {"label": label, "p": None}

    corr, p = pointbiserialr(lista_binaria, lista_continua)

    magnitude = (
        "correlação fraca"   if abs(corr) < 0.3 else
        "correlação moderada" if abs(corr) < 0.5 else
        "correlação forte"
    )

    reporter.write(
        f"  [Point-Biserial | {label}] "
        f"p={p:.4f} | r={corr:.4f} | {magnitude}"
    )
    return {"label": label, "p": p}


def teste_kruskal(grupos_dict, label, reporter):
    """
    Testa se há diferença entre 3 ou mais grupos independentes.
    Calcula épsilon² como effect size.

    Retorna dict {"label", "p"} para correção BH posterior.
    """
    
    grupos = [v for v in grupos_dict.values() if len(v) >= 2]
    if len(grupos) < 2:
        reporter.write(f"  [Kruskal-Wallis | {label}] Grupos insuficientes.")
        return {"label": label, "p": None}

    stat, p = kruskal(*grupos)
    
    # Calcula épsilon² como effect size
    n = sum(len(g) for g in grupos)
    epsilon_sq = (stat - len(grupos) + 1) / (n - len(grupos))
    epsilon_sq = max(0, epsilon_sq)  # não pode ser negativo
    
    magnitude = (
        "efeito pequeno" if epsilon_sq < 0.01 else
        "efeito médio"   if epsilon_sq < 0.06 else
        "efeito grande"
    )
    
    reporter.write(
        f"  [Kruskal-Wallis | {label}] "
        f"H={stat:.4f} | p={p:.4f} | ε²={epsilon_sq:.4f} ({magnitude})"
    )
    return {"label": label, "p": p}