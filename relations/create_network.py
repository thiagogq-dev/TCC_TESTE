from pyvis.network import Network
import pyvis
import json
import os

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


for file in os.listdir('./'):
    if file.endswith('.json'):
        output_base_file = file.split('.')[0]
        output_base_folder = output_base_file
        with open(file) as f:
            data = json.load(f)


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
            bic = item["commit"]
            # fix_data = get_data_in_json(f"../analysis/{output_base_file}.json", fix_commit)
            net.add_node(
                bic, 
                label=bic, 
                color=generate_ramdom_color(), 
                title=f"Repository: {item['Repository']}\n  Commit: {bic}"
            )

            for fix_commit in item["fixed_by"]:
                edge_key = (bic, fix_commit)
                if edge_key not in existing_edges:
                    data = get_data_in_json(f"../data/{output_base_file}.json", fix_commit)
                    net.add_node(fix_commit, label=fix_commit, title=f"Repository: {data['repo_name']}\n Commit: {data['fix_commit_hash']}")
                    net.add_edge(bic, fix_commit, arrowStrikethrough=False)
                    existing_edges.add(edge_key)
            
        net.show(f"../results/{output_base_folder}/{output_base_file}.html")