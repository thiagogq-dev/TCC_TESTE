import os
import json
import glob
import pandas as pd

if __name__ == "__main__":
    os.makedirs("./results", exist_ok=True)
    
    json_files = glob.glob('./relations/*.json')
    dados_tabela = []

    for json_file in sorted(json_files):
        repo_name = os.path.basename(json_file).replace('.json', '')
        
        with open(json_file, 'r') as f:
            data = json.load(f)

        commit_map = {
            entry['commit']: entry
            for entry in data
        }

        # Contadores
        bic_fix = 0   # FIX com teste + BIC com teste (Ambos)
        bic = 0       # FIX sem teste + BIC com teste (Apenas BIC)
        fix = 0       # FIX com teste + BIC sem teste (Apenas FIX)
        none = 0      # FIX sem teste + BIC sem teste (Nenhum)

        # Para cada BIC no dataset
        for entry in data:
            bic_has_asserts_changes = entry.get('test_files_with_asserts_changes', 0) > 0
            fix_hashes = entry.get('fixed_by', [])

            # Para cada FIX associado ao BIC
            for fix_hash in fix_hashes:
                fix_entry = commit_map.get(fix_hash)

                # Se o FIX não estiver no dataset, ignora
                if not fix_entry:
                    continue

                fix_has_asserts_changes = fix_entry.get('test_files_with_asserts_changes', 0) > 0

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
        dados_tabela.append({
            "Repositório": repo_name,
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
        
        # 1. Exporta para CSV
        csv_path = "./results/tabela_rq3.csv"
        df.to_csv(csv_path, index=False)
        print(f"\nTabela CSV salva em: {csv_path}")

        # 2. Exporta para LaTeX (pronto para o artigo, alinhado: left e 4 rights)
        # latex_path = "./results/tabela_rq3.tex"
        # with open(latex_path, "w") as f:
        #     f.write(df.to_latex(index=False, column_format="lrrrr"))
        # print(f"Código LaTeX gerado em: {latex_path}")
        