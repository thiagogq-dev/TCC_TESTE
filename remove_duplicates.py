import json
import os
input_file = "./json/raw_data/final.json"
# Carregar o JSON de um arquivo
with open(input_file, 'r') as file:
    data = json.load(file)

print(len(data))

# Remover duplicatas
data_unique = list({json.dumps(item, sort_keys=True) for item in data})
data_unique = [json.loads(item) for item in data_unique]

print(len(data_unique))
# Salvar o JSON sem duplicatas em um novo arquivo
with open(input_file, 'w') as file:
    json.dump(data_unique, file, indent=4)

print("Registros duplicados foram removidos!")


# for file in os.listdir("./json/raw_data/"):
#     with open(f"./json/raw_data/{file}") as f:
#         data = json.load(f)

#         for record in data:
#             record.pop("best_scenario_issue_date", None)
#             record.pop("modified_files", None)

#         with open(f"./json/raw_data/{file}", "w") as f:
#             json.dump(data, f, indent=4)