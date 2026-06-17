import os

import matplotlib.pyplot as plt
import numpy as np
import json
import glob

def plot_confusion_matrix(tp, fp, tn, fn, output_file, quadrant_colors, repo_name=''):
    matrix = np.array([[tp, fp], [fn, tn]])

    plt.figure(figsize=(8, 8))
    plt.imshow(matrix, interpolation='nearest', cmap=plt.cm.Blues)

    for i in range(2):
        for j in range(2):
            plt.text(j, i, str(matrix[i, j]), horizontalalignment='center', verticalalignment='center', color='black')

    plt.gca().add_patch(plt.Rectangle((-0.5, 0.5), 1, 1, fill=True, edgecolor='black', facecolor=quadrant_colors[0]))
    plt.gca().add_patch(plt.Rectangle((0.5, 0.5), 1, 1, fill=True, edgecolor='black', facecolor=quadrant_colors[1]))
    plt.gca().add_patch(plt.Rectangle((-0.5, -0.5), 1, 1, fill=True, edgecolor='black', facecolor=quadrant_colors[2]))
    plt.gca().add_patch(plt.Rectangle((0.5, -0.5), 1, 1, fill=True, edgecolor='black', facecolor=quadrant_colors[3]))

    classes = ['Com', 'Sem']
    tick_marks = np.arange(len(classes))

    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    plt.ylabel('BIC')
    plt.xlabel('FIX')

    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(False)

    plt.gca().invert_yaxis()

    plt.title(f'Confusion Matrix - {repo_name}')
    plt.savefig(output_file)
    plt.close()

# json_files = glob.glob('./data/*.json')

# for json_file in json_files:

#     with open(json_file, 'r') as f:
#         data = json.load(f)

#     commit_map = {
#         entry['fix_commit_hash']: entry
#         for entry in data
#     }

#     # Contadores
#     bic_fix = 0   # FIX com teste + BIC com teste
#     bic = 0       # FIX sem teste + BIC com teste
#     fix = 0       # FIX com teste + BIC sem teste
#     none = 0      # FIX sem teste + BIC sem teste

#     # Para cada FIX
#     for entry in data:
#         fix_has_tests = entry.get('has_tests') == 'Yes'
#         bic_hashes = entry.get('bic', [])

#         # Para cada BIC associado ao FIX
#         for bic_hash in bic_hashes:

#             bic_entry = commit_map.get(bic_hash)

#             # Se o BIC não estiver no dataset, ignora
#             if not bic_entry:
#                 continue

#             bic_has_tests = bic_entry.get('has_tests') == 'Yes'

#             # Classificação do par (FIX, BIC)
#             if fix_has_tests and bic_has_tests:
#                 bic_fix += 1
#             elif fix_has_tests and not bic_has_tests:
#                 fix += 1
#             elif not fix_has_tests and bic_has_tests:
#                 bic += 1
#             else:
#                 none += 1

#     tp = bic_fix
#     fp = bic
#     tn = none
#     fn = fix

#     repo_name = json_file.split('/')[-1].replace('.json', '')
#     output_file = f"./results/{repo_name}/data.png"
#     os.makedirs(f"./results/{repo_name}", exist_ok=True)
#     plot_confusion_matrix(tp, fp, tn, fn, output_file, quadrant_colors=('yellow', 'red', 'green', 'orange'), repo_name=repo_name)



json_files = glob.glob('./relations/*.json')

for json_file in json_files:

    with open(json_file, 'r') as f:
        data = json.load(f)

    commit_map = {
        entry['commit']: entry
        for entry in data
    }

    # Contadores
    bic_fix = 0   # FIX com teste + BIC com teste
    bic = 0       # FIX sem teste + BIC com teste
    fix = 0       # FIX com teste + BIC sem teste
    none = 0      # FIX sem teste + BIC sem teste

    # Para cada FIX
    for entry in data:
        bic_has_asserts_changes = entry.get('test_files_with_asserts_changes') > 0
        fix_hashes = entry.get('fixed_by', [])

        # Para cada BIC associado ao FIX
        for fix_hash in fix_hashes:

            fix_entry = commit_map.get(fix_hash)

            # Se o BIC não estiver no dataset, ignora
            if not fix_entry:
                continue

            fix_has_asserts_changes = fix_entry.get('test_files_with_asserts_changes') > 0

            # Classificação do par (FIX, BIC)
            if fix_has_asserts_changes and bic_has_asserts_changes:
                bic_fix += 1
            elif fix_has_asserts_changes and not bic_has_asserts_changes:
                fix += 1
            elif not fix_has_asserts_changes and bic_has_asserts_changes:
                bic += 1
            else:
                none += 1

    tp = bic_fix
    fp = bic
    tn = none
    fn = fix

    repo_name = json_file.split('/')[-1].replace('.json', '')
    output_file = f"./results/{repo_name}/rq3.png"
    os.makedirs(f"./results/{repo_name}", exist_ok=True)
    plot_confusion_matrix(tp, fp, tn, fn, output_file, quadrant_colors=('yellow', 'red', 'green', 'orange'), repo_name=repo_name)
