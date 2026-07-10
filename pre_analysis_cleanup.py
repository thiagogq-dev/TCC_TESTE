"""
This script performs pre-analysis cleanup on the collected data. It merges all JSON files in the 'data' folder into a single file, removes duplicate entries, and prepares the final dataset for analysis.
"""
import json

from utils.utils import group_file_by_fix, merge_files, remove_duplicates
import os
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Prepare data for SZZ analysis"
    )

    parser.add_argument(
        "--input_folder",
        required=True,
        help="Folder containing input JSON files",
    )

    parser.add_argument(
        "--output_folder",
        required=True,
        help="Folder where output JSON files will be saved",
    )

    parser.add_argument(
        "--output_file",
        required=True,
        help="Name of the final output JSON file",
    )
    
    args = parser.parse_args()
    
    input_folder = args.input_folder
    output_folder = args.output_folder
    output_file = args.output_file

    # Passo 1: Juntar todos os registros de uma pasta em um só arquivo
    merged_data = merge_files(input_folder)

    # Passo 2: Agrupar registros de mesma correcão e relacionar os diferentes BICs detectados
    grouped_data = group_file_by_fix(merged_data)

    # Passo 3: Remover registros duplicados
    unique_data = remove_duplicates(grouped_data)

    # Passo 4: Salvar a json final
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_path = os.path.join(output_folder, output_file)
    with open(output_path, 'w') as f:
        json.dump(unique_data, f, indent=4)
    print(f"Data cleaned and saved to {output_path} with {len(unique_data)} unique entries.")


if __name__ == "__main__":
    main()
