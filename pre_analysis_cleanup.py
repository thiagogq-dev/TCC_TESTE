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

    # Step 1: Merge all JSON files in the input folder into a data register
    merged_data = merge_files(input_folder)

    # Step 2: Group the merged data by 'fix_commit_hash' to avoid duplicates of 'bic' for each fix
    grouped_data = group_file_by_fix(merged_data)

    # Step 3: Remove duplicate entries from the grouped data
    unique_data = remove_duplicates(grouped_data)

    # Step 4: Save the cleaned data to the output folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_path = os.path.join(output_folder, output_file)
    with open(output_path, 'w') as f:
        json.dump(unique_data, f, indent=4)
    print(f"Data cleaned and saved to {output_path} with {len(unique_data)} unique entries.")


if __name__ == "__main__":
    main()
