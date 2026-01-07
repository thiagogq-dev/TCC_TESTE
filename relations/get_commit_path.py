import json
import os
import sys

# Ensure project root is on sys.path so `utils` package can be imported
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from utils.utils import (
    preload_commits_index,
    get_commit_date_from_index,
    get_contributor_activity_from_index,
)

# Caminhos relativos ao diretório do projeto (garante execução de qualquer cwd)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ISSUES_PATH = os.path.join(BASE_DIR, 'data', 'issues.json')
REPO_PATH = os.path.join(BASE_DIR, 'repos_dir', 'jabref')
OUT_PATH = os.path.join(os.path.dirname(__file__), 'commit_path.json')

# Pré-carregar commits (utilitário compartilhado)
commit_date, author_commits = preload_commits_index(REPO_PATH)

def get_commit_date(fix_commit):
    return get_commit_date_from_index(fix_commit, commit_date)

def get_contributor_activity(author, fix_date):
    return get_contributor_activity_from_index(author, fix_date, author_commits)

with open(ISSUES_PATH) as f:
    bics = json.load(f)
    path = []

    for data in bics:
        bic = []
        repository = data.get('repo_name')
        fix_commit = data.get('fix_commit_hash')

        for d in bics:
            # se o commit de correção está contido na lista de commits que causaram o bug
            # adiciona o commit que consertou o erro introduzido pelo commit de correção
            if fix_commit in d.get('bic', []):
                bic.append(d.get("fix_commit_hash"))

        # calcular contributor_activity a partir do autor e da data do commit de correção
        author = data.get('commit_author')
        fix_date = get_commit_date(fix_commit)
        activity = get_contributor_activity(author, fix_date)

        path.append({
            "Repository": repository,
            "bug_causer": fix_commit,
            "fixed_by": bic, # lista que consertaram o erro introduzido pelo commit de correção
            "has_tests": data.get("has_tests"),
            "dmm_unit_size": data.get("dmm_unit_size"),
            "dmm_unit_complexity": data.get("dmm_unit_complexity"),
            "dmm_unit_interfacing": data.get("dmm_unit_interfacing"),
            "contributor_activity": activity
        })

    with open(OUT_PATH, 'w') as f:
        json.dump(path, f, indent=4)