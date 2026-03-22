"""
This script performs pre-analysis cleanup on the collected data. It merges all JSON files in the 'data' folder into a single file, removes duplicate entries, and prepares the final dataset for analysis.
"""
from utils.utils import merge_files, remove_duplicates
import os

# Step 1: Merge all JSON files in the 'data' folder into a single file
merge_files('data', 'data.json')
# Step 2: Remove duplicate entries from the merged file
remove_duplicates('data.json', 'final_data.json')
# Step 3: Remove the intermediate merged file
os.remove('data.json')