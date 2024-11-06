import json
import requests

def remove_duplicates(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    seen = set()
    unique_data = []

    for item in data:
        identifier = json.dumps(item, sort_keys=True)  # Converte o registro inteiro em uma string JSON
        if identifier not in seen:
            seen.add(identifier)
            unique_data.append(item)

    with open(output_file, 'w') as f:
        json.dump(unique_data, f, indent=4)

# Defina o nome do arquivo de entrada e saída
input_file = "./json/raw_data/issues.json"
output_file = "./json/raw_data/issues_no_duplicates.json"

# remove_duplicates(input_file, output_file)

token1 = ""
token2 =""


headers = {
    "Authorization": f"token {token1}"
}

txt_file = "commits.txt"

def check_commit_existence(input_file):
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    for item in data:
        commit = item["fix_commit_hash"]
        issue_number = item["issue_number"]
        url = f"https://api.github.com/repos/JabRef/jabref/commits/{commit}"
        response = requests.get(url, headers=headers)
        print(response.json())
        if response.status_code == 422:
            with open(txt_file, 'a') as f:
                f.write(f"Commit {commit} of issue {issue_number} does not exist\n")

            print(f"Commit {commit} of issue {issue_number} does not exist")

check_commit_existence("./json/raw_data/issues.json")
