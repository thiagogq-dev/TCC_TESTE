import os
import json
from pydriller import Repository
from utils.utils import split_json_file
import argparse

def check_merge_commit(repo_path, commit_sha):
    for commit in Repository(repo_path, single=commit_sha).traverse_commits():
        if commit.merge:
            return True
    return False


def prepare_data(input_folder, first_actions_attempt=False):
    if first_actions_attempt:
        print("Primeira tentativa de usar github actions para os BICs. Verificando se os commits são merge commits...")
    else:
        print("Processamento dos dados falhou no github actions (limite de tempo ou memória). Reduzindo o tamanho do chunk para tentar evitar falhas.")

    data_file = []
    for file in os.listdir(input_folder):
        if file.endswith('.json'):
            original_file_path = os.path.join(input_folder, file)
            with open(original_file_path, 'r') as f:
                data = json.load(f)
                for d in data:
                    # Verifica se é a primeira tentativa de usar github actions para os BICs
                    # Se for, e se houver BICs disponíveis, utiliza o último BIC para verificar se o commit é um merge commit
                    if first_actions_attempt:
                        if len(d.get('bic')) > 0:
                            commit_sha = d['fix_commit_hash']
                            bic = d.get('bic')[-1]
                            if check_merge_commit(f'./repos_dir/{d.get("repo_name").split("/")[-1]}', commit_sha):
                                print(f"Skipping merge commit {commit_sha} in repo {d.get('repo_name')}")
                                d['bic'] = []
                                continue
                            szz_data = {
                                'repo_name': d.get('repo_name'),
                                'fix_commit_hash': bic,
                                'path_id': d.get('path_id'),
                            }
                    else:
                        # Se não, quer dizer que o processamento anterior já foi feito
                        # E a falaha ocorreu no uso do github actions para os BICs
                        # Nesse caso, diminuímos o tamanho do chunn para verificar se o processo é mais leve e não falha
                        szz_data = {
                            'repo_name': d.get('repo_name'),
                            'fix_commit_hash': d.get('fix_commit_hash'),
                            'path_id': d.get('path_id'),
                        }

                    data_file.append(szz_data)

    return data_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare data for SZZ analysis")
    parser.add_argument("--input_folder", type=str, required=True, help="Path to the folder containing the input JSON files") 
    parser.add_argument("--output_folder", type=str, required=True, help="Path to the folder where the output JSON files will be saved")
    parser.add_argument("--file_prefix", type=str, required=True, help="Prefix for the output files")
    parser.add_argument("--batch_size", type=int, default=50, help="Number of entries per output file")
    parser.add_argument("--first_actions_attempt", action='store_true', help="Flag to indicate if this is the first attempt to use github actions for the BICs")
    
    args = parser.parse_args()

    if not os.path.exists(args.input_folder):
        print(f"Input folder '{args.input_folder}' does not exist.")
        exit(1)

    data_to_split = prepare_data(args.input_folder, args.first_actions_attempt)
    
    split_json_file(data_to_split, args.output_folder, args.file_prefix, args.batch_size)