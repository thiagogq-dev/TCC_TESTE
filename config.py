import os

if not os.path.exists('pyszz_v2/repos_dir'):
    os.makedirs('pyszz_v2/repos_dir')

if not os.path.exists('bug_fix_commits'):
    os.makedirs('bug_fix_commits')

with open('repos_name.txt') as f:
    repos = f.readlines()
    repos = [x.strip() for x in repos]

for repo in repos:
    repo_name = repo.split('/')[1]
    repo_path = os.path.join('pyszz_v2/repos_dir', repo_name)
    if not os.path.exists(repo_path):
        print(f"Clonando o repositório {repo}.")
        os.system(f"git clone https://github.com/{repo}.git {repo_path}")
        print(f"O repositório {repo} foi clonado.")
    else:
        os.chdir('pyszz_v2/repos_dir/' + repo_name)
        os.system("git fetch origin")
        os.system("git pull")
        print(f"O repositório {repo} foi atualizado.")
