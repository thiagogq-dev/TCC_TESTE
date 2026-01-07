import json
from datetime import timedelta
from statistics import mode, mean
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import os
from utils.utils import (
    preload_commits_index,
    get_commit_date_from_index,
    get_contributor_activity_from_index,
)

REPO_PATH = "repos_dir/jabref"

# -----------------------------
# Pré-carregar commits usando utilitário compartilhado
# -----------------------------
commit_date, author_commits = preload_commits_index(REPO_PATH)

def get_commit_date(fix_commit):
    return get_commit_date_from_index(fix_commit, commit_date)

def get_contributor_activity(author, fix_date):
    return get_contributor_activity_from_index(author, fix_date, author_commits)

# -----------------------------
# Análise
# -----------------------------
qtde_commits = []
analyses = defaultdict(int)

with open("./data/issues.json") as f:
    data = json.load(f)
    for record in data:
        if record["has_tests"] == "Yes":
            fix_commit = record["fix_commit_hash"]
            author = record["commit_author"]

            if fix_commit not in commit_date:
                continue

            fix_date = get_commit_date(fix_commit)
            activity = get_contributor_activity(author, fix_date)

            analyses[activity] += 1
            qtde_commits.append(activity)

# -----------------------------
# Estatísticas básicas
# -----------------------------
print("Moda:", mode(qtde_commits))
print("Média:", mean(qtde_commits))
print("Total analisado:", len(qtde_commits))

if not os.path.exists("./charts"):
    os.makedirs("./charts")
# -----------------------------
# Preparar dados para gráficos
# -----------------------------
activity = sorted(analyses.keys())
counts = np.array([analyses[a] for a in activity])

total = counts.sum()
cumulative = np.cumsum(counts) / total

# recriar dados "crus" para boxplot
raw_data = np.repeat(activity, counts)

# -----------------------------
# Gráfico 1 — Barras
# -----------------------------
plt.figure(figsize=(10, 5))
plt.bar(activity, counts)
plt.xlabel("Número de commits anteriores do autor")
plt.ylabel("Quantidade de fixes com testes")
plt.title("Distribuição da atividade dos autores (barras)")
plt.tight_layout()
plt.savefig("./charts/contributor_activity_bar.png")
# plt.show()

# -----------------------------
# Gráfico 2 — CDF (acumulado)
# -----------------------------
plt.figure(figsize=(10, 5))
plt.plot(activity, cumulative, marker="o")
plt.xlabel("Número de commits anteriores do autor")
plt.ylabel("Proporção acumulada")
plt.title("Distribuição acumulada da experiência dos autores")
plt.grid(True)
plt.tight_layout()
plt.savefig("./charts/contributor_activity_cdf.png")
# plt.show()

# -----------------------------
# Gráfico 3 — Boxplot
# -----------------------------
plt.figure(figsize=(6, 4))
plt.boxplot(raw_data, vert=False)
plt.xlabel("Número de commits anteriores do autor")
plt.title("Resumo estatístico da atividade dos autores")
plt.tight_layout()
plt.savefig("./charts/contributor_activity_boxplot.png")
