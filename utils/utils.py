from collections import defaultdict
import json
import os
import requests
import glob
from pydriller import Git, Repository
from datetime import time, timedelta
from bisect import bisect_right
from utils.logger_config import log_message

ACTIVITY_BUCKETS = ["0", "1-5", "6-20", "21-100", "100+"]

def remove_duplicates(data):
    """
    Remove duplicatas de um arquivo JSON, mantendo apenas entradas únicas.
    Args:
        data (list): Lista de registros JSON.
    Returns:
        list: Lista de registros JSON sem duplicatas.
    """
    tam = len(data)
    seen = set()
    unique_data = []

    for item in data:
        identifier = json.dumps(item, sort_keys=True)
        if identifier not in seen:
            seen.add(identifier)
            unique_data.append(item)
    
    print(f'Removed {tam - len(unique_data)} duplicate items.')
    return unique_data

def split_json_file(input_data, output_folder, file_prefix, max_items_per_file=10):
    """
    Divide um arquivo JSON em vários arquivos menores, cada um contendo no máximo `max_items_per_file` registros.
    Args:
        input_data (list): Lista de registros JSON a serem divididos.
        output_folder (str): Pasta onde os arquivos divididos serão salvos.
        file_prefix (str): Prefixo para os arquivos de saída.
        max_items_per_file (int): Número máximo de registros por arquivo.
    """
    if not isinstance(input_data, list):
        raise ValueError("The input data does not contain a JSON list.")

    chunks = [input_data[i:i + max_items_per_file] for i in range(0, len(input_data), max_items_per_file)]

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    for idx, chunk in enumerate(chunks):
        output_file = os.path.join(output_folder, f"{file_prefix}_{idx + 1}.json")
        with open(output_file, 'w') as f:
            json.dump(chunk, f, indent=4)
        print(f"File {output_file} created with {len(chunk)} items.")
              
def merge_files(folder_path):
    """
    Mescla todos os arquivos JSON em uma pasta especificada em um único arquivo JSON.
    Args:
        folder_path (str): Caminho para a pasta contendo os arquivos JSON.
    Returns:
        list: Lista combinada de registros JSON de todos os arquivos.
    """
    json_files = glob.glob(folder_path + "/**/*.json", recursive=True)
    combined_data = []
    for file in json_files:
        with open(file, 'r') as f:
            data = json.load(f)
            print(f'Processing {file} with {len(data)} items')
            combined_data.extend(data)
    print(f'Dados combinados contêm {len(combined_data)} items')
    return combined_data

def group_file_by_fix(data):
    """
    Agrupa os registros de um arquivo JSON pelo hash do commit de correção (fix_commit_hash).
    Evita duplicatas de 'bic' para cada commit de correção.
    
    :param input_file: Caminho para o arquivo JSON de entrada.
    :return: Dados agrupados.
    """
    grouped_data = {}

    for record in data:
        fix_hash = record["fix_commit_hash"]
        
        if fix_hash not in grouped_data:
            grouped_data[fix_hash] = record
            grouped_data[fix_hash]["bic"] = set(record["bic"])
        else:
            grouped_data[fix_hash]["bic"].update(record["bic"])

    result = [
        {**values, "bic": list(values["bic"])}
        for values in grouped_data.values()
    ]

    return result 

def is_commit_valid(repo_path, commit_hash):
    """
    Verifica se o commit existe no repositório e não é um commit de merge.

    Args:
        repo_path (str): Caminho para o repositório local.
        commit_hash (str): Hash do commit a ser verificado.

    Returns:
        bool: True se o commit existe e não é um merge, False caso contrário.
    """
    gr = Git(repo_path)
    try:
        commit = gr.get_commit(commit_hash)
        if commit.merge:
            return False, "Commit é um merge"
    except Exception as e:
        return False, "Commit não encontrado"

    return True, "Commit válido"

def extract_metrics_from_commit(commit, author_commits_map, pranalyzer_fn=None):
    """"
    Extrai métricas de um commit específico, incluindo informações sobre alterações em arquivos de teste e asserts.
    Args:
        commit (pydriller.Commit): Objeto de commit do PyDriller.
        author_commits_map (dict): Mapeamento de autores para suas datas de commits.
        pranalyzer_fn (callable, optional): Função para analisar diffs e detectar alterações em asserts. 
            Deve aceitar dois argumentos: linguagem e diff, e retornar uma tupla (has_asserts_changes, added_asserts, removed_asserts).
    Returns:
        dict: Dicionário contendo métricas extraídas do commit.
    """
    has_test_files = False
    java_lines_changed = 0
    java_files = 0
    files_with_asserts_changes = 0
    test_files_with_asserts_changes = 0
    added_asserts = 0
    removed_asserts = 0


    for mf in commit.modified_files:
        if mf.filename.endswith(".java"):
            java_lines_changed += mf.added_lines + mf.deleted_lines
            java_files += 1

            is_test_file = (
                "test" in mf.filename.lower()
                or (mf.new_path and "test" in mf.new_path.lower())
                or (mf.old_path and "test" in mf.old_path.lower())
            )

            if is_test_file:
                has_test_files = True

            has_asserts_changes, file_added_asserts, file_removed_asserts = pranalyzer_fn('JAVA', mf.diff)
            if has_asserts_changes:
                files_with_asserts_changes += 1
                if is_test_file:
                    test_files_with_asserts_changes += 1
                    added_asserts += file_added_asserts
                    removed_asserts += file_removed_asserts
                    
    # Calcula contributor_activity para o autor até a data do commit - 1 dia
    author = commit.author.name
    commit_date = commit.author_date
    contributor_activity = get_contributor_activity_from_index(author, commit_date - timedelta(days=1), author_commits_map)

    if test_files_with_asserts_changes <= 0:
        asserts_changes_type = "None"
    else:
        asserts_changes_type = (
            "Added" if added_asserts > removed_asserts
            else "Removed" if removed_asserts > added_asserts
            else "Maintained"
        )
    
    data = {
        "commit_author": author,
        "committer": commit.committer.name,
        "commit_date": commit_date.isoformat(),
        "committer_date": commit.committer_date.isoformat(),
        "changed_files": commit.files,
        "deletions": commit.deletions,
        "insertions": commit.insertions,
        "lines": commit.lines,
        "java_lines_changed": java_lines_changed,
        "java_files": java_files,
        "dmm_unit_size": commit.dmm_unit_size,
        "dmm_unit_complexity": commit.dmm_unit_complexity,
        "dmm_unit_interfacing": commit.dmm_unit_interfacing,
        "contributor_activity": contributor_activity,
        "has_test_files": has_test_files,
        "has_asserts_changes": files_with_asserts_changes > 0,
        "files_with_asserts_changes": files_with_asserts_changes,
        "test_files_with_asserts_changes": test_files_with_asserts_changes,
        "added_asserts": added_asserts,
        "removed_asserts": removed_asserts,
        "asserts_changes_type": asserts_changes_type
    }
    return data


def preload_commits_index(repo_path):
    """
    Precarrega um índice de commits para um repositório específico, mapeando cada commit para sua data e agrupando commits por autor.
    Args:
        repo_path (str): Caminho para o repositório local.
    Returns:
        tuple: Um dicionário mapeando hashes de commits para suas datas e um dicionário mapeando autores para listas de datas de commits.
    """
    commit_date = {}
    author_commits = defaultdict(list)

    try:
        for commit in Repository(repo_path).traverse_commits():
            commit_date[commit.hash] = commit.author_date
            author_commits[commit.author.name].append(commit.author_date)
    except Exception:
        # fallback: return empty maps if repo not available or pydriller missing
        return {}, defaultdict(list)

    for author in author_commits:
        author_commits[author].sort()

    return commit_date, author_commits


def get_commit_date_from_index(fix_commit, commit_date_map):
    """
    Retorna a data de um commit específico a partir do índice de commits.
    Args:
        fix_commit (str): Hash do commit a ser consultado.
        commit_date_map (dict): Dicionário mapeando hashes de commits para suas datas.
    Returns:
            datetime: A data do commit ou None se não encontrado.
    """
    d = commit_date_map.get(fix_commit)
    if not d:
        return None
    return d - timedelta(days=1)


def get_contributor_activity_from_index(author, fix_date, author_commits_map):
    """
    Retorna a atividade do contribuinte (número de commits) até a data do commit de correção.
    Args:
        author (str): Nome do autor do commit.
        fix_date (datetime): Data do commit de correção.
        author_commits_map (dict): Dicionário mapeando autores para listas de datas de commits.
    Returns:
        int: Número de commits do autor até a data do commit de correção.
    """
    if fix_date is None:
        return 0
    dates = author_commits_map.get(author, [])
    return bisect_right(dates, fix_date)

def safe_float(value):
    """
    Converte um valor para float de forma segura, retornando None se a conversão falhar.
    Args:
        value: Valor a ser convertido.
    Returns:
        float or None: Valor convertido para float ou None se a conversão falhar.
    """
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None
    
def load_data(path):
    """
    Carrega dados de um arquivo JSON.
    Args:
        path (str): Caminho para o arquivo JSON.
    Returns:
        dict: Dados carregados do arquivo JSON.
    Raises:
        FileNotFoundError: Se o arquivo não for encontrado.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)
    
class Reporter:
    """
    Classe para registrar mensagens em um arquivo de log específico.
    Args:
        path (str): Caminho para o arquivo de log.
    """
    def __init__(self, path):
        self.path = path

    def write(self, text):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(text + "\n")

def get_activity_bucket(activity):
    """
    Retorna o bucket de atividade com base no número de commits.
    Args:
        activity (int): Número de commits.
    Returns:
        str: O bucket de atividade.
    """
    if activity is None: return None
    if activity == 0:    return "0"
    if activity <= 5:    return "1-5"
    if activity <= 20:   return "6-20"
    if activity <= 100:  return "21-100"
    return "100+"