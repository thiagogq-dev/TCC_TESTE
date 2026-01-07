import csv
import json
import numpy as np
import json

def process_json():
    with open('./json/raw_data/final.json') as file:
        data = json.load(file)
        return data

def process_csv():
    final_data = []
    with open('./data/jabref.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            final_data.append(row)

    return final_data

def json_to_csv(input_file, output_file):
    # Ler o arquivo JSON
    with open(input_file, mode="r", encoding="utf-8") as file:
        data = json.load(file)

    # Converter JSON para CSV
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # Escrever cabeçalhos (usando as chaves do primeiro elemento do JSON)
        headers = data[0].keys()
        writer.writerow(headers)
        
        # Escrever dados
        for entry in data:
            # Ajustar 'matched' para ser apenas uma string ou vazio
            if len(entry["matched"]) > 0:
                string_resultante = ', '.join(entry["matched"])
                entry["matched"] = string_resultante
            else:
                entry["matched"] = ""
            writer.writerow(entry.values())

    print(f"Arquivo CSV salvo como {output_file}")


#########################################################################################################

def calculate_avg_complexity():
    tests = 0
    complexity_tests = 0

    no_tests = 0
    complexity_no_tests = 0

    ignored = 0
    data = process_json()
    for record in data:
        try:
            complexity_value = float(record['dmm_unit_complexity']) if record['dmm_unit_complexity'] else None
            if record['test_changes'] == 'Yes' and complexity_value is not None:
                tests += 1
                complexity_tests += complexity_value
            elif record['test_changes'] == 'No' and complexity_value is not None:
                no_tests += 1
                complexity_no_tests += complexity_value
            else:
                ignored += 1
        except ValueError:
            continue

    with open('./data/analyses.txt', 'w', encoding='utf-8') as file:
        if tests > 0:
            file.write(f"Complexidade média dos commits com testes: {complexity_tests / tests}\n")
        else:
            file.write("Nenhum commit com testes foi encontrado.\n")

        if no_tests > 0:
            file.write(f"Complexidade média dos commits sem testes: {complexity_no_tests / no_tests}\n")
        else:
            file.write("Nenhum commit sem testes foi encontrado.\n")

    print(tests + no_tests + ignored)

#############################################################################################################################################

def calculate_test_changes():
    data = process_json()
    records = len(data)
    tests = 0
    no_tests = 0

    for record in data:
        if record['test_changes'] == 'Yes':
            tests += 1
        elif record['test_changes'] == 'No':
            no_tests += 1

    with open('./data/analyses.txt', 'a', encoding='utf-8') as file:
        file.write(f"Quantidade de commits com testes: {tests} - {tests / records * 100:.2f}%\n")
        file.write(f"Quantidade de commits sem testes: {no_tests} - {no_tests / records * 100:.2f}%\n")

#############################################################################################################################################

def calculate_files_changed():
    data = process_json()

    tests = 0
    greater_tests = 0
    smaller_tests = -1
    total_changes_tests = 0

    no_tests = 0
    greater_no_tests = 0
    smaller_no_tests = -1
    total_changes_no_tests = 0

    for record in data:
        if record['test_changes'] == 'Yes':
            tests += 1
            total_changes_tests += int(record['changed_files'])
            if smaller_tests == -1 or int(record['changed_files']) < smaller_tests:
               smaller_tests = int(record['changed_files'])
            if int(record['changed_files']) > greater_tests:
                    greater_tests = int(record['changed_files'])
        elif record['test_changes'] == 'No':
            no_tests += 1
            total_changes_no_tests += int(record['changed_files'])
            if smaller_no_tests == -1 or int(record['changed_files']) < smaller_no_tests:
                smaller_no_tests = int(record['changed_files'])
            if int(record['changed_files']) > greater_no_tests:
                greater_no_tests = int(record['changed_files'])

    with open('./data/analyses.txt', 'a', encoding='utf-8') as file:
        file.write(f"Menor quantidade de arquivos modificados em commits com testes: {smaller_tests}\n")
        file.write(f"Maior quantidade de arquivos modificados em commits com testes: {greater_tests}\n")
        file.write(f"Média de arquivos modificados em commits com testes: {total_changes_tests / tests}\n")

        file.write(f"Menor quantidade de arquivos modificados em commits sem testes: {smaller_no_tests}\n")
        file.write(f"Maior quantidade de arquivos modificados em commits sem testes: {greater_no_tests}\n")
        file.write(f"Média de arquivos modificados em commits sem testes: {total_changes_no_tests / no_tests}\n")

#############################################################################################################################################

def calculate_proportion_bugs_tests():
    caused_bug_with_tests = 0
    caused_bug_without_tests = 0

    no_caused_bug_with_tests = 0
    no_caused_bug_without_tests = 0

    tests = 0
    no_tests = 0

    avg_caused_bugs_with_tests = 0
    avg_caused_bugs_without_tests = 0

    processed_commits = set()  # Conjunto para armazenar commits já processados
    with open('./relations/commit_path.json') as file:
        data = json.load(file)

        for d in data:
            fix_commit = d['fix_commit']
            
            if fix_commit in processed_commits:
                continue

            data = process_json()
            for record in data:
                if record['fix_commit_hash'] == fix_commit:
                    if len(d['Fix in BIC']) > 0:
                        if record['test_changes'] == 'Yes':
                            caused_bug_with_tests += 1
                        elif record['test_changes'] == 'No':
                            caused_bug_without_tests += 1
                    else:
                        if record['test_changes'] == 'Yes':
                            no_caused_bug_with_tests += 1
                        elif record['test_changes'] == 'No':
                            no_caused_bug_without_tests += 1
                    break

    with open('./data/analyses.txt', 'a', encoding='utf-8') as file:
        file.write(f"Quantidade de commits com testes que introduziram bugs: {caused_bug_with_tests}\n")
        file.write(f"Quantidade de commits sem testes que introduziram bugs: {caused_bug_without_tests}\n")
        file.write(f"Quantidade de commits com testes que não introduziram bugs: {no_caused_bug_with_tests}\n")
        file.write(f"Quantidade de commits sem testes que não introduziram bugs: {no_caused_bug_without_tests}\n")

########################################################################################################################################

def calculate_avg_for_bugy_fixes():
    final_data = process_json()

    dicionario = {}

    with open('./relations/commit_path.json') as file:
        data = json.load(file)

        for d in data:
            len_bic = len(d['Fix in BIC'])
            if len_bic == 22:
                print(d)
            if len_bic not in dicionario:
                dicionario[len_bic] = {
                    "lines": 0,
                    "dmm_unit_complexity": 0.0,
                    "dmm_unit_interfacing": 0.0,
                    "dmm_unit_size": 0.0,
                    "count": 0,
                }
            fix_commit = d['fix_commit']
            for row in final_data:
                if row['fix_commit_hash'] == fix_commit:
                    try:
                        if row['dmm_unit_complexity'] and row['dmm_unit_interfacing'] and row['dmm_unit_size']:
                            dicionario[len_bic]['lines'] += int(row['lines'])
                            dicionario[len_bic]['dmm_unit_complexity'] += float(row['dmm_unit_complexity'])
                            dicionario[len_bic]['dmm_unit_interfacing'] += float(row['dmm_unit_interfacing'])
                            dicionario[len_bic]['dmm_unit_size'] += float(row['dmm_unit_size'])
                            dicionario[len_bic]['count'] += 1
                        else:
                            continue
                    except ValueError as e:
                        print(f"Erro ao processar linha: {row}. Detalhes: {e}")
                        continue
                    
    with open('./data/analyses.txt', 'a', encoding='utf-8') as file:
        for key, value in dicionario.items():
            if value['count'] == 0:
                continue
            file.write(f"Quantidade de BICs gerados: {key}\n")
            file.write(f"Linhas: {value['lines']/value['count']}\n")
            file.write(f"Complexidade média: {value['dmm_unit_complexity'] / value['count']}\n")
            file.write(f"Interfacing médio: {value['dmm_unit_interfacing'] / value['count']}\n")
            file.write(f"Tamanho médio: {value['dmm_unit_size'] / value['count']}\n")
            file.write("\n\n")

#########################################################################################################################

def calculate_avg_qtde_files_tests():
    count = 0
    files_changed = []
    changed_files_tests = 0
    changed_files = 0
    data = process_json()

    for d in data:  
        if d["changed_files"] > 0:
            if d["test_changes"] == "Yes":
                count += 1
                files_changed.append(d['files_with_test'])
                changed_files += int(d['changed_files'])
                changed_files_tests += int(d['files_with_test'])


    print(f"Quantidade de commits com testes: {count}")
    print(f"Quantidade de arquivos modificados que possuem testes: {changed_files_tests}")
    print(f"Quantidade de arquivos modificados: {changed_files}")
    print(f"Média de arquivos modificados: {changed_files / count}")
    print(f"Média de arquivos modificados que possuem testes: {changed_files_tests / count}")
    files_changed.sort()
    mediana = np.median(files_changed)

    with open('./data/analyses.txt', 'a', encoding='utf-8') as file:
        file.write(f"Média de arquivos modificados que possuem testes: {changed_files / count}\n")
        file.write(f"Mediana de arquivos modificados que possuem testes: {mediana}\n")

########################################################################################################

def calculate_avg_for_metric():
    tests = 0
    unit_interfacing_tests = 0
    unit_size_tests = 0

    no_tests = 0
    unit_interfacing_no_tests = 0
    unit_size_no_tests = 0

    data = process_json()

    # Passar por todas as linhas
    for row in data:
        try:
            # complexity_value = float(row['dmm_unit_complexity']) if row['dmm_unit_complexity'] else None
            if row['dmm_unit_interfacing'] and row['dmm_unit_size']:
                if row['test_changes'] == 'Yes':
                    unit_interfacing_tests += float(row['dmm_unit_interfacing'])
                    unit_size_tests += float(row['dmm_unit_size'])
                    tests += 1
                elif row['test_changes'] == 'No':
                    no_tests += 1
                    unit_interfacing_no_tests += float(row['dmm_unit_interfacing'])
                    unit_size_no_tests += float(row['dmm_unit_size'])
        except ValueError:
            # Ignorar valores que não podem ser convertidos
            continue

    with open('./data/analyses.txt', 'a', encoding='utf-8') as file:
        if tests > 0:
            file.write(f"Interfacing médio dos commits com testes: {unit_interfacing_tests / tests}\n")
            file.write(f"Tamanho médio dos commits com testes: {unit_size_tests / tests}\n")
        else:
            file.write("Nenhum commit com testes foi encontrado.\n")

        if no_tests > 0:
            file.write(f"Interfacing médio dos commits sem testes: {unit_interfacing_no_tests / no_tests}\n")
            file.write(f"Tamanho médio dos commits sem testes: {unit_size_no_tests / no_tests}\n")
        else:
            file.write("Nenhum commit sem testes foi encontrado.\n")

calculate_avg_complexity()
calculate_test_changes()
calculate_files_changed()
calculate_proportion_bugs_tests()
calculate_avg_for_bugy_fixes()
calculate_avg_qtde_files_tests()
calculate_avg_for_metric()