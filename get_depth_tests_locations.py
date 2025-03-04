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

# Função para contar a propagação reversa e identificar commits com testes
def count_propagation_reverse_with_tests(fix_commit, depth=1, propagation_count=None, visited=None, commits_with_tests=None):
    if propagation_count is None:
        propagation_count = defaultdict(int)
    if visited is None:
        visited = set()
    if commits_with_tests is None:
        commits_with_tests = {"inicio": 0, "meio": 0, "fim": 0}

    # Evitar ciclos
    if fix_commit in visited:
        return propagation_count, commits_with_tests

    visited.add(fix_commit)

    # Contar o nível de propagação atual
    propagation_count[depth] += 1

    # Verificar se o commit tem testes
    for record in data:
        if record["bug_causer"] == fix_commit:
            has_tests = record["has_tests"]
            if has_tests == "Yes":
                # Classificar o commit com base na profundidade
                if depth <= 28:
                    commits_with_tests["inicio"] += 1
                elif depth <= 56:
                    commits_with_tests["meio"] += 1
                else:
                    commits_with_tests["fim"] += 1

    # Obter os commits onde o fix_commit foi BIC
    bics = fix_to_bic.get(fix_commit, [])

    # Recursão para os BICs encontrados
    for bic in bics:
        count_propagation_reverse_with_tests(bic, depth + 1, propagation_count, visited, commits_with_tests)

    return propagation_count, commits_with_tests

# Dicionário para armazenar a propagação geral e commits com testes
overall_propagation = defaultdict(int)
commits_with_tests = {"inicio": 0, "meio": 0, "fim": 0}

# Contar a propagação para todos os commits de correção
for record in data:
    fix_commit = record["bug_causer"]  # "fix_commit" não está definido no seu JSON, então usei "bug_causer"
    propagation_count, commits_with_tests = count_propagation_reverse_with_tests(fix_commit, propagation_count=overall_propagation, commits_with_tests=commits_with_tests)

# Exibir os resultados gerais de propagação
# print("Propagação reversa (onde as correções são apontadas como BIC):")
# for depth, count in sorted(overall_propagation.items()):
#     print(f"Nível {depth}: {count} vezes")

# Exibir os resultados sobre os commits com testes
print("\nPosição dos commits com testes:")
print(f"Commits no início da cadeia: {commits_with_tests['inicio']}")
print(f"Commits no meio da cadeia: {commits_with_tests['meio']}")
print(f"Commits no fim da cadeia: {commits_with_tests['fim']}")
