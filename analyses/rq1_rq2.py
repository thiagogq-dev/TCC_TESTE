import os
import pandas as pd
from utils.utils import load_data, format_percentage
import argparse

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

    return {
        "Total": total,
        "Adição": stronger_asserts,
        "Remoção": weaker_asserts,
        "Manutenção": maintenance_asserts,
        "Negligenciado": no_asserts,
    }

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Calcula a qualidade efetiva das alterações em testes nos commits.")
    arg_parser.add_argument("input_folder", type=str, help="Pasta contendo os arquivos JSON de entrada.")
    args = arg_parser.parse_args()

    last_subfolder = os.path.basename(os.path.normpath(args.input_folder))

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    dados_tabela = []

    for file in sorted(os.listdir(args.input_folder)):
        if not file.endswith(".json"):
            continue

        repo_name = file.replace(".json", "")
        input_path = f"{args.input_folder}/{file}"

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

        total_row = {
            "Repositório": "Total",
            "Total": df["Total"].sum(),
            "Adição": df["Adição"].sum(),
            "Remoção": df["Remoção"].sum(),
            "Manutenção": df["Manutenção"].sum(),
            "Negligenciado": df["Negligenciado"].sum(),
        }

        df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

        df["Adição %"] = (df["Adição"] / df["Total"] * 100).apply(format_percentage)
        df["Remoção %"] = (df["Remoção"] / df["Total"] * 100).apply(format_percentage)
        df["Adaptação. %"] = (df["Manutenção"] / df["Total"] * 100).apply(format_percentage)
        df["Neglig. %"] = (df["Negligenciado"] / df["Total"] * 100).apply(format_percentage)

        colunas_ordenadas = [
            "Repositório", "Total", 
            "Adição", "Adição %", 
            "Remoção", "Remoção %", 
            "Manutenção", "Adaptação. %", 
            "Negligenciado", "Neglig. %"
        ]

        df = df[colunas_ordenadas]
        
        # CSV
        csv_path = os.path.join(OUTPUT_FOLDER, f"rq1_rq2_{last_subfolder}.csv")
        df.to_csv(csv_path, index=False)
        print(f"\nTabela consolidada salva em: {csv_path}")