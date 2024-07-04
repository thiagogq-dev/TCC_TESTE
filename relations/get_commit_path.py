import json

with open('../json/consolidated_data.json') as f:
    bics = json.load(f)
    path = []

    for data in bics:
        bic_pyszz = []
        bic_pd = []
        bic = []
        repository = data['repo_url']
        fix_commit = data['fix_commit_hash']

        for d in bics:
            # if fix_commit in d['inducing_commit_hash_pyszz']:
            #      bic_pyszz.append(d["fix_commit_hash"])
            # if fix_commit in d['inducing_commit_hash_pd']:
            #     bic_pd.append(d["fix_commit_hash"])
            # se o commit de correção está contido na lista de commits que causaram o bug
            if fix_commit in d['matched']:
                bic.append(d["fix_commit_hash"]) # adiciona o commit de correção do fix_commit na lista 

        path.append({
            "Repository": repository, # repositório
            "fix_commit": fix_commit, # commit de correção
            "Fix in BIC": bic # lista que consertaram o erro introduzido pelo commit de correção
            # "Fix in BIC pyszz": bic_pyszz,
            # "Fix in BIC pydriller": bic_pd
        })

    with open('commit_path.json', 'w') as f:
        json.dump(path, f, indent=4)