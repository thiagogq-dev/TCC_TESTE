import json

with open('../data/issues.json') as f:
    bics = json.load(f)
    path = []

    for data in bics:
        bic = []
        repository = data['repo_name']
        fix_commit = data['fix_commit_hash']

        for d in bics:
            # se o commit de correção está contido na lista de commits que causaram o bug
            # adiciona o commit que consertou o erro introduzido pelo commit de correção
            if fix_commit in d['bic']:
                bic.append(d["fix_commit_hash"])

        path.append({
            "Repository": repository, 
            "bug_causer": fix_commit, 
            "fixed_by": bic, # lista que consertaram o erro introduzido pelo commit de correção
            "has_tests": data["has_tests"]
        })

    with open('commit_path.json', 'w') as f:
        json.dump(path, f, indent=4)