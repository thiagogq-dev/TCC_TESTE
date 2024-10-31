import json
import csv

# calcula a porcentagem de fix e bic que possuem mudanças de testes
def calculate_percentage_of_fixes_and_bics_with_test_changes(csv_file, output_path):
    """
    Calcula a porcentagem de fix e bic que possuem mudanças de testes

    :param csv_file: arquivo csv com os dados de teste dos commits
    :param output_path: caminho do arquivo de saída
    """
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)
        rows = list(reader)
        total = len(rows) - 1
        print('Total:', total)
        fix_with_tests = 0
        bic_with_tests = 0
        for row in rows:
            if row[2] == 'Yes':
                fix_with_tests += 1

            if row[4] == 'Yes': 
                bic_with_tests += 1

    with open(output_path, 'a') as file:
        writer = csv.writer(file)
        writer.writerow(['Repository', 'Total', 'Fix with tests', 'Fix %', 'BIC with tests', 'BIC %'])
        writer.writerow(['JabRef/jabref', total, fix_with_tests, fix_with_tests/total, bic_with_tests, bic_with_tests/total])

def check_if_commit_has_tests(commit_hash, type, csv_file):
    """
    Verifica se um commit possui mudaças de testes

    :param commit_hash: hash do commit
    :param type: tipo do commit (fix ou bic)
    :param csv_file: arquivo csv com os dados de teste dos commits

    :return: True se o commit possui mudanças de testes, False caso contrário
    """
    if type == 'fix':
        pos_hash = 1
        pos_info = 2
    else:
        pos_hash = 3
        pos_info = 4

    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)
        rows = list(reader)
        for row in rows:
            if row[pos_hash] == commit_hash:
                if row[pos_info] == 'Yes':
                    return True
                else:
                    return False

def calculate_the_fix_commits_with_tests_that_become_bic(json_file, csv_file, output_path):
    """
    Calcula a quantidade de fix com testes que se tornam bic

    :param json_file: arquivo json com os dados consolidados
    :param csv_file: arquivo csv com os dados de teste dos commits
    :param output_path: caminho do arquivo de saída
    """

    fix_with_tests = [] # lista de fix com testes
    fix_with_no_tests = [] # lista de fix sem testes

    bic_with_tests = []
    bic_with_no_tests = []

    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)
        rows = list(reader)
        for row in rows:
            if row[2] == 'Yes':
                fix_with_tests.append(row[1]) # adiciona o hash do commit na lista de fix com testes
            else:
                fix_with_no_tests.append(row[1]) # adiciona o hash do commit na lista de fix sem testes

            if row[4] == 'Yes':
                bic_with_tests.append(row[3])
            else:
                bic_with_no_tests.append(row[3])

    with open(json_file) as f:
        data = json.load(f)

        fix_with_test_in_bic = 0
        fix_with_no_tests_in_bic = 0
        fix_test_seen = []
        fix_no_test_seen = []

        bic_in_other_bic = 0
        bic_in_other_bic_with_tests = 0

        for d in data:
            bic = d['matched'][0]

            if bic in fix_with_tests and bic not in fix_test_seen:
                fix_with_test_in_bic += 1
                fix_test_seen.append(bic)
            elif bic in fix_with_no_tests and bic not in fix_no_test_seen:
                fix_with_no_tests_in_bic += 1
                fix_no_test_seen.append(bic)

    with open(output_path, 'a') as file:
        writer = csv.writer(file)
        writer.writerow(['Fix with Tests', 'Fix with tests in BIC', '%', 'Fix with no BIC', 'Fix with no tests in BIC', '%'])
        writer.writerow([len(fix_with_tests), fix_with_test_in_bic, fix_with_test_in_bic/len(fix_with_tests), len(fix_with_no_tests), fix_with_no_tests_in_bic, fix_with_no_tests_in_bic/len(fix_with_no_tests)])

