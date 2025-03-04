import json
from collections import defaultdict

# Carregar os dados JSON
with open('./relations/commit_path.json') as file:
    data = json.load(file)

# Criar um dicionário que mapeia fix_commit para seus "Fix in BIC"
fix_to_bic = defaultdict(list)
for record in data:
    fix_commit = record["bug_causer"]
    fix_in_bic = record["fixed_by"]
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

    # Contar o nível de propagação atual
    propagation_count[depth] += 1

    # Obter os commits onde o fix_commit foi BIC
    bics = fix_to_bic.get(fix_commit, [])

    # Recursão para os BICs encontrados
    for bic in bics:
        count_propagation_reverse(bic, depth + 1, propagation_count, visited)

    return propagation_count

# Função para rastrear o caminho completo de um commit específico
def trace_path(fix_commit, path=None, all_paths=None, visited=None):
    if path is None:
        path = [fix_commit]  # Inicia o caminho com o fix_commit atual
    if all_paths is None:
        all_paths = []  # Armazena todos os caminhos percorridos
    if visited is None:
        visited = set()  # Evitar ciclos

    # Evitar ciclos
    if fix_commit in visited:
        return all_paths

    visited.add(fix_commit)

    # Obter os commits onde o fix_commit foi BIC
    bics = fix_to_bic.get(fix_commit, [])

    # Caso base: quando não há mais BICs
    if not bics:
        all_paths.append(path)
        return all_paths

    # Recursão para cada BIC
    for bic in bics:
        trace_path(bic, path + [bic], all_paths, visited)

    return all_paths

# Função para calcular a profundidade média das cadeias de commits
def average_depth(all_paths):
    if not all_paths:
        return 0
    total_depth = sum(len(path) for path in all_paths)
    return total_depth / len(all_paths)

# Dicionário para armazenar a propagação geral
overall_propagation_expert = defaultdict(int)
overall_propagation_non_expert = defaultdict(int)

# Listas para armazenar os caminhos
expert_paths = []
non_expert_paths = []

# Contar a propagação para todos os commits de correção
for record in data:
    fix_commit = record["bug_causer"]
    contributor_activity = record["contributor_activity"]

    # Verifica se o contribuinte é experiente (contributor_activity > 50)
    if contributor_activity > 50:
        expert_paths.extend(trace_path(fix_commit))
        count_propagation_reverse(fix_commit, propagation_count=overall_propagation_expert)
    else:
        non_expert_paths.extend(trace_path(fix_commit))
        count_propagation_reverse(fix_commit, propagation_count=overall_propagation_non_expert)

# Calcular a profundidade média das cadeias de commits
avg_depth_expert = average_depth(expert_paths)
avg_depth_non_expert = average_depth(non_expert_paths)

# Exibir os resultados
print("Propagação reversa (onde as correções são apontadas como BIC):")
print("\nPara contribuintes experientes:")
# for depth, count in sorted(overall_propagation_expert.items()):
#     print(f"Nível {depth}: {count} vezes")
print(f"\nProfundidade média das cadeias de commits (experientes): {avg_depth_expert}")

print("\nPara contribuintes menos experientes:")
# for depth, count in sorted(overall_propagation_non_expert.items()):
#     print(f"Nível {depth}: {count} vezes")
print(f"\nProfundidade média das cadeias de commits (menos experientes): {avg_depth_non_expert}")

# Comparar as profundidades médias
if avg_depth_expert < avg_depth_non_expert:
    print("\nA cadeia de commits tende a ter uma menor dispersão de camadas quando realizada por contribuidores experientes.")
else:
    print("\nA cadeia de commits tende a ter uma menor dispersão de camadas quando realizada por contribuidores menos experientes.")
