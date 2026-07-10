import json
import argparse
from utils.utils import split_json_file

OUTPUT_FOLDER = "./data"

def main(input_file: str, file_prefix: str) -> None:
    """
    Prepara os dados para análise SZZ, filtrando apenas as issues classificados como 'bug' e dividindo o arquivo JSON resultante em arquivos menores.
    A serem utilizados na análise SZZ.
    Args:
        input_file (str): Caminho para o arquivo JSON de entrada contendo os dados coletados.
        file_prefix (str): Prefixo para os arquivos de saída. 
    """
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    data_to_split = []
    for entry in data:
        if entry.get("predicted_class") == 'bug':
            data_to_split.append(entry)

    if data_to_split:
        if not file_prefix:
            file_prefix = data_to_split[0].get("repo_name")
        split_json_file(data_to_split, OUTPUT_FOLDER, file_prefix, 50)
        print(f"Arquivo {input_file} processado e dividido em arquivos menores na pasta {OUTPUT_FOLDER}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepara os dados para análise SZZ, filtrando apenas as issues classificadas como 'bug' e dividindo o arquivo JSON resultante em arquivos menores.")
    parser.add_argument("input_file", help="Caminho para o arquivo JSON de entrada contendo os dados coletados.")
    parser.add_argument("file_prefix", help="Prefixo para os arquivos de saída. Se não fornecido, será usado o nome do repositório do primeiro registro.")
    args = parser.parse_args()
    main(args.input_file, args.file_prefix)
