import os
import json
from pydriller import Repository
from utils.utils import split_json_file
import argparse

def prepare_data(input_folder):
    data_file = []
    for file in os.listdir(input_folder):
        if file.endswith('.json'):
            original_file_path = os.path.join(input_folder, file)
            with open(original_file_path, 'r') as f:
                data = json.load(f)
                for d in data:
                    if len(d.get('bic')) > 0:
                        commit_sha = d['fix_commit_hash']
                        bic = d.get('bic')[-1]
                        for commit in Repository(f'./repos_dir/{d.get("repo_name").split("/")[-1]}', single=commit_sha).traverse_commits():
                            if commit.merge:
                                print(f"Skipping merge commit {commit_sha} in repo {d.get('repo_name')}")
                                d['bic'] = []
                                continue
                        usable_bic = {
                            'repo_name': d.get('repo_name'),
                            'fix_commit_hash': bic,
                            'path_id': d.get('path_id'),
                        }
                        data_file.append(usable_bic)

    return data_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare data for SZZ analysis")
    parser.add_argument("--input_folder", type=str, required=True, help="Path to the folder containing the input JSON files") 
    parser.add_argument("--output_folder", type=str, required=True, help="Path to the folder where the output JSON files will be saved")
    parser.add_argument("--file_prefix", type=str, required=True, help="Prefix for the output files")
    parser.add_argument("--batch_size", type=int, default=50, help="Number of entries per output file")
    
    args = parser.parse_args()

    if not os.path.exists(args.input_folder):
        print(f"Input folder '{args.input_folder}' does not exist.")
        exit(1)

    data_to_split = prepare_data(args.input_folder)
    
    split_json_file(data_to_split, args.output_folder, args.file_prefix, args.batch_size)