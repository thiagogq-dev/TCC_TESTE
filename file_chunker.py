import json

def split_json_file(input_file, output_prefix, max_items_per_file=100):
    with open(input_file, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("O arquivo JSON deve conter uma lista de itens")

    chunks = [data[i:i + max_items_per_file] for i in range(0, len(data), max_items_per_file)]

    for idx, chunk in enumerate(chunks):
        output_file = f"{output_prefix}_{idx + 1}.json"
        with open(output_file, 'w') as f:
            json.dump(chunk, f, indent=4)
        print(f"Arquivo {output_file} criado com {len(chunk)} itens.")

input_file = './json/issues_data.json'  
output_prefix = './json/issues_data'  
split_json_file(input_file, output_prefix)
