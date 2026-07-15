import json
import argparse
import os

def main(input_folder: str) -> None:
    """
    Divide os arquivos JSON de entrada em dois grupos: commits com BICs e commits sem BICs. Em seguida, salva cada grupo em arquivos JSON separados na pasta de saída.
    Args:
        input_folder (str): Caminho para a pasta contendo os arquivos JSON de entrada.
    """

    os.makedirs(os.path.join(input_folder, "with_bic"), exist_ok=True)
    os.makedirs(os.path.join(input_folder, "without_bic"), exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            input_file = os.path.join(input_folder, filename)
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            with_bic = []
            without_bic = []
            for entry in data:
                if len(entry.get("bic", [])) > 0:
                    with_bic.append(entry)
                else:
                    without_bic.append(entry)

            if with_bic:
                output_file_path = os.path.join(input_folder, "with_bic", filename)
                with open(output_file_path, "w", encoding="utf-8") as f:
                    json.dump(with_bic, f, indent=4)
                print(f"Arquivo JSON com commits contendo BICs salvo em: {output_file_path}")

            if without_bic:
                output_file_path = os.path.join(input_folder, "without_bic", filename)
                with open(output_file_path, "w", encoding="utf-8") as f:
                    json.dump(without_bic, f, indent=4)
                print(f"Arquivo JSON com commits sem BICs salvo em: {output_file_path}")

if __name__ == "__main__":
    main("./dataset2/3-szz")
