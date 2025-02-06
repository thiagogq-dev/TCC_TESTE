import requests
import json
import os
import datetime
import logging

from utils.utils import check_commit_existence, check_commit_existence_pd, get_commit_that_references_pr, get_commit_that_references_issue, get_commit_pr, get_pull_request_language 

if not os.path.exists("logs"):
    os.makedirs("logs")

# Set Up INFO Log
general_log = logging.getLogger("general_log")
general_log.setLevel(logging.INFO)

general_log_handler = logging.FileHandler("logs/general.log")
general_log_handler.setLevel(logging.INFO)

general_log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
general_log_handler.setFormatter(general_log_formatter)

general_log.addHandler(general_log_handler)

# Set Up ERROR Log
error_log = logging.getLogger("error_log")
error_log.setLevel(logging.ERROR)

error_log_handler = logging.FileHandler("logs/error.log")
error_log_handler.setLevel(logging.ERROR)

error_log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
error_log_handler.setFormatter(error_log_formatter)

error_log.addHandler(error_log_handler)

# Set Up WARNING Log
warning_log = logging.getLogger("warning_log")
warning_log.setLevel(logging.WARNING)

warning_log_handler = logging.FileHandler("logs/warning.log")
warning_log_handler.setLevel(logging.WARNING)

warning_log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
warning_log_handler.setFormatter(warning_log_formatter)

warning_log.addHandler(warning_log_handler)

def log_message(message, level):
    if level == "info":
        general_log.info(message)
    elif level == "error":
        error_log.error(message)
    elif level == "warning":
        warning_log.warning(message)

API_TOKENS = [
    os.getenv('API_TOKEN_1'),
    os.getenv('API_TOKEN_2'),
    os.getenv('API_TOKEN_3'),
    os.getenv('API_TOKEN_4'),
    os.getenv('API_TOKEN_5'),
    os.getenv('API_TOKEN_6'),
    os.getenv('API_TOKEN_7'),
    os.getenv('API_TOKEN_8'),
    os.getenv('API_TOKEN_9'),
    os.getenv('API_TOKEN_10')
]

token_index = 0
graph_ql_url = 'https://api.github.com/graphql'

def define_query(issue_number, repo):
    owner, name = repo.split("/")

    query = f'''
        {{
            repository(name: "{name}", owner: "{owner}") {{
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
                                        commits(last: 1) {{
                                            nodes {{
                                                commit {{
                                                    oid
                                                }}
                                            }}
                                        }}
                                        mergeCommit {{
                                            oid
                                        }}
                                        author {{
                                            login
                                        }}
                                    }}
                                    ... on Commit {{
                                        oid
                                        committedDate
                                        messageHeadline
                                        url
                                        author {{
                                            user {{
                                                login
                                            }}
                                        }}
                                        associatedPullRequests(first: 1) {{
                                            nodes {{
                                                number
                                                title
                                                createdAt
                                                mergedAt
                                                url
                                                commits(last: 1) {{
                                                    nodes {{
                                                        commit {{
                                                            oid
                                                        }}
                                                    }}
                                                }}
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
        
    return query

def execute_query(query, headers):
    response = requests.post(graph_ql_url, headers=headers, json={'query': query})

    if response.status_code == 403:
        switch_token()
        headers = get_headers()
        response = requests.post(graph_ql_url, headers=headers, json={'query': query})

    return response.json()

def check_data(data):
    if "errors" in data:
        return True
    return False

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
    
    if rate_limit == 0:
        switch_token()

def get_data(url, repo_name, repo, full_data):
    headers = get_headers()

    pages_remaining = True
    show_total_count = True

    while pages_remaining:
        log_message(f"Getting data from {url}", "info")
        response = requests.get(url, headers=headers)

        if response.status_code == 403:
            switch_token()
            headers = get_headers()
            response = requests.get(url, headers=headers)

        if show_total_count:
            total_count = response.json()["total_count"]
            log_message(f"Total count: {total_count}", "info")
            show_total_count = False

        data = response.json()["items"]
        read = 0
        for issue in data:
            read += 1
            issue_number = issue["number"]
            log_message(f"Reading issue {issue_number} - {read}/{len(data)}", "info")

            query = define_query(issue_number, repo)
            query_response = execute_query(query, headers)

            issue_labels = [label["name"] for label in issue["labels"]]

            if check_data(query_response):
                print("Error in data")
                return full_data, True

            if query_response['data']['repository']['issue']['timelineItems']['nodes'] == []:
                log_message(f"Missing data for issue {issue_number} in {repo_name}", "warning")
                continue

            closer = query_response['data']['repository']['issue']['timelineItems']['nodes'][0]['closer']

            if closer is None:
                    log_message(f"Missing data for issue {issue_number} in {repo_name}", "warning")
                    continue
            elif closer['__typename'] == 'PullRequest':
                pr_number = closer['number']
                # pr_title = closer['title']
                # if closer['author'] is None:
                #     pr_created_by = "ghost"
                # else:
                #     pr_created_by = closer['author']['login']
                # pr_created_at = closer['createdAt']
                # pr_merged_at = closer['mergedAt']
                # pr_html_url = closer['url']
                if closer['mergeCommit'] is None:
                    log_message(f"PR {pr_number} without merge commit - Issue {issue_number}", "error")
                    merge_commit = get_commit_pr(repo, closer['commits']['nodes'][0]['commit']['oid'], headers)
                    pr_merge_commit_sha = merge_commit
                else:
                    pr_merge_commit_sha = closer['mergeCommit']['oid']

                if not check_commit_existence_pd(f"./repos_dir/{repo}", pr_merge_commit_sha):
                    log_message(f"PR {pr_number} merge commit does not exist in PyDriller- Issue {issue_number}", "error")
                    pr_merge_commit_sha = get_commit_that_references_pr(repo, pr_number, headers, issue_number)
                
                tipo = "PR"

                check_rate_limit(headers)
                headers = get_headers()
                # pr_language = get_pull_request_language(repo, headers, pr_number)
            elif closer['__typename'] == 'Commit':
                if len(closer['associatedPullRequests']['nodes']) == 0:
                    log_message(f"Commit of issue {issue_number} without associated PR", "error")
                    # pr_created_by = closer['author']['user']['login']
                    # pr_merged_at = closer['committedDate']
                    pr_merge_commit_sha = closer['oid']
                    # pr_title = closer['messageHeadline']
                    # pr_html_url = closer['url']
                    pr_number = None
                    # pr_created_at = None
                    # pr_language = None
                    tipo = "Commit"
                else:
                    pr_number = closer['associatedPullRequests']['nodes'][0]['number']
                    # pr_title = closer['associatedPullRequests']['nodes'][0]['title']
                    # pr_created_by = closer['associatedPullRequests']['nodes'][0]['author']['login']
                    # pr_created_at = closer['associatedPullRequests']['nodes'][0]['createdAt']
                    # pr_merged_at = closer['associatedPullRequests']['nodes'][0]['mergedAt']
                    # pr_html_url = closer['associatedPullRequests']['nodes'][0]['url']
                    pr_merge_commit_sha = closer['oid']  
                    tipo = "Commit"

                    if not check_commit_existence_pd(f"./repos_dir/{repo}", pr_merge_commit_sha):
                        log_message(f"Commit {pr_merge_commit_sha} does not exist in PyDriller - Issue {issue_number}", "error")
                        pr_merge_commit_sha = get_commit_that_references_pr(repo, pr_number, headers, issue_number)
                        tipo = "Commit NF - PR"

                    check_rate_limit(headers)
                    headers = get_headers()
                    # pr_language = get_pull_request_language(repo, headers, pr_number)
            else:
                log_message(f"Missing data for issue {issue_number} in {repo_name}", "warning")
                continue
            
            full_data.append({
                "repo_name": repo_name,
                "repo_url": repo,
                # "issue_title": issue["title"],
                # "issue_created_by": issue["user"]["login"],
                # "issue_labels": issue_labels,
                # "issue_number": issue["number"],
                "issue_html_url": issue["html_url"],
                "earliest_issue_date": issue["created_at"],
                # "issue_closed_at": issue["closed_at"],
                # "pr_title": pr_title,
                # "pr_language": pr_language,
                # "pr_created_by": pr_created_by,
                # "pr_number": pr_number,
                # "pr_html_url": pr_html_url,
                # "pr_created_at": pr_created_at,
                # "pr_merged_at": pr_merged_at,
                "fix_commit_hash": pr_merge_commit_sha,
                "tipo": tipo
            })

        if 'next' in response.links: 
            url = response.links['next']['url']
        else:
            pages_remaining = False

    return full_data, False        

   
def get_issues(repos):
    full_data = []

    for repo in repos:
        repo_name = repo.split("/")[1]

        if not os.path.exists(f"repos_dir/{repo}"):
            print(f"Cloning {repo}")
            os.system(f"git clone https://github.com/{repo}.git repos_dir/{repo}")

        url = f'https://api.github.com/search/issues?q=is:issue%20repo:{repo}%20is:closed&sort=created&order=asc&per_page=100'
        response = requests.get(url)
        data = response.json()["items"]
        
        start_date = data[0]["created_at"].split("T")[0]
        today = datetime.datetime.now().date()
        today.strftime('%Y-%m-%d')
        
        delta = datetime.timedelta(days=365)
        # start_date = "2023-06-11"
        start_date =  datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        current_start_date = start_date

        while current_start_date < today:
            current_end_date = current_start_date + delta
            if current_end_date > today:
                current_end_date = today
            url = f'https://api.github.com/search/issues?q=is:issue%20repo:{repo}%20is:closed%20created:{current_start_date}..{current_end_date}&per_page=100'
            full_data, state = get_data(url, repo_name, repo, full_data)
            if state:
                break
            current_start_date = current_end_date + datetime.timedelta(days=1)

    if not os.path.exists("json/raw_data"):
        os.makedirs("json/raw_data")

    with open('./json/raw_data/issues.json', 'w') as f:
        json.dump(full_data, f)

with open('repos_name.txt') as f:
    repos = f.readlines()
    repos = [x.strip() for x in repos]

get_issues(repos)
