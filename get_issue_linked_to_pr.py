import requests
import json
import sys
import os

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

name = "jabref"
owner = "JabRef"
url = 'https://api.github.com/graphql'
# pr_number = 4918

def get_issues(pr_number):
    query = f"""
        {{
            repository(owner: "{owner}", name: "{name}") {{
                pullRequest(number: {pr_number}) {{
                    closingIssuesReferences(first: 10) {{
                        nodes {{
                            number
                            url
                        }}
                    }}
                }}
            }}
        }}
    """

    headers = get_headers()
    check_rate_limit(headers)

    issues = []

    r = requests.post(url=url, json={'query': query}, headers=headers)

    if r.status_code == 403:
        headers = get_headers()

    r = requests.post(url=url, json={'query': query}, headers=headers)
    data = r.json()

    for issue in data["data"]["repository"]["pullRequest"]["closingIssuesReferences"]["nodes"]:
        issues.append(issue["url"])

    return issues


def process_file(file_path):
    with open(file_path) as f:
        data = json.load(f)
        
        for record in data:
            if record["pr_url"] is None:
                record["issues"] = None
            else:
                pr_number = record["pr_url"].split("/")[-1]
                issues = get_issues(pr_number)
                record["issues"] = issues
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_commit_pr.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    process_file(file_path)
