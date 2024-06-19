import requests
import json
import os
import datetime

from utils.utils import remove_null_prs, get_pull_request_language

API_TOKENS = [
    os.getenv('API_TOKEN_1'),
    os.getenv('API_TOKEN_2'),
    os.getenv('API_TOKEN_3'),
    os.getenv('API_TOKEN_4'),
    os.getenv('API_TOKEN_5'),
    os.getenv('API_TOKEN_6'),
]
token_index = 0

graph_ql_url = 'https://api.github.com/graphql'

def define_query(issue_number, repo, query_type):
    owner, name = repo.split("/")

    if query_type == "closed":
        query = f'''
            {{
                repository(name: {name}, owner: {owner}) {{
                    issue(number: {issue_number}) {{
                        timelineItems(itemTypes: CLOSED_EVENT, last: 1) {{
                            nodes {{
                                ... on ClosedEvent {{
                                    createdAt
                                    closer {{
                                    __typename
                                        ... on PullRequest {{
                                            number
                                            title
                                            createdAt
                                            mergedAt
                                            url
                                            mergeCommit {{
                                                oid
                                            }}
                                            author {{
                                                login
                                            }}
                                        }}
                                        ... on Commit {{
                                            oid
                                            associatedPullRequests(first: 1) {{
                                                nodes {{
                                                    number
                                                    title
                                                    createdAt
                                                    mergedAt
                                                    url
                                                    mergeCommit {{
                                                        oid
                                                    }}
                                                    author {{
                                                        login
                                                    }}
                                                }}
                                            }}
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
            '''
    elif query_type == "cross_reference":
        query = f'''
            {{
                repository(name: {name}, owner: {owner}) {{
                    issue(number: {issue_number}) {{
                        timelineItems(itemTypes: CROSS_REFERENCED_EVENT, last: 1) {{
                            nodes {{
                                ... on CrossReferencedEvent {{
                                    createdAt
                                    source {{
                                        __typename
                                        ... on PullRequest {{
                                            number
                                            title
                                            createdAt
                                            mergedAt
                                            url
                                            mergeCommit {{
                                                oid
                                            }}
                                            author {{
                                                login
                                            }}
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
            '''
        
    return query

def execute_query(query, headers):
    response = requests.post(graph_ql_url, headers=headers, json={'query': query})
    if response.status_code == 403:
        switch_token()
        headers = get_headers()
        response = requests.post(graph_ql_url, headers=headers, json={'query': query})
    return response.json()

def get_headers():
    return {
        'Authorization': f'token {API_TOKENS[token_index]}'
    }

def switch_token():
    global token_index
    token_index = (token_index + 1) % len(API_TOKENS)

def check_rate_limit(headers):
    response = requests.get('https://api.github.com/rate_limit', headers=headers)
    rate_limit = response.json()["rate"]["remaining"]
    reset_time = response.json()["rate"]["reset"]
    return rate_limit, reset_time

def get_data(url, repo_name, repo, full_data):
    headers = get_headers()

    pages_remaining = True

    while pages_remaining:
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
            switch_token()
            headers = get_headers()
            response = requests.get(url, headers=headers)
        data = response.json()["items"]
        for issue in data:
            issue_number = issue["number"]

            query = define_query(issue_number, repo, "closed")
            data = execute_query(query, headers)
            closer = data['data']['repository']['issue']['timelineItems']['nodes'][0]['closer']
            
            if closer['__typename'] == 'PullRequest':
                pr_number = closer['number']
                pr_title = closer['title']
                pr_created_by = closer['author']['login']
                pr_created_at = closer['createdAt']
                pr_merged_at = closer['mergedAt']
                pr_html_url = closer['url']
                pr_merge_commit_sha = closer['mergeCommit']['oid']
                pr_last_commit_sha = None
                pr_language = get_pull_request_language(pr_html_url)
            elif closer['__typename'] == 'Commit':
                pr_number = closer['associatedPullRequests']['nodes'][0]['number']
                pr_title = closer['associatedPullRequests']['nodes'][0]['title']
                pr_created_by = closer['associatedPullRequests']['nodes'][0]['author']['login']
                pr_created_at = closer['associatedPullRequests']['nodes'][0]['createdAt']
                pr_merged_at = closer['associatedPullRequests']['nodes'][0]['mergedAt']
                pr_html_url = closer['associatedPullRequests']['nodes'][0]['url']
                pr_merge_commit_sha = closer['associatedPullRequests']['nodes'][0]['mergeCommit']['oid']
                pr_last_commit_sha = closer['oid']
                pr_language = get_pull_request_language(pr_html_url)
            else:
                define_query(issue_number, repo, "cross_reference")
                data = execute_query(query, headers)
                pr_number = data['data']['repository']['issue']['timelineItems']['nodes'][0]['source']['number']
                pr_title = data['data']['repository']['issue']['timelineItems']['nodes'][0]['source']['title']
                pr_created_by = data['data']['repository']['issue']['timelineItems']['nodes'][0]['source']['author']['login']
                pr_created_at = data['data']['repository']['issue']['timelineItems']['nodes'][0]['source']['createdAt']
                pr_merged_at = data['data']['repository']['issue']['timelineItems']['nodes'][0]['source']['mergedAt']
                pr_html_url = data['data']['repository']['issue']['timelineItems']['nodes'][0]['source']['url']
                pr_merge_commit_sha = data['data']['repository']['issue']['timelineItems']['nodes'][0]['source']['mergeCommit']['oid']

            if data["data"]["repository"]["issue"]["timelineItems"]["nodes"] == []:
                continue

            # if pr_title == None or pr_language == None or pr_created_by == None or pr_created_at == None or pr_merged_at == None or pr_html_url == None or pr_number == None or pr_merge_commit_sha == None or pr_last_commit_sha == None:
                # continue

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

        url = f'https://api.github.com/search/issues?q=is:issue%20repo:{repo}%20is:closed&sort=created&order=asc&per_page=100'
        response = requests.get(url)
        data = response.json()["items"]
        
        start_date = data[0]["created_at"].split("T")[0]
        today = datetime.datetime.now().date()
        today.strftime('%Y-%m-%d')
        
        delta = datetime.timedelta(days=365)
        start_date =  datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        current_start_date = start_date

        while current_start_date < today:
            current_end_date = current_start_date + delta
            if current_end_date > today:
                current_end_date = today
            url = f'https://api.github.com/search/issues?q=is:issue%20repo:{repo}%20is:closed%20created:{current_start_date}..{current_end_date}&per_page=100'
            full_data = get_data(url, repo_name, repo, full_data)
            current_start_date = current_end_date + datetime.timedelta(days=1)

        full_data = [dict(t) for t in {tuple(d.items()) for d in full_data}]

    if not os.path.exists("json/raw_data"):
        os.makedirs("json/raw_data")

    with open('./json/raw_data/issues.json', 'w') as f:
        json.dump(full_data, f)

with open('repos_name.txt') as f:
    repos = f.readlines()
    repos = [x.strip() for x in repos]

get_issues(repos)
remove_null_prs("json/raw_data/issues.json")
