

import requests
import json
import sys
import os
from pydriller import Git, Repository

def get_commit_data(commit_hash):
    for commit in Repository("repos_dir/jabref", single=commit_hash).traverse_commits():
        print(commit.msg)
           

get_commit_data("2cd83dfdb056482aad9595489a4a7c4b796f6e37")