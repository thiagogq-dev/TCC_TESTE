from pyvis.network import Network
import pyvis
import json

def get_data_in_json(filename, hash):
    with open(filename) as f:
        data = json.load(f)

    for d in data:
        if d["fix_commit_hash"] == hash:
            return d

def generate_ramdom_color():
    import random
    r = lambda: random.randint(0, 255)
    return '#%02X%02X%02X' % (r(), r(), r())

with open('./commit_path.json', 'r') as file:
    data = json.load(file)

existing_edges = set()

net = Network(
    notebook=True, 
    cdn_resources="remote",
    select_menu=True,
    filter_menu=True,
    directed=True
)

for item in data:
    # if len(item["Fix in BIC pyszz"]) == 0 and len(item["Fix in BIC pydriller"]) == 0:
    #     continue
    if len(item["Fix in BIC"]) == 0:
        continue
    fix_commit = item["fix_commit"]
    fix_data = get_data_in_json("../json/consolidated_data.json", fix_commit)
    net.add_node(
        fix_commit, 
        label=fix_commit, 
        color=generate_ramdom_color(), 
        title=f"Repository: {fix_data['repo_url']}\n Issue Fix: {fix_data['issue_number']} \n  PR Fix: {fix_data['pr_number']} \n Fix Commit: {fix_data['fix_commit_hash']}"
    )

    # for bic in item["Fix in BIC pyszz"] + item["Fix in BIC pydriller"]:
    for bic in item["Fix in BIC"]:
        edge_key = (fix_commit, bic)
        if edge_key not in existing_edges:
            data = get_data_in_json("../json/consolidated_data.json", bic)
            net.add_node(bic, label=bic, title=f"Repository: {data['repo_url']}\n Issue Fix: {data['issue_number']} \n  PR Fix: {data['pr_number']} \n Fix Commit: {data['fix_commit_hash']}")
            net.add_edge(fix_commit, bic, arrowStrikethrough=False)
            existing_edges.add(edge_key)

net.show('./commit_path.html')