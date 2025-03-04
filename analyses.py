import csv
import json
import numpy as np

def process_csv():
    final_data = []
    with open('./data/jabref.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            final_data.append(row)

    return final_data

# input_file = "./data/jabref.json"
# output_file = "./data/jabref.csv"

# # Ler o arquivo JSON
# with open(input_file, mode="r", encoding="utf-8") as file:
#     data = json.load(file)

# # Converter JSON para CSV
# with open(output_file, mode="w", newline="", encoding="utf-8") as file:
#     writer = csv.writer(file)
    
#     # Escrever cabeçalhos (usando as chaves do primeiro elemento do JSON)
#     headers = data[0].keys()
#     writer.writerow(headers)
    
#     # Escrever dados
#     for entry in data:
#         # Ajustar 'matched' para ser apenas uma string ou vazio
#         if len(entry["matched"]) > 0:
#             string_resultante = ', '.join(entry["matched"])
#             entry["matched"] = string_resultante
#         else:
#             entry["matched"] = ""
#         # entry['matched'] = entry['matched'][0] if entry['matched'] else ""
#         writer.writerow(entry.values())

# print(f"Arquivo CSV salvo como {output_file}")

#########################################################################################################

# import json

# file_path = "./data/jabref.json"

# # Definir a nova ordem das chaves
# field_order = [
#     "repo_name", "fix_commit_hash", "test_changes", "files_with_tests", "changed_files", "lines", "insertions", "deletions",
#     "commit_author", "commit_date", "commiter", "committer_data",
#     "dmm_unit_complexity", "dmm_unit_interfacing", "dmm_unit_size", "matched"
# ]

# # # # Função para reordenar os campos
# def reorder_fields(item, order):
#     return {key: item[key] for key in order if key in item}

# # Carregar o JSON, reordenar e salvar novamente
# with open(file_path, "r", encoding="utf-8") as file:
#     data = json.load(file)

# print(len(data))

# # Reordenar cada objeto na lista
# reordered_data = [reorder_fields(commit, field_order) for commit in data]

# # Salvar o JSON com as chaves reordenadas
# with open(file_path, "w", encoding="utf-8") as file:
#     json.dump(reordered_data, file, indent=4, ensure_ascii=False)

# with open(file_path, "r", encoding="utf-8") as file:
#     data = json.load(file)
# print(len(data))

# print("Campos reordenados com sucesso!")

#########################################################################################################

# import csv

# tests = 0
# complexity_tests = 0

# no_tests = 0
# complexity_no_tests = 0

# with open('./data/jabref.csv', 'r', encoding='utf-8') as file:
#     reader = csv.DictReader(file)
#     data = list(reader) 

#     # Passar por todas as linhas
#     for row in data:
#         try:
#             complexity_value = float(row['dmm_unit_complexity']) if row['dmm_unit_complexity'] else None
#             if row['test_changes'] == 'Yes' and complexity_value is not None:
#                 tests += 1
#                 complexity_tests += complexity_value
#             elif row['test_changes'] == 'No' and complexity_value is not None:
#                 no_tests += 1
#                 complexity_no_tests += complexity_value
#         except ValueError:
#             # Ignorar valores que não podem ser convertidos
#             continue

# with open('./data/analyses.txt', 'w', encoding='utf-8') as file:
#     if tests > 0:
#         file.write(f"Complexidade média dos commits com testes: {complexity_tests / tests}\n")
#     else:
#         file.write("Nenhum commit com testes foi encontrado.\n")

#     if no_tests > 0:
#         file.write(f"Complexidade média dos commits sem testes: {complexity_no_tests / no_tests}\n")
#     else:
#         file.write("Nenhum commit sem testes foi encontrado.\n")

# print(tests + no_tests)

#############################################################################################################################################

# import csv

# records = 3547
# tests = 0
# no_tests = 0

# with open('./data/jabref.csv', 'r', encoding='utf-8') as file:
#     reader = csv.DictReader(file)
#     data = list(reader) 

#     # Passar por todas as linhas
#     for row in data:
#         if row['test_changes'] == 'Yes':
#             tests += 1
#         elif row['test_changes'] == 'No':
#             no_tests += 1

# with open('./data/analyses.txt', 'a', encoding='utf-8') as file:
#     file.write(f"Quantidade de commits com testes: {tests} - {tests / records * 100:.2f}%\n")
#     file.write(f"Quantidade de commits sem testes: {no_tests} - {no_tests / records * 100:.2f}%\n")

#############################################################################################################################################

# import csv

# records = 3547

# tests = 0
# greater_tests = 0
# smaller_tests = -1
# total_changes_tests = 0

# no_tests = 0
# greater_no_tests = 0
# smaller_no_tests = -1
# total_changes_no_tests = 0

# with open('./data/jabref.csv', 'r', encoding='utf-8') as file:
#     reader = csv.DictReader(file)
#     data = list(reader) 

#     # Passar por todas as linhas
#     for row in data:
#         if row['test_changes'] == 'Yes':
#             tests += 1
#             total_changes_tests += int(row['changed_files'])
#             if smaller_tests == -1 or int(row['changed_files']) < smaller_tests:
#                smaller_tests = int(row['changed_files'])
#             if int(row['changed_files']) > greater_tests:
#                     greater_tests = int(row['changed_files'])
#         elif row['test_changes'] == 'No':
#             no_tests += 1
#             total_changes_no_tests += int(row['changed_files'])
#             if smaller_no_tests == -1 or int(row['changed_files']) < smaller_no_tests:
#                 smaller_no_tests = int(row['changed_files'])
#             if int(row['changed_files']) > greater_no_tests:
#                 greater_no_tests = int(row['changed_files'])

# with open('./data/analyses.txt', 'a', encoding='utf-8') as file:
#     file.write(f"Menor quantidade de arquivos modificados em commits com testes: {smaller_tests}\n")
#     file.write(f"Maior quantidade de arquivos modificados em commits com testes: {greater_tests}\n")
#     file.write(f"Média de arquivos modificados em commits com testes: {total_changes_tests / tests}\n")

#     file.write(f"Menor quantidade de arquivos modificados em commits sem testes: {smaller_no_tests}\n")
#     file.write(f"Maior quantidade de arquivos modificados em commits sem testes: {greater_no_tests}\n")
#     file.write(f"Média de arquivos modificados em commits sem testes: {total_changes_no_tests / no_tests}\n")

#############################################################################################################################################

# import csv
# import json

# caused_bug_with_tests = 0
# caused_bug_without_tests = 0

# no_caused_bug_with_tests = 0
# no_caused_bug_without_tests = 0

# tests = 0
# no_tests = 0

# avg_caused_bugs_with_tests = 0
# avg_caused_bugs_without_tests = 0

# processed_commits = set()  # Conjunto para armazenar commits já processados
# with open('./relations/commit_path.json') as file:
#     data = json.load(file)

#     for d in data:
#         fix_commit = d['fix_commit']
        
#         if fix_commit in processed_commits:
#             continue

#         with open('./data/jabref.csv', 'r', encoding='utf-8') as file:
#             reader = csv.DictReader(file)
#             for row in reader:
#                 if row['fix_commit_hash'] == fix_commit:
#                     if len(d['Fix in BIC']) > 0:
#                         if row['test_changes'] == 'Yes':
#                             caused_bug_with_tests += 1
#                         elif row['test_changes'] == 'No':
#                             caused_bug_without_tests += 1
#                     else:
#                         if row['test_changes'] == 'Yes':
#                             no_caused_bug_with_tests += 1
#                         elif row['test_changes'] == 'No':
#                             no_caused_bug_without_tests += 1
#                     break

# with open('./data/analyses.txt', 'a', encoding='utf-8') as file:
#     file.write(f"Quantidade de commits com testes que introduziram bugs: {caused_bug_with_tests}\n")
#     file.write(f"Quantidade de commits sem testes que introduziram bugs: {caused_bug_without_tests}\n")
#     file.write(f"Quantidade de commits com testes que não introduziram bugs: {no_caused_bug_with_tests}\n")
#     file.write(f"Quantidade de commits sem testes que não introduziram bugs: {no_caused_bug_without_tests}\n")

########################################################################################################################################


# final_data = []
# with open('./data/final.csv', 'r', encoding='utf-8') as file:
#     reader = csv.DictReader(file)
#     for row in reader:
#         final_data.append(row)

# dicionario = {}

# with open('./relations/commit_path.json') as file:
#     data = json.load(file)

#     for d in data:
#         len_bic = len(d['Fix in BIC'])
#         if len_bic == 22:
#             print(d)
#         if len_bic not in dicionario:
#             dicionario[len_bic] = {
#                 "lines": 0,
#                 "dmm_unit_complexity": 0.0,
#                 "dmm_unit_interfacing": 0.0,
#                 "dmm_unit_size": 0.0,
#                 "count": 0,
#             }
#         fix_commit = d['fix_commit']
#         for row in final_data:
#             if row['fix_commit_hash'] == fix_commit:
#                 try:
#                     if row['dmm_unit_complexity'] and row['dmm_unit_interfacing'] and row['dmm_unit_size']:
#                         dicionario[len_bic]['lines'] += int(row['lines'])
#                         dicionario[len_bic]['dmm_unit_complexity'] += float(row['dmm_unit_complexity'])
#                         dicionario[len_bic]['dmm_unit_interfacing'] += float(row['dmm_unit_interfacing'])
#                         dicionario[len_bic]['dmm_unit_size'] += float(row['dmm_unit_size'])
#                         dicionario[len_bic]['count'] += 1
#                     else:
#                         continue
#                 except ValueError as e:
#                     print(f"Erro ao processar linha: {row}. Detalhes: {e}")
#                     continue
                
# with open('./data/analyses.txt', 'a', encoding='utf-8') as file:
#     for key, value in dicionario.items():
#         file.write(f"Quantidade de BICs gerados: {key}\n")
#         file.write(f"Linhas: {value['lines']/value['count']}\n")
#         file.write(f"Complexidade média: {value['dmm_unit_complexity'] / value['count']}\n")
#         file.write(f"Interfacing médio: {value['dmm_unit_interfacing'] / value['count']}\n")
#         file.write(f"Tamanho médio: {value['dmm_unit_size'] / value['count']}\n")
#         file.write("\n\n")

#########################################################################################################################

count = 0
files_changed = []
changed_files_tests = 0
changed_files = 0
with open('./data/jabref/jabref.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

    for d in data:  
        if d["changed_files"] > 0:
            if d["test_changes"] == "Yes":
                count += 1
                files_changed.append(d['files_with_tests'])
                changed_files += int(d['changed_files'])
                changed_files_tests += int(d['files_with_tests'])


print(f"Quantidade de commits com testes: {count}")
print(f"Quantidade de arquivos modificados que possuem testes: {changed_files_tests}")
print(f"Quantidade de arquivos modificados: {changed_files}")
print(f"Média de arquivos modificados: {changed_files / count}")
print(f"Média de arquivos modificados que possuem testes: {changed_files_tests / count}")
# pegar mediana e média
# files_changed.sort()
# mediana = np.median(files_changed)

# with open('./data/analyses.txt', 'a', encoding='utf-8') as file:
#     file.write(f"Média de arquivos modificados que possuem testes: {changed_files / count}\n")
#     file.write(f"Mediana de arquivos modificados que possuem testes: {mediana}\n")

########################################################################################################

# import csv

# tests = 0
# unit_interfacing_tests = 0
# unit_size_tests = 0

# no_tests = 0
# unit_interfacing_no_tests = 0
# unit_size_no_tests = 0

# with open('./data/jabref.csv', 'r', encoding='utf-8') as file:
#     reader = csv.DictReader(file)
#     data = list(reader) 

#     # Passar por todas as linhas
#     for row in data:
#         try:
#             # complexity_value = float(row['dmm_unit_complexity']) if row['dmm_unit_complexity'] else None
#             if row['dmm_unit_interfacing'] and row['dmm_unit_size']:
               
#                 if row['test_changes'] == 'Yes':
#                     unit_interfacing_tests += float(row['dmm_unit_interfacing'])
#                     unit_size_tests += float(row['dmm_unit_size'])
#                     tests += 1
#                 elif row['test_changes'] == 'No':
#                     no_tests += 1
#                     unit_interfacing_no_tests += float(row['dmm_unit_interfacing'])
#                     unit_size_no_tests += float(row['dmm_unit_size'])
#         except ValueError:
#             # Ignorar valores que não podem ser convertidos
#             continue

# with open('./data/analyses.txt', 'a', encoding='utf-8') as file:
#     if tests > 0:
#         file.write(f"Interfacing médio dos commits com testes: {unit_interfacing_tests / tests}\n")
#         file.write(f"Tamanho médio dos commits com testes: {unit_size_tests / tests}\n")
#     else:
#         file.write("Nenhum commit com testes foi encontrado.\n")

#     if no_tests > 0:
#         file.write(f"Interfacing médio dos commits sem testes: {unit_interfacing_no_tests / no_tests}\n")
#         file.write(f"Tamanho médio dos commits sem testes: {unit_size_no_tests / no_tests}\n")
#     else:
#         file.write("Nenhum commit sem testes foi encontrado.\n")
