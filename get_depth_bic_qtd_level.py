import json
from collections import defaultdict

qtd_level_bic = {}

# Carregar os dados JSON
with open('./relations/commit_path.json') as file:
    data = json.load(file)

# Criar um dicionário que mapeia fix_commit para seus "Fix in BIC"
fix_to_bic = defaultdict(list)
for record in data:
    fix_commit = record["bug_causer"]
    fix_in_bic = record["fixed_by"]
    if fix_in_bic:  # Apenas considerar commits que foram BIC
        fix_to_bic[fix_commit].extend(fix_in_bic)

# Função para contar a propagação

def count_propagation_reverse(fix_commit, depth=1, propagation_count=None, visited=None):
    if propagation_count is None:
        propagation_count = defaultdict(int)
    if visited is None:
        visited = set()

    # Evitar ciclos
    if fix_commit in visited:
        return propagation_count

    visited.add(fix_commit)

    # Obter os commits onde o fix_commit foi BIC
    bics = fix_to_bic.get(fix_commit, [])
    if not bics:
        return propagation_count

    # Contar o nível de propagação atual
    propagation_count[depth] += 1

    # Recursão para os BICs encontrados
    for bic in bics:
        count_propagation_reverse(bic, depth + 1, propagation_count, visited)

    return propagation_count

# Dicionário para armazenar a propagação geral considerando apenas commits que foram BIC
overall_propagation = defaultdict(int)

# Contar a propagação para todos os commits que são BIC
for record in data:
    fix_commit = record["bug_causer"]
    if fix_to_bic.get(fix_commit):  # Garantir que o commit foi um BIC
        count_propagation_reverse(fix_commit, propagation_count=overall_propagation)

total_count = 0
total = 0
# Exibir os resultados gerais considerando apenas commits que foram BIC
print("Propagação reversa (apenas commits que foram BIC):")
for depth, count in sorted(overall_propagation.items()):
    print(f"Nível {depth}: {count} vezes")
    total += depth * count
    total_count += count
    qtd_level_bic[depth] = count

if total_count > 0:
    print("MÉDIA: ", total / total_count)
else:
    print("Nenhum commit foi BIC.")


import matplotlib.pyplot as plt


# Separar os níveis e os valores para o gráfico
levels = list(qtd_level_bic.keys())
counts = list(qtd_level_bic.values())

# Criar o gráfico de barras
plt.figure(figsize=(10, 5))
plt.bar(levels, counts, color='blue', alpha=0.7)

# Adicionar títulos e rótulos
plt.xlabel("Nível de Propagação")
plt.ylabel("Quantidade de BICs")
plt.title("Histograma da Contagem de BICs por Nível")
plt.xticks(levels)  # Garantir que os níveis apareçam corretamente no eixo X
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Exibir o gráfico
plt.savefig("histograma_bics.png")
print("Gráfico salvo como 'histograma_bics.png'. Abra o arquivo para visualizar.")

