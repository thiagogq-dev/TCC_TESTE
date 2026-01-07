"""
Define o bug inducing commit (BIC) final e adiciona métricas dos commits de correção no arquivo JSON de issues.
"""
from utils.utils import get_commit_data, define_bic, group_file_by_fix
import json

new_data = []

with open("data/issues.json", "r") as f:
    data = json.load(f)
    tam = len(data)
    for index, d in enumerate(data):
        print(f"Processando issue {index + 1} de {tam}")
        rszz = d.pop("inducing_commit_hash_pyszz", [])
        pdszz = d.pop("inducing_commit_hash_pd", [])
        d["bic"] = define_bic(rszz, pdszz)

        new_data = get_commit_data(d["fix_commit_hash"])
        if new_data:
            d.update(new_data)

with open("data/issues.json", "w") as f:
    json.dump(data, f, indent=4)

group_file_by_fix("data/issues.json")