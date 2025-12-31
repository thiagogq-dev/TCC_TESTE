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
    if len(item["fixed_by"]) == 0:
        continue
    fix_commit = item["bug_causer"]
    fix_data = get_data_in_json("../data/issues.json", fix_commit)
    net.add_node(
        fix_commit, 
        label=fix_commit, 
        color=generate_ramdom_color(), 
        title=f"Repository: {fix_data['repo_url']}\n Issue Fix: {fix_data['issue_number']} \n  Fix Commit: {fix_data['fix_commit_hash']}"
    )

    for bic in item["fixed_by"]:
        edge_key = (fix_commit, bic)
        if edge_key not in existing_edges:
            data = get_data_in_json("../data/issues.json", bic)
            net.add_node(bic, label=bic, title=f"Repository: {data['repo_url']}\n Issue Fix: {data['issue_number']} \n  Fix Commit: {data['fix_commit_hash']}")
            net.add_edge(fix_commit, bic, arrowStrikethrough=False)
            existing_edges.add(edge_key)

net.show('./commit_path.html')