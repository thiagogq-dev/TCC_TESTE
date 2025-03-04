import json
from collections import defaultdict

# Carregar os dados JSON
with open('./relations/commit_path.json') as file:
    data = json.load(file)

# Criar um dicionário que mapeia fix_commit para seus "Fix in BIC"
fix_to_bic = defaultdict(list)
has_tests_map = {}  # Mapeia commit -> se tem testes ou não

for record in data:
    fix_commit = record["bug_causer"]
    fix_in_bic = record["fixed_by"]
    has_tests_map[fix_commit] = record["has_tests"] == "Yes"
    fix_to_bic[fix_commit].extend(fix_in_bic)

# Função para contar a propagação separando caminhos com e sem testes
def count_propagation_separated(fix_commit, depth=1, propagation_with_tests=None, propagation_without_tests=None, visited=None, has_tests_in_path=False):
    if propagation_with_tests is None:
        propagation_with_tests = defaultdict(int)
    if propagation_without_tests is None:
        propagation_without_tests = defaultdict(int)
    if visited is None:
        visited = set()

    # Evitar ciclos
    if fix_commit in visited:
        return propagation_with_tests, propagation_without_tests

    visited.add(fix_commit)

    # Atualizar se esse commit tem testes
    if has_tests_map.get(fix_commit, False):
        has_tests_in_path = True

    # Contar a propagação no grupo correspondente
    if has_tests_in_path:
        propagation_with_tests[depth] += 1
    else:
        propagation_without_tests[depth] += 1

    # Obter os commits onde o fix_commit foi BIC
    bics = fix_to_bic.get(fix_commit, [])

    # Recursão para os BICs encontrados
    for bic in bics:
        count_propagation_separated(bic, depth + 1, propagation_with_tests, propagation_without_tests, visited, has_tests_in_path)

    return propagation_with_tests, propagation_without_tests

# Dicionários para armazenar a propagação separada
propagation_with_tests = defaultdict(int)
propagation_without_tests = defaultdict(int)

# Contar a propagação para todos os commits de correção
for record in data:
    fix_commit = record["bug_causer"]
    count_propagation_separated(fix_commit, propagation_with_tests=propagation_with_tests, propagation_without_tests=propagation_without_tests)

# Exibir os resultados gerais de propagação
print("Propagação para caminhos COM commits de teste:")
for depth, count in sorted(propagation_with_tests.items()):
    print(f"Nível {depth}: {count} vezes")

print("\nPropagação para caminhos SEM commits de teste:")
for depth, count in sorted(propagation_without_tests.items()):
    print(f"Nível {depth}: {count} vezes")
