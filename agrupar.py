import json
from collections import defaultdict

# Carregar o arquivo JSON
with open("./data/final.json", "r") as file:
    data = json.load(file)

# Dicionário para agrupar os registros por fix_commit_hash
grouped_data = {}

for record in data:
    fix_hash = record["fix_commit_hash"]
    
    # Se o fix_commit_hash ainda não estiver no dicionário, adicionar o registro completo
    if fix_hash not in grouped_data:
        grouped_data[fix_hash] = record
        grouped_data[fix_hash]["matched"] = set(record["matched"])  # Usar conjunto para evitar duplicatas
    else:
        # Apenas atualizar o campo "matched"
        grouped_data[fix_hash]["matched"].update(record["matched"])

# Converter o conjunto "matched" de volta para lista
result = [
    {**values, "matched": list(values["matched"])}
    for values in grouped_data.values()
]

# Salvar o resultado em um novo arquivo JSON
with open("./data/final.json", "w") as file:
    json.dump(result, file, indent=4)

print("Processamento concluído! O arquivo agrupado foi salvo como 'arquivo_agrupado.json'.")
