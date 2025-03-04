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

# Dicionário para armazenar a propagação geral
overall_propagation = defaultdict(int)

# Contar a propagação para todos os commits de correção
for record in data:
    fix_commit = record["bug_causer"]
    count_propagation_reverse(fix_commit, propagation_count=overall_propagation)

total_count = 0
total = 0
# Exibir os resultados gerais
print("Propagação reversa (onde as correções são apontadas como BIC):")
for depth, count in sorted(overall_propagation.items()):
    print(f"Nível {depth}: {count} vezes")
    total+= depth * count
    total_count += count

print("MÉDIA: ", total/total_count)