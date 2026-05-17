"""
This script performs pre-analysis cleanup on the collected data. It merges all JSON files in the 'data' folder into a single file, removes duplicate entries, and prepares the final dataset for analysis.
"""
from utils.utils import group_file_by_fix, merge_files, remove_duplicates
import os

# Step 1: Merge all JSON files in the 'data' folder into a single file
merge_files('data', 'data.json')
# Step 2: Group the merged file by 'fix_commit_hash' to avoid duplicates of 'bic' for each fix
group_file_by_fix('data.json', 'grouped_data.json')
# Step 3: Remove duplicate entries from the grouped file
remove_duplicates('grouped_data.json', 'final_data.json')
# Step 4: Remove the intermediate files
os.remove('data.json')
os.remove('grouped_data.json')