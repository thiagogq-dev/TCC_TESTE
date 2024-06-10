import json

with open('../json/consolidated_data.json.json') as f:
    bics = json.load(f)
    path = []

    for data in bics:
        bic_pyszz = []
        bic_pd = []
        repository = data['repo_url']
        fix_commit = data['fix_commit_hash']

        for d in bics:
            if fix_commit in d['inducing_commit_hash_pyszz']:
                 bic_pyszz.append(d["fix_commit_hash"])
            if fix_commit in d['inducing_commit_hash_pd']:
                bic_pd.append(d["fix_commit_hash"])

        path.append({
            "Repository": repository,
            "fix_commit": fix_commit,
            "Fix in BIC pyszz": bic_pyszz,
            "Fix in BIC pydriller": bic_pd
        })

    with open('./relations/commit_path.json', 'w') as f:
        json.dump(path, f, indent=4)