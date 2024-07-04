import json
import os
import csv

if os.path.exists("./csv/bics_recurrence.csv"):
    os.remove("./csv/bics_recurrence.csv")

def write_csv(commit_hash, count_pyszz, count_pd, filename):
    mode = 'a' if os.path.exists(filename) else 'w'

    with open(filename, mode, newline='') as csvfile:
        fieldnames = ['Commit Hash', 'Count in pyszz', 'Count in pd']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if mode == 'w':
            writer.writeheader()

        writer.writerow({'Commit Hash': commit_hash, 'Count in pyszz': count_pyszz, 'Count in pd': count_pd})

with open('./json/consolidated_data.json') as f:
    bics = json.load(f)

    for data in bics:
        count_pyszz = 0
        count_pd = 0
        repository = data['repo_url']
        hash = ""

        # if len(data['inducing_commit_hash_pyszz']) > 0:
        #     hash = data['inducing_commit_hash_pyszz'][0]

        hash = data['matched'][0]
        fix_commit = data['fix_commit_hash']

        for d in bics:
            if d == data:
                continue

            if hash in d['inducing_commit_hash_pyszz']:
                count_pyszz += 1

            if hash in d['inducing_commit_hash_pd']:
                count_pd += 1


        write_csv(hash, count_pyszz, count_pd, "./csv/bics_recurrence.csv")