import os
from utils.utils import format, remove_non_existing_commits

for file in os.listdir("./json/bics/"):
    print(f"Removing non-existing commits from {file}")
    format(f"json/bics/{file}")
    remove_non_existing_commits(f"json/bics/{file}")
