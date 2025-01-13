import os
import json

total = 0
# listar subdiretórios de um diretório

for file in os.listdir("./json/v2"):
    data_check = []
    file_path = f"./json/v2/{file}"
    with open(file_path, 'r') as f:
        data = json.load(f)
        for item in data:
            if item['changed_files'] > 300 and item['changed_files'] != item['modified_files']:
                print(f"json/v2/{file}")
                # data_check.append(item)
                total += 1
# with open(f'./json_check/{dir}.json', 'w') as f:
#     json.dump(data_check, f, indent=4)

print(total)
