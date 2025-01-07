import json
import os
import sys
import requests

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
    
def get_commit_pr(commit_hash):
    headers = get_headers()
    check_rate_limit(headers)
    response = requests.get(f'https://api.github.com/repos/JabRef/jabref/commits/{commit_hash}/pulls', headers=headers)
    
    if response.status_code == 403:
        headers = get_headers()
        response = requests.get(f'https://api.github.com/repos/JabRef/jabref/commits/{commit_hash}/pulls', headers=headers)
    
    if response.status_code == 404:
        return None
    
    data = response.json()
    if len(data) == 0:
        return None
    else:
        return data[0]["html_url"]
    
def process_file(file_path):
    with open(file_path) as f:
        data = json.load(f)
        for record in data:
            print(f'Processing {record["fix_commit_hash"]}')
            commit_pr = get_commit_pr(record["fix_commit_hash"])
            record["pr_html_url"] = commit_pr
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_commit_pr.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    process_file(file_path)