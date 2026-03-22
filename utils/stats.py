from scipy.stats import mannwhitneyu, spearmanr, chi2_contingency, pointbiserialr, kruskal
import numpy as np
from statistics import median

def describe_distribution(values):
    if not values:
        return None

    values = sorted(values)
    return {
        "min": min(values),
        "max": max(values),
        "mean": float(np.mean(values)),
        "median": float(median(values)),
        "std": float(np.std(values)),
        "p90": float(np.percentile(values, 90)),
    }

def teste_mann_whitney(grupo_a, grupo_b, label, reporter):
    """
    Testa se dois grupos independentes têm distribuições diferentes.
    Não assume normalidade — ideal para métricas de commits.
    H0: as distribuições são iguais.
    """
    if len(grupo_a) < 2 or len(grupo_b) < 2:
        reporter.write(f"  [Mann-Whitney | {label}] Dados insuficientes.")
        return

    stat, p = mannwhitneyu(grupo_a, grupo_b, alternative="two-sided")
    significativo = "SIGNIFICATIVO" if p < 0.05 else "NÃO significativo"

    r, magnitude = rank_biserial(stat, len(grupo_a), len(grupo_b))

    reporter.write(
        f"  [Mann-Whitney | {label}] "
        f"U={stat:.2f} | p={p:.4f} | {significativo} | "
        f"effect size r={r:.4f} ({magnitude})"
    )


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


def teste_chi2(tabela_2x2, label, reporter):
    """
    Testa associação entre duas variáveis categóricas.
    """
    try:
        chi2, p, dof, expected = chi2_contingency(tabela_2x2)
        significativo = "SIGNIFICATIVO" if p < 0.05 else "NÃO significativo"
        reporter.write(
            f"  [Chi-quadrado | {label}] "
            f"χ²={chi2:.4f} | gl={dof} | p={p:.4f} | {significativo}"
        )
    except Exception as e:
        reporter.write(f"  [Chi-quadrado | {label}] Erro: {e}")


def teste_spearman(lista_x, lista_y, label, reporter):
    """
    Mede correlação monotônica entre duas variáveis contínuas/ordinais.
    H0: não há correlação.
    """
    if len(lista_x) < 3 or len(lista_y) < 3:
        reporter.write(f"  [Spearman | {label}] Dados insuficientes.")
        return

    corr, p = spearmanr(lista_x, lista_y)
    significativo = "SIGNIFICATIVO" if p < 0.05 else "NÃO significativo"

    magnitude = (
        "correlação fraca"   if abs(corr) < 0.3 else
        "correlação moderada" if abs(corr) < 0.5 else
        "correlação forte"
    )

    reporter.write(
        f"  [Spearman | {label}] "
        f"r={corr:.4f} | p={p:.4f} | {significativo} | {magnitude}"
    )

def teste_pointbiserial(lista_binaria, lista_continua, label, reporter):
    """
    Mede correlação entre uma variável binária e uma contínua.
    H0: não há correlação.
    """
    if len(lista_binaria) < 3 or len(lista_continua) < 3:
        reporter.write(f"  [Point-Biserial | {label}] Dados insuficientes.")
        return

    corr, p = pointbiserialr(lista_binaria, lista_continua)
    significativo = "SIGNIFICATIVO" if p < 0.05 else "NÃO significativo"

    magnitude = (
        "correlação fraca"   if abs(corr) < 0.3 else
        "correlação moderada" if abs(corr) < 0.5 else
        "correlação forte"
    )

    reporter.write(
        f"  [Point-Biserial | {label}] "
        f"r={corr:.4f} | p={p:.4f} | {significativo} | {magnitude}"
    )


def teste_kruskal(grupos_dict, label, reporter):
    """Testa se há diferença entre 3 ou mais grupos independentes.
    """
    grupos = [v for v in grupos_dict.values() if len(v) >= 2]
    if len(grupos) < 2:
        reporter.write(f"  [Kruskal-Wallis | {label}] Grupos insuficientes.")
        return
    stat, p = kruskal(*grupos)
    sig = "SIGNIFICATIVO" if p < 0.05 else "NÃO significativo"
    reporter.write(f"  [Kruskal-Wallis | {label}] H={stat:.4f} | p={p:.4f} | {sig}")