import json
from collections import defaultdict

# Carregar os dados JSON
with open('./relations/commit_path.json') as file:
    data = json.load(file)

# Criar um dicionário que mapeia fix_commit para seus "Fix in BIC"
fix_to_bic = defaultdict(list)
has_tests_map = {}

for record in data:
    fix_commit = record["bug_causer"]
    fix_in_bic = record["fixed_by"]
    fix_to_bic[fix_commit].extend(fix_in_bic)
    has_tests_map[fix_commit] = record["has_tests"]  # Mapeia se tem teste ou não

# Função para contar propagação reversa e localização de commits com testes
def count_propagation_reverse_with_tests(fix_commit, depth=1, propagation_count=None, visited=None, commits_with_tests=None, paths=None):
    if propagation_count is None:
        propagation_count = defaultdict(int)
    if visited is None:
        visited = set()
    if commits_with_tests is None:
        commits_with_tests = {"inicio": 0, "meio": 0, "fim": 0}
    if paths is None:
        paths = []  # Lista para armazenar todos os caminhos

    # Evitar ciclos
    if fix_commit in visited:
        return propagation_count, commits_with_tests, paths

    visited.add(fix_commit)
    
    # Atualizar contagem de propagação
    propagation_count[depth] += 1

    # Verificar se o commit tem testes
    if has_tests_map.get(fix_commit) == "Yes":
        paths.append((fix_commit, depth))  # Salvar commit com teste e sua profundidade

    # Obter os commits onde o fix_commit foi BIC
    bics = fix_to_bic.get(fix_commit, [])

    # Caso base: quando não há mais BICs
    if not bics:
        return propagation_count, commits_with_tests, paths

    # Recursão para os BICs encontrados
    for bic in bics:
        count_propagation_reverse_with_tests(bic, depth + 1, propagation_count, visited, commits_with_tests, paths)

    return propagation_count, commits_with_tests, paths

# Dicionário para armazenar a propagação geral e commits com testes
overall_propagation = defaultdict(int)
all_paths = []

# Contar a propagação para todos os commits de correção
for record in data:
    fix_commit = record["bug_causer"]
    propagation_count, commits_with_tests, paths = count_propagation_reverse_with_tests(fix_commit, propagation_count=overall_propagation)

    # Adicionar caminhos de commits com testes à lista geral
    all_paths.extend(paths)

# Descobrir a localização relativa dos commits com testes
total_depths = [depth for _, depth in all_paths]
if total_depths:
    threshold_early = min(total_depths) + (max(total_depths) - min(total_depths)) * 0.33
    threshold_mid = min(total_depths) + (max(total_depths) - min(total_depths)) * 0.66
else:
    threshold_early, threshold_mid = 9, 18  # Valores padrão

commits_with_tests = {"inicio": 0, "meio": 0, "fim": 0}

for _, depth in all_paths:
    if depth <= threshold_early:
        commits_with_tests["inicio"] += 1
    elif depth <= threshold_mid:
        commits_with_tests["meio"] += 1
    else:
        commits_with_tests["fim"] += 1

# Exibir os resultados gerais de propagação
# print("Propagação reversa (onde as correções são apontadas como BIC):")
# for depth, count in sorted(overall_propagation.items()):
#     print(f"Nível {depth}: {count} vezes")

# Exibir os resultados sobre os commits com testes
print("\nPosição dos commits com testes:")
print(f"Commits no início da cadeia: {commits_with_tests['inicio']}")
print(f"Commits no meio da cadeia: {commits_with_tests['meio']}")
print(f"Commits no fim da cadeia: {commits_with_tests['fim']}")
