import json
from collections import defaultdict

# Carregar os dados JSON
with open('./relations/commit_path.json') as file:
    data = json.load(file)

# Criar um dicionário que mapeia fix_commit para seus "Fix in BIC"
fix_to_bic = defaultdict(list)
commit_metrics = {}

for record in data:
    fix_commit = record["bug_causer"]
    fix_in_bic = record["fixed_by"]
    fix_to_bic[fix_commit].extend(fix_in_bic)
    
    # Armazena métricas
    commit_metrics[fix_commit] = {
        "dmm_unit_size": record["dmm_unit_size"],
        "dmm_unit_complexity": record["dmm_unit_complexity"],
        "dmm_unit_interfacing": record["dmm_unit_interfacing"]
    }

# Função para contar a propagação e calcular métricas por nível
def count_propagation_reverse(fix_commit, depth=1, propagation_count=None, metrics_sum=None, metrics_count=None, visited=None):
    if propagation_count is None:
        propagation_count = defaultdict(int)
    if metrics_sum is None:
        metrics_sum = defaultdict(lambda: {"dmm_unit_size": 0, "dmm_unit_complexity": 0, "dmm_unit_interfacing": 0})
    if metrics_count is None:
        metrics_count = defaultdict(lambda: {"dmm_unit_size": 0, "dmm_unit_complexity": 0, "dmm_unit_interfacing": 0})
    if visited is None:
        visited = set()

    # Evitar ciclos
    if fix_commit in visited:
        return propagation_count, metrics_sum, metrics_count

    visited.add(fix_commit)
    propagation_count[depth] += 1

    # Adicionar métricas do commit
    metrics = commit_metrics.get(fix_commit, {})
    for key in ["dmm_unit_size", "dmm_unit_complexity", "dmm_unit_interfacing"]:
        if metrics.get(key) is not None:
            metrics_sum[depth][key] += metrics[key]
            metrics_count[depth][key] += 1

    # Obter os commits onde o fix_commit foi BIC
    bics = fix_to_bic.get(fix_commit, [])

    # Recursão para os BICs encontrados
    for bic in bics:
        count_propagation_reverse(bic, depth + 1, propagation_count, metrics_sum, metrics_count, visited)

    return propagation_count, metrics_sum, metrics_count

# Dicionários para armazenar a propagação e as métricas gerais
overall_propagation = defaultdict(int)
overall_metrics_sum = defaultdict(lambda: {"dmm_unit_size": 0, "dmm_unit_complexity": 0, "dmm_unit_interfacing": 0})
overall_metrics_count = defaultdict(lambda: {"dmm_unit_size": 0, "dmm_unit_complexity": 0, "dmm_unit_interfacing": 0})

# Contar a propagação para todos os commits de correção
for record in data:
    fix_commit = record["bug_causer"]
    count_propagation_reverse(fix_commit, propagation_count=overall_propagation, metrics_sum=overall_metrics_sum, metrics_count=overall_metrics_count)

# Exibir os resultados gerais
print("Propagação reversa e médias das métricas por nível:")
for depth in sorted(overall_propagation.keys()):
    print(f"Nível {depth}: {overall_propagation[depth]} vezes")
    
    for key in ["dmm_unit_size", "dmm_unit_complexity", "dmm_unit_interfacing"]:
        if overall_metrics_count[depth][key] > 0:
            avg = overall_metrics_sum[depth][key] / overall_metrics_count[depth][key]
            print(f"  Média {key}: {avg:.4f}")
        else:
            print(f"  Média {key}: N/A")
