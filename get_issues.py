import requests
import json
import os

from utils.utils import remove_null_prs, get_pull_request_language

API_TOKEN = os.getenv("API_TOKEN")
print(API_TOKEN)

def check_issue_pr(pr_urls, headers, repo):
    prs = []

    print(pr_urls)

    for url in pr_urls:
        response = requests.get(url, headers=headers)
        if response.json()["merged_at"] == None:
            continue
        else:
            prs.append({
                "title": response.json()["title"],
                "language": get_pull_request_language(repo, headers, response.json()["number"]),
                "created_by": response.json()["user"]["login"], 
                "created_at": response.json()["created_at"],
                "merged_at": response.json()["merged_at"],
                "html_url": response.json()["html_url"],
                "number": response.json()["number"],
                "merge_commit_sha": response.json()["merge_commit_sha"],
                "last_commit_sha": response.json()["head"]["sha"]
            })

    if len(prs) == 0:
        return None, None, None, None, None, None, None, None, None
    else:
        pr = prs[0]
        for i in range(1, len(prs)):
            if prs[i]["merged_at"] > pr["merged_at"]:
                pr = prs[i]

    if repo in pr["html_url"]:
        return pr["title"], pr["language"], pr["created_by"], pr["created_at"], pr["merged_at"], pr["html_url"], pr["number"], pr["merge_commit_sha"], pr["last_commit_sha"]
    else:
        return None, None, None, None, None, None, None, None, None
    
def get_data(url, repo_name, repo, full_data):
    headers = {
        'Authorization': 'token ' + API_TOKEN,
    }
    pages_remaining = True

    while pages_remaining:
        response = requests.get(url, headers=headers)
        data = response.json()["items"]
        read = 0
        for issue in data:
            read += 1
            print(f'{read}/{len(data)}')
            timeline_url = issue["timeline_url"]
            timeline_response = requests.get(timeline_url, headers=headers)

            issue_pr_urls = []
            
            for event in timeline_response.json():
                if "source" in event:
                    if "issue" in event["source"]:
                        if "pull_request" in event["source"]["issue"]:
                            issue_pr_urls.append(event["source"]["issue"]["pull_request"]["url"])

            if len(issue_pr_urls) == 0:
                continue
            else:
                pr_title, pr_language, pr_created_by, pr_created_at, pr_merged_at, pr_html_url, pr_number, pr_merge_commit_sha, pr_last_commit_sha = check_issue_pr(issue_pr_urls, headers, repo)

            full_data.append({
                "repo_name": repo_name,
                "repo_url": repo,
                "issue_created_by": issue["user"]["login"],
                "issue_title": issue["title"],
                "issue_number": issue["number"],
                "issue_html_url": issue["html_url"],
                "issue_created_at": issue["created_at"],
                "issue_closed_at": issue["closed_at"],
                "pr_title": pr_title,
                "pr_language": pr_language,
                "pr_created_by": pr_created_by,
                "pr_number": pr_number,
                "pr_html_url": pr_html_url,
                "pr_created_at": pr_created_at,
                "pr_merged_at": pr_merged_at,
                "fix_commit_hash": pr_merge_commit_sha,
                "pr_last_commit_sha": pr_last_commit_sha
            })

        if 'next' in response.links: 
            url = response.links['next']['url']
        else:
            pages_remaining = False

    return full_data        

   
def get_issues(repos):
    full_data = []

    for repo in repos:
        repo_name = repo.split("/")[1]

        # url = f'https://api.github.com/search/issues?q=is:issue%20repo:{repo}%20is:closed&per_page=100'
        url = f'https://api.github.com/search/issues?q=is:issue%20repo:{repo}%20is:closed&sort=created&order=asc&per_page=100'
        full_data = get_data(url, repo_name, repo, full_data)
        last_item_desc = full_data[-1]["issue_created_at"]

        url = f'https://api.github.com/search/issues?q=is:issue%20repo:{repo}%20is:closed&sort=created&order=desc&per_page=100'
        full_data = get_data(url, repo_name, repo, full_data)
        first_item_desc = full_data[-1]["issue_created_at"]

        start_date = min(last_item_desc, first_item_desc)
        end_date = max(last_item_desc, first_item_desc)

        url = f'https://api.github.com/search/issues?q=is:issue%20repo:{repo}%20is:closed%20created:{start_date}..{end_date}&sort=created&order=asc&per_page=100'
        full_data = get_data(url, repo_name, repo, full_data)

        full_data = [dict(t) for t in {tuple(d.items()) for d in full_data}]

    if not os.path.exists("json"):
        os.makedirs("json")

    with open('./json/raw_data/issues.json', 'w') as f:
        json.dump(full_data, f)

with open('repos_name.txt') as f:
    repos = f.readlines()
    repos = [x.strip() for x in repos]

get_issues(repos)
remove_null_prs("json/raw_data/issues.json")
