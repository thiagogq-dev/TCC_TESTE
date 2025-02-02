from collections import defaultdict
import json
import re
import requests
import glob
from pydriller import Git, Repository

# COMMITS MANIPULATION
def check_commit_existence(repo_path, commit_hash, headers):
    url = f"https://api.github.com/repos/{repo_path}/commits/{commit_hash}"
    response = requests.get(url, headers=headers)

    if response.status_code == 422:
        return False

    return True

def check_commit_existence_pd(repo_path, commit_hash):
    gr = Git(repo_path)
    try:
        commit = gr.get_commit(commit_hash)
    except Exception as e:
        print(f"Error: {e}")
        return False

    return True


def get_commit_that_references_issue(repo_path, issue_number, headers):
    owner, name = repo_path.split("/")
    graphql_url = 'https://api.github.com/graphql'

    query = f'''
    {{
        repository(name: "{name}", owner: "{owner}") {{
            issue(number: {issue_number}) {{
                timelineItems(itemTypes: REFERENCED_EVENT, last: 1) {{
                    nodes {{
                        ... on ReferencedEvent {{
                            commit {{
                                oid
                                url
                                committedDate
                                messageHeadline
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
    '''

    response = requests.post(graphql_url, json={'query': query}, headers=headers)
    data = response.json()

    if 'data' in data and data['data']['repository']['issue']['timelineItems']['nodes'] != []:
        return data['data']['repository']['issue']['timelineItems']['nodes'][0]['commit']
    return None


def get_pr_from_issue_comments(repo_path, issue_number, headers):
    
    owner, name = repo_path.split("/")
    url = 'https://api.github.com/graphql'

    query = f"""
    {{
        repository(owner: "{owner}", name: "{name}") {{
            issue(number: {issue_number}) {{
            title
                comments(last: 100) {{
                    edges {{
                        node {{
                            body
                        }}
                    }}
                }}
            }}
        }}
    }}
    """

    response = requests.post(url, json={'query': query}, headers=headers)
    data = response.json()

    possible_prs = []

    for comment in data["data"]["repository"]["issue"]["comments"]["edges"]:
        pr = re.findall(r"#\d+", comment["node"]["body"])
        possible_prs.extend(pr)

    possible_prs = list(set(possible_prs))

    for pr in possible_prs:
        pr_number = pr.replace("#", "")

    pr_query = f"""
    {{
      repository(owner: "{owner}", name: "{name}") {{
        pullRequest(number: {pr_number}) {{
          state
          merged
          createdAt
          mergedAt
          mergeCommit {{
            oid
          }}
          url
          title
          author {{
            login 
          }}
        }}
      }}
    }}
    """

    pr_response = requests.post(url, json={'query': pr_query}, headers=headers)
    pr_data = pr_response.json()

    if 'data' in pr_data and pr_data['data']['repository']['pullRequest']['state'] == "MERGED" or pr_data['data']['repository']['pullRequest']['merged']:
        return pr_data['data']['repository']['pullRequest']
    else:
        return None


def get_commit_that_references_pr(repo_path, pr_number, headers, issue):
    owner, name = repo_path.split("/")
    graphql_url = 'https://api.github.com/graphql'

    query3 = f'''
    {{
        repository(name: "{name}", owner: "{owner}") {{
            pullRequest(number: {pr_number}) {{
                timelineItems(itemTypes: REFERENCED_EVENT, last: 1) {{
                    nodes {{
                        ... on ReferencedEvent {{
                            commit {{
                                oid
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}
    '''

    response = requests.post(graphql_url, json={'query': query3}, headers=headers)
    data = response.json()

    if 'errors' in data:
        print(f"Error in get_commit_that_references_pr for {pr_number} - issue {issue}")
        # print(data)
        return None
    if 'data' in data and data['data']['repository']['pullRequest']['timelineItems']['nodes'] != []:
        commit_node = data['data']['repository']['pullRequest']['timelineItems']['nodes'][0]['commit']
        if commit_node:
            return commit_node['oid']
        # return data['data']['repository']['pullRequest']['timelineItems']['nodes'][0]['commit']['oid']
    return None

def get_commit_pr(repo_path, commit_hash, headers):
    url = f"https://api.github.com/repos/{repo_path}/commits/{commit_hash}/pulls"
    response = requests.get(url, headers=headers)
    data = response.json()

    prs = []

    for pr in data:
        if pr["state"] == "closed":
            prs.append({
                "merged_at": pr["merged_at"],
                "merge_commit_sha": pr["merge_commit_sha"]
            })

    if len(prs) == 0:
        return None
    
    pr = max(prs, key=lambda x: x["merged_at"]) 
    return pr["merge_commit_sha"]


def get_pr_that_mentions_issue(repo_path, issue_number, headers):
    owner, name = repo_path.split("/")
    graphql_url = 'https://api.github.com/graphql'

    query = f'''
    {{
        repository(name: "{name}", owner: "{owner}") {{
            issue(number: {issue_number}) {{
                timelineItems(itemTypes: MENTIONED_EVENT, last: 1) {{
                    nodes {{
                        ... on ReferencedEvent {{
                            subject {{
                                __typename
                                ... on PullRequest {{
                                    number
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}
    '''

    response = requests.post(graphql_url, json={'query': query}, headers=headers)
    data = response.json()
    return data["data"]["repository"]["issue"]["timelineItems"]["nodes"][0]["subject"]["number"]


def match_bics(bics, bics2):
    matched = []

    for bic in bics:
       if bic in bics2:
           matched.append(bic)

    return matched


# SELECT THE MAIN LANGUAGE OF THE PULL REQUEST
def get_pull_request_language(repo, headers, pr_number):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return None

    data = response.json()

    file_changes = defaultdict(int)
    for file in data:
        file_extension = file["filename"].split(".")[-1]
        file_changes[file_extension] += file["additions"] + file["deletions"] + file["changes"]

    if max(file_changes, key=file_changes.get) == "js":
        return "Javascript"
    elif max(file_changes, key=file_changes.get) == "rb":
        return "Ruby"
    elif max(file_changes, key=file_changes.get) == "py":
        return "Python"
    elif max(file_changes, key=file_changes.get) == "java":
        return "JAVA"
    else:
        return "JAVA"

    return max(file_changes, key=file_changes.get) 


# JSON MANIPULATION
def remove_duplicates(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    seen = set()
    unique_data = []

    for item in data:
        identifier = json.dumps(item, sort_keys=True)
        if identifier not in seen:
            seen.add(identifier)
            unique_data.append(item)

    with open(output_file, 'w') as f:
        json.dump(unique_data, f, indent=4)


def format(filename):
    with open(filename, 'r') as f:
        data = json.load(f)

    formatted_data = []
    for item in data:  
        if "inducing_commit_hash_pyszz" not in item:
            print(f"Skipping {item['repo_name']} - {item['issue_title']}")
            item["inducing_commit_hash_pyszz"] = "-"
        formatted_item = {
            "repo_name": item["repo_name"],
            "repo_url": item["repo_url"],
            "Issue Title": item["issue_title"],
            "Issue Created By": item["issue_created_by"],
            "Issue Number": item["issue_number"],
            "Issue URL": item["issue_html_url"],
            "Issue Creation Date": item["issue_created_at"],
            "Issue Closing Date": item["issue_closed_at"],
            "PR Title": item["pr_title"],
            "PR Language": item["pr_language"],
            "PR Created By": item["pr_created_by"],
            "PR Number": item["pr_number"],
            "PR URL": item["pr_html_url"],
            "PR Created At": item["pr_created_at"],
            "PR Merged At": item["pr_merged_at"],
            "PR Last Commit SHA": item["pr_last_commit_sha"],
            "fix_commit_hash": item["fix_commit_hash"],
            "inducing_commit_hash_pyszz": item["inducing_commit_hash_pyszz"]
        }

        formatted_data.append(formatted_item)

    with open(filename, 'w') as f:
        json.dump(formatted_data, f, indent=4)


def remove_null_fixes(json_file):
    with open(json_file) as f:
        data = json.load(f)
        to_remove = []
        for d in data:
            if d["fix_commit_hash"] is None:
                to_remove.append(d)

        for d in to_remove:
            data.remove(d)
            
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)


def is_empty_or_dash(value):
    if value == [] or value == "-":
        return True
    return False

def remove_empty_bug_hashs(json_file):
    with open(json_file) as f:
        data = json.load(f)
        to_remove = []
        remover = 0
        for d in data:
            if is_empty_or_dash(d["inducing_commit_hash_pyszz"]) and is_empty_or_dash(d["inducing_commit_hash_pd"]):
                remover += 1
                to_remove.append(d)

        print(f"Removed {remover} items")

        for d in to_remove:
            data.remove(d)
            
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

def update_matched(json_file):
    with open(json_file) as f:
        data = json.load(f)

    for d in data:
        if not is_empty_or_dash(d["inducing_commit_hash_pyszz"]) and not is_empty_or_dash(d["inducing_commit_hash_pd"]):
            d["matched"] =d["inducing_commit_hash_pyszz"]
        elif is_empty_or_dash(d["inducing_commit_hash_pyszz"]) and not is_empty_or_dash(d["inducing_commit_hash_pd"]):
            value = d["inducing_commit_hash_pd"][0]
            d["matched"] = [value]
        elif not is_empty_or_dash(d["inducing_commit_hash_pyszz"]) and is_empty_or_dash(d["inducing_commit_hash_pd"]):
            d["matched"] = d["inducing_commit_hash_pyszz"]
        else:
            d["matched"] = []

        d.pop("inducing_commit_hash_pyszz", None)
        d.pop("inducing_commit_hash_pd", None)

    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)


def update_matched_v2(pyszz, pd, matched):
    result = []
    if matched == []:
        if not is_empty_or_dash(pyszz) and not is_empty_or_dash(pd):
            result = pyszz
        elif is_empty_or_dash(pyszz) and not is_empty_or_dash(pd):
            result = [pd[0]]
        elif not is_empty_or_dash(pyszz) and is_empty_or_dash(pd):
            result = pyszz
    else:
        result = matched

    return result
    
    
    
def remove_non_existing_commits(filename):
    with open(filename) as f:
        data = json.load(f)

    new_data = [item for item in data if item["inducing_commit_hash_pyszz"] != "-"]        

    with open(filename, 'w') as f:
        json.dump(new_data, f, indent=4)


def indent_file(filename):
    with open(filename) as f:
        data = json.load(f)

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def split_json_file(input_file, output_prefix, max_items_per_file=10):
    with open(input_file, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("The input file does not contain a JSON list.")

    chunks = [data[i:i + max_items_per_file] for i in range(0, len(data), max_items_per_file)]

    for idx, chunk in enumerate(chunks):
        output_file = f"{output_prefix}_{idx + 1}.json"
        with open(output_file, 'w') as f:
            json.dump(chunk, f, indent=4)
        print(f"File {output_file} created with {len(chunk)} items.")
              


def merge_files(folder_path, output_path):
    json_files = glob.glob(folder_path + "/*.json")
    
    combined_data = []

    for file in json_files:
        with open(file, 'r') as f:
            data = json.load(f)
            print(f'Processing {file} with {len(data)} items')
            combined_data.extend(data)


    print(f'Combined data has {len(combined_data)} items')
    with open(output_path, 'w') as f:
        json.dump(combined_data, f, indent=4)

