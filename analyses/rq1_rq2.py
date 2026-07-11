import os
import pandas as pd
from utils.utils import load_data

OUTPUT_FOLDER = "./results/rq1_rq2"

def calculate_test_changes(data):
    """
    Calcula a qualidade efetiva das alterações em testes nos commits.
    Args:
        data (list): Lista de dicionários contendo informações sobre commits e alterações em testes.
    Returns:
        dict: Dicionário contendo contadores de alterações em testes, incluindo adições, remo
    """
    total = len(data)
    
    no_asserts = 0
    no_real_tests = 0

    weaker_asserts = 0
    stronger_asserts = 0
    maintenance_asserts = 0

    for d in data:
        changes_type = d.get("asserts_changes_type")
        
        if changes_type == "Added":
            stronger_asserts += 1
        elif changes_type == "Removed":
            weaker_asserts += 1
        elif changes_type == "Maintained":
            maintenance_asserts += 1
        elif changes_type == "None": 
            no_asserts += 1
            if d.get("has_test_files"):
                no_real_tests += 1

    return {
        "Total": total,
        "Adição": stronger_asserts,
        "Remoção": weaker_asserts,
        "Manutenção": maintenance_asserts,
        "Negligenciado": no_asserts,
        "Negligenciado com arquivo de teste": no_real_tests
    }


if __name__ == "__main__":
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    dados_tabela = []

    for file in sorted(os.listdir("./relations")):
        if not file.endswith(".json"):
            continue

        repo_name = file.replace(".json", "")
        input_path = f"./relations/{file}"

        # Carrega os dados
        data = load_data(input_path)
        
        # Extrai os dados e monta a linha
        linha_repositorio = {"Repositório": repo_name}
        linha_repositorio.update(calculate_test_changes(data))
        
        dados_tabela.append(linha_repositorio)
        print(f"Processado: {repo_name}")

    # ==========================================================
    # GERAÇÃO DAS TABELAS
    # ==========================================================
    if dados_tabela:
        df = pd.DataFrame(dados_tabela)
        
        # CSV
        csv_path = os.path.join(OUTPUT_FOLDER, "rq1_rq2.csv")
        df.to_csv(csv_path, index=False)
        print(f"\nTabela consolidada salva em: {csv_path}")

        # LaTeX (ideal para copiar e colar no artigo)
        # latex_path = "./results/tabela_rq1_rq2.tex"
        # with open(latex_path, "w") as f:
        #     f.write(df.to_latex(index=False, column_format="lrrrrr"))
        # print(f"Código LaTeX gerado em: {latex_path}")