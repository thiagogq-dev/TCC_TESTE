import json

read = {}  # Armazenará os `fix_commit_hash` com o valor correspondente de `matched`
duplicates = []  # Armazenará os registros com `matched` diferentes

with open('./data/final copy.json') as f:
    data = json.load(f)

    for d in data:
        fix_commit = d['fix_commit_hash']
        matched_value = d['matched']

        if fix_commit not in read:
            read[fix_commit] = matched_value  # Salva o primeiro `matched` encontrado
        else:
            # Compara o `matched` do registro atual com o anterior
            if read[fix_commit] != matched_value:
                duplicates.append(d)  # Armazena o registro atual como duplicado

# Exibir os registros duplicados
for duplicate in duplicates:
    print(duplicate)
