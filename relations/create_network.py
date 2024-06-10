from pyvis.network import Network
import pyvis
import json

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
    fix_commit = item["fix_commit"]
    net.add_node(fix_commit, label=fix_commit, color=generate_ramdom_color(), title="teste")

    for bic in item["Fix in BIC pyszz"] + item["Fix in BIC pydriller"]:
        edge_key = (fix_commit, bic)
        if edge_key not in existing_edges:
            net.add_node(bic, label=bic)
            net.add_edge(fix_commit, bic, arrowStrikethrough=False)
            existing_edges.add(edge_key)

net.show('./commit_path.html')