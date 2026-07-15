import json
import os
from utils.utils import group_file_by_fix, remove_duplicates

def process_folder(input_folder: str, output_folder: str) -> None:
    """
    Processa todos os arquivos JSON em uma pasta de entrada, criando novos registros para cada BIC que não seja um fix commit.
    O arquivo gerado será usado nas análises de cadeias de commits, garantindo que cada BIC seja tratado como um commit independente.
    Args:
        input_folder (str): Caminho para a pasta contendo os arquivos JSON de entrada.
        output_folder (str): Caminho para a pasta onde os arquivos JSON de saída serão salvos.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            input_path = os.path.join(input_folder, filename)

            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            result_with_bic = []
            result_pair = []
            existing_fixes = []

            for item in data:
                if len(item.get("bic", [])) > 0: # Lista dos commits de correção (fix_commit_hash) que possuem BICs
                    result_with_bic.append({
                        "repo_name": item["repo_name"],
                        "fix_commit_hash": item["fix_commit_hash"],
                        "bic": item.get("bic", [])
                    })

                result_pair.append({ # Lista que terá todos os commits de correção (fix_commit_hash) e seus BICs, incluindo os BICs que não são commits de correção
                    "repo_name": item["repo_name"],
                    "fix_commit_hash": item["fix_commit_hash"],
                    "bic": item.get("bic", [])
                })
                existing_fixes.append(item["fix_commit_hash"])

            for item in data:
                for bic in item.get("bic", []):
                    if bic not in existing_fixes:
                        new_item = {
                            "repo_name": item["repo_name"],
                            "fix_commit_hash": bic,  # o BIC passa a ser o commit
                            "bic": []                # sem filhos conhecidos
                        }
                        result_pair.append(new_item)
                        existing_fixes.append(bic)

            grouped_data_with_bic = group_file_by_fix(result_with_bic)
            final_result_with_bic = remove_duplicates(grouped_data_with_bic)  
            os.makedirs(os.path.join(output_folder, "with_bic"), exist_ok=True)
            with open(os.path.join(output_folder, "with_bic", filename), "w", encoding="utf-8") as f:
                json.dump(final_result_with_bic, f, indent=4, ensure_ascii=False)

            grouped_data = group_file_by_fix(result_pair)
            final_result = remove_duplicates(grouped_data)
            os.makedirs(os.path.join(output_folder, "final_pairs"), exist_ok=True)
            with open(os.path.join(output_folder, "final_pairs", filename), "w", encoding="utf-8") as f:
                json.dump(final_result, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    process_folder("./dataset/3-szz/with_bic", "./dataset2/4-szz")