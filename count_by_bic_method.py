import json
import os
import csv

filename = "./csv/got_by_method.csv"

if os.path.exists(filename):
    os.remove(filename)

def write_csv(count_pyszz, count_pd, count_matched):
    mode = 'a' if os.path.exists(filename) else 'w'

    with open(filename, mode, newline='') as csvfile:
        fieldnames = ['Number of caught by PYSZZ', 'Number of caught by PyDriller', 'Number of caught by both']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if mode == 'w':
            writer.writeheader()

        writer.writerow({'Number of caught by PYSZZ': count_pyszz, 'Number of caught by PyDriller': count_pd, 'Number of caught by both': count_matched})

with open('./json/bics.json') as f:
    bics = json.load(f)

    count_pyszz = 0
    count_pd = 0
    count_match = 0

    print(len(bics))

    for data in bics:
        if len(data['matched']) > 0:
            count_match += 1
        else:
            if len(data['inducing_commit_hash_pyszz']) > 0:
                count_pyszz += 1
            if len(data['inducing_commit_hash_pd']) > 0:
                count_pd += 1

    write_csv(count_pyszz, count_pd, count_match)