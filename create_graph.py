from pyvis.network import Network
import json
import os
import random


def generate_random_color():
    r = lambda: random.randint(0, 255)
    return '#%02X%02X%02X' % (r(), r(), r())

INPUT_FOLDER = "./dataset/4-metricas/with_bic"

for file in os.listdir(INPUT_FOLDER):
    if file.endswith('.json'):
        output_base_file = file.split('.')[0]
        file_path = os.path.join(INPUT_FOLDER, file)

        with open(file_path) as f:
            data = json.load(f)

        commit_index = {item["fix_commit_hash"]: item for item in data}

        net = Network(
            notebook=True,
            cdn_resources="remote",
            select_menu=True,
            filter_menu=True,
            directed=True
        )

        existing_nodes = set()
        existing_edges = set()

        for item in data:
            fix_commit = item.get("fix_commit_hash")
            bics = item.get("bic", [])

            if not bics:
                continue

            if fix_commit not in existing_nodes:
                net.add_node(
                    fix_commit,
                    label=fix_commit,
                    title=f"Repository: {item.get('repo_name', 'Unknown')}\nCommit: {fix_commit}"
                )
                existing_nodes.add(fix_commit)

            for bic in bics:
                if bic not in existing_nodes:
                    bic_meta = commit_index.get(bic)
                    repo = bic_meta.get("repo_name", "Unknown") if bic_meta else item.get("repo_name", "Unknown")
                    net.add_node(
                        bic,
                        label=bic,
                        color=generate_random_color(),
                        title=f"Repository: {repo}\nCommit: {bic}"
                    )
                    existing_nodes.add(bic)

                edge_key = (bic, fix_commit)
                if edge_key not in existing_edges:
                    net.add_edge(bic, fix_commit, arrowStrikethrough=False)
                    existing_edges.add(edge_key)
        print(f"Quantidade de pares (arestas) no arquivo {file}: {len(existing_edges)}")
        os.makedirs("./results/graph", exist_ok=True)
        net.show(f"./results/graph/{output_base_file}_v2.html")