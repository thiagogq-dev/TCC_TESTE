import os
import json
import glob
import pandas as pd

OUTPUT_FOLDER = "./results/rq3"

if __name__ == "__main__":
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    dados_tabela = []

    for json_file in os.listdir('./dataset/4-metricas/with_bic'):
        if not json_file.endswith('.json'):
            continue
        repo_name = os.path.basename(json_file).replace('.json', '')
        
        path = os.path.join('./dataset/4-metricas/with_bic', json_file)
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
                    print(f"AVISO: BIC {bic_hash} não encontrado no dataset para o repositório {repo_name}.")
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
        csv_path = os.path.join(OUTPUT_FOLDER, "rq3.csv")
        df.to_csv(csv_path, index=False)
        print(f"\nTabela CSV salva em: {csv_path}")

        # 2. Exporta para LaTeX (pronto para o artigo, alinhado: left e 4 rights)
        # latex_path = os.path.join(OUTPUT_FOLDER, "rq3.tex")
        # with open(latex_path, "w") as f:
        #     f.write(df.to_latex(index=False, column_format="lrrrr"))
        # print(f"Código LaTeX gerado em: {latex_path}")
        