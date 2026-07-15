import json
import argparse
import os

def main(input_folder: str) -> None:
    """
   Divide os arquivos JSON de entrada em dois grupos: issues classificadas como 'bug' e issues não relacionadas a bugs. Em seguida, salva cada grupo em arquivos JSON separados na pasta de saída.
    Args:
        input_folder (str): Caminho para a pasta contendo os arquivos JSON de entrada.
    """

    os.makedirs(os.path.join(input_folder, "bug_issues"), exist_ok=True)
    os.makedirs(os.path.join(input_folder, "no_bug_issues"), exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            input_file = os.path.join(input_folder, filename)
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            bug_issues = []
            no_bug_issues = []
            for entry in data:
                if entry.get("predicted_class") == 'bug':
                    bug_issues.append(entry)
                else:
                    no_bug_issues.append(entry)

            if bug_issues:
                output_file_path_bug = os.path.join(input_folder, "bug_issues", filename)
                with open(output_file_path_bug, "w", encoding="utf-8") as f:
                    json.dump(bug_issues, f, indent=4)
                print(f"Arquivo JSON com issues de bug salvo em: {output_file_path_bug}")

            if no_bug_issues:
                output_file_path_no_bug = os.path.join(input_folder, "no_bug_issues", filename)
                with open(output_file_path_no_bug, "w", encoding="utf-8") as f:
                    json.dump(no_bug_issues, f, indent=4)
                print(f"Arquivo JSON com issues não relacionadas a bugs salvo em: {output_file_path_no_bug}")

if __name__ == "__main__":
    main("./dataset/2-classificados_llm")
