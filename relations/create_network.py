from pyvis.network import Network
import json
import os
import random

def get_data_in_json(filename, hash):
    with open(filename) as f:
        json_data = json.load(f)

    for d in json_data:
        if d["fix_commit_hash"] == hash:
            return d
    return None

def generate_random_color():
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
            bic = item["commit"]
            fixed_by = item.get("fixed_by", [])
            has_fix = len(fixed_by) > 0

            # 1. PULA O COMMIT SE NÃO TIVER CORREÇÕES
            # Isso garante que nós "vazios" nunca sejam adicionados ao grafo
            if not has_fix:
                continue

            # 2. ADICIONA O NÓ APENAS SE ELE TIVER RELAÇÕES
            # (Removi a condicional da cor cinza, pois agora todos os nós que chegam aqui têm correções)
            net.add_node(
                bic, 
                label=bic, 
                color=generate_random_color(), 
                title=f"Repository: {item['repository']}\n  Commit: {bic}"
            )

            for fix_commit in fixed_by:
                edge_key = (bic, fix_commit)
                if edge_key not in existing_edges:
                    # 3. CORREÇÃO DE BUG: Renomeado de 'data' para 'fix_data' para não sobrescrever o loop principal
                    fix_data = get_data_in_json(f"../szz/{output_base_file}.json", fix_commit)
                    
                    if fix_data:
                        repo_name = fix_data.get('repo_name', 'Unknown')
                        fix_hash = fix_data.get('fix_commit_hash', fix_commit)
                        
                        net.add_node(
                            fix_commit, 
                            label=fix_commit, 
                            title=f"Repository: {repo_name}\n Commit: {fix_hash}"
                        )
                        net.add_edge(bic, fix_commit, arrowStrikethrough=False)
                        existing_edges.add(edge_key)

        os.makedirs(f"../results/graph", exist_ok=True)
        net.show(f"../results/graph/{output_base_file}.html")