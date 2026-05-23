import os
from utils.utils import load_data, Reporter

def calculate_test_changes(data, reporter):
    """Calcula a proporção de commits com e sem testes, e a qualidade efetiva das alterações em testes nos commits."""
    total = len(data)
    
    asserts = 0
    no_asserts = 0

    no_real_tests = 0

    weaker_asserts = 0
    stronger_asserts = 0
    maintenance_asserts = 0

    for d in data:

        if d.get("has_tests") == "Yes":
            asserts += 1

        if d.get("asserts_changes_type") == "Removed":
            weaker_asserts += 1
        elif d.get("asserts_changes_type") == "Added":
            stronger_asserts += 1
        elif d.get("asserts_changes_type") == "Maintained":
            maintenance_asserts += 1
        elif d.get("asserts_changes_type") == "None":
            no_asserts += 1
            if d.get("has_test_files"):
                no_real_tests += 1

    reporter.write("=== PROPORÇÃO DE ASSERTS NOS COMMITS ===")
    reporter.write(f"Com asserts: {asserts} ({asserts/total*100:.2f}%)")
    reporter.write(f"Sem asserts: {no_asserts} ({no_asserts/total*100:.2f}%)")
    reporter.write(f"Sem asserts com arquivos de testes: {no_real_tests} ({no_real_tests/no_asserts*100:.2f}%)")
    reporter.write(f"Com asserts mais fortes (adição de asserts): {stronger_asserts} ({stronger_asserts/asserts*100:.2f}%)")
    reporter.write(f"Com asserts mais fracos (remoção de asserts): {weaker_asserts} ({weaker_asserts/asserts*100:.2f}%)")
    reporter.write(f"Manutenção de asserts: {maintenance_asserts} ({maintenance_asserts/asserts*100:.2f}%)")
    reporter.write("")

# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    os.makedirs("./results", exist_ok=True)

    for file in sorted(os.listdir("./relations")):
        if not file.endswith(".json"):
            continue

        FOLDER_REPO_PATH = file.replace(".json", "")
        os.makedirs(f"./results/{FOLDER_REPO_PATH}", exist_ok=True)

        INPUT_PATH      = f"./relations/{file}"
        RESULTS_FOLDER  = f"./results/{FOLDER_REPO_PATH}"
        OUTPUT_PATH     = f"{RESULTS_FOLDER}/rq1_rq2.txt"

        data = load_data(INPUT_PATH)

        if os.path.exists(OUTPUT_PATH):
            open(OUTPUT_PATH, "w").close()

        reporter = Reporter(OUTPUT_PATH)

        reporter.write(f"{FOLDER_REPO_PATH}")
        reporter.write("R1: Qual é a proporção de commits que incluem alterações em asserts?\n")
        reporter.write("R2: Qual é a qualidade efetiva das alterações em asserts nos commits?\n")
        calculate_test_changes(data, reporter) 


        print(f"Análises de RQ1 e RQ2 concluídas: {file} -> {OUTPUT_PATH}")