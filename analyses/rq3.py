"""
Scripta para análise da RQ3: Comparação entre FIX e BIC em relação à presença de alterações em testes.
O script lê arquivos JSON contendo informações sobre commits FIX e seus respectivos BICs, e classifica cada par (FIX, BIC) em quatro categorias:
1. Ambos têm alterações em testes
2. Apenas o FIX tem alterações em testes
3. Apenas o BIC tem alterações em testes
4. Nenhum tem alterações em testes
O resultado é salvo em um arquivo CSV, que pode ser usado para análises estatísticas posteriores
"""

import os
import json
import glob
import pandas as pd
from utils.utils import format_percentage

OUTPUT_FOLDER = "./results/rq3"

if __name__ == "__main__":
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    dados_tabela = []

    for json_file in os.listdir('./dataset/4-metricas/pair_bic_fix'):
        if not json_file.endswith('.json'):
            continue
        repo_name = os.path.basename(json_file).replace('.json', '')
        
        path = os.path.join('./dataset/4-metricas/pair_bic_fix', json_file)
        with open(path, 'r') as f:
            data = json.load(f)

        commit_map = {
            entry['fix_commit_hash']: entry
            for entry in data
        }

        # Contadores
        bic_fix = 0   # FIX com teste + BIC com teste (Ambos)
        bic = 0       # FIX sem teste + BIC com teste (Apenas BIC)
        fix = 0       # FIX com teste + BIC sem teste (Apenas FIX)
        none = 0      # FIX sem teste + BIC sem teste (Nenhum)

        # Para cada BIC no dataset
        for entry in data:
            fix_has_asserts_changes = entry.get('test_files_with_asserts_changes', 0) > 0
            bics = entry.get('bic', [])

            # Para cada BIC associado ao FIX
            for bic_hash in bics:
                bic_entry = commit_map.get(bic_hash)

                # Se o BIC não estiver no dataset, ignora
                if not bic_entry:
                    continue

                bic_has_asserts_changes = bic_entry.get('test_files_with_asserts_changes', 0) > 0

                # Classificação do par (FIX, BIC)
                if fix_has_asserts_changes and bic_has_asserts_changes: # Ambos tem alterações em testes
                    bic_fix += 1
                elif fix_has_asserts_changes and not bic_has_asserts_changes: # Apenas FIX tem alterações em testes
                    fix += 1
                elif not fix_has_asserts_changes and bic_has_asserts_changes: # Apenas BIC tem alterações em testes
                    bic += 1
                else: # Nenhum tem alterações em testes
                    none += 1

        # Adiciona a linha do repositório na nossa lista de dados
        total_pares = bic_fix + bic + fix + none

        dados_tabela.append({
            "Repositório": repo_name,
            "Total": total_pares,
            "Ambos": bic_fix,
            "Apenas FIX": fix,
            "Apenas BIC": bic,
            "Nenhum": none
        })
        
        print(f"Processado: {repo_name}")

    # ==========================================================
    # GERAÇÃO DAS TABELAS (CSV, LaTeX e Excel)
    # ==========================================================
    if dados_tabela:
        df = pd.DataFrame(dados_tabela)

        total_row = {
            "Repositório": "Total",
            "Total": df["Total"].sum(),
            "Ambos": df["Ambos"].sum(),
            "Apenas FIX": df["Apenas FIX"].sum(),
            "Apenas BIC": df["Apenas BIC"].sum(),
            "Nenhum": df["Nenhum"].sum()
        }
        df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

        # 2. Calcula as porcentagens
        df["Ambos %"] = (df["Ambos"] / df["Total"] * 100).fillna(0).apply(format_percentage)
        df["Apenas FIX %"] = (df["Apenas FIX"] / df["Total"] * 100).fillna(0).apply(format_percentage)
        df["Apenas BIC %"] = (df["Apenas BIC"] / df["Total"] * 100).fillna(0).apply(format_percentage)
        df["Nenhum %"] = (df["Nenhum"] / df["Total"] * 100).fillna(0).apply(format_percentage)

        colunas_ordenadas = [
            "Repositório", "Total", 
            "Ambos", "Ambos %", 
            "Apenas FIX", "Apenas FIX %", 
            "Apenas BIC", "Apenas BIC %", 
            "Nenhum", "Nenhum %"
        ]
        df = df[colunas_ordenadas]
        # 1. Exporta para CSV
        csv_path = os.path.join(OUTPUT_FOLDER, "rq3.csv")
        df.to_csv(csv_path, index=False)
        print(f"\nTabela CSV salva em: {csv_path}")
        