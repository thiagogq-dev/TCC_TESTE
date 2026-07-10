from .PRAnalizer import PRAnalizer

allowed_extensions = {
    'java': 'JAVA'
}

def check_test_changes(tests):
    """
    Verifica se houve alterações em arquivos de teste com base nos dados fornecidos.
    Args:
        tests (dict): Dicionário contendo contadores de alterações em arquivos de teste.
    Returns:
        bool: True se houver alterações em arquivos de teste, False caso contrário.
    """
    test_changes = tests['removed'] + tests['added'] + tests['others']
    return test_changes > 0

def analyze_diff(language, patch):
    """
    Analisa o diff de um arquivo específico, verificando alterações em arquivos de teste e contando adições e remoções de asserts.
    Args:
        language (str): Linguagem de programação do arquivo.
        patch (str): Conteúdo do diff do arquivo.
    Returns:
        tuple: (has_test, added_asserts, removed_asserts)
            has_test (bool): True se houver alterações em arquivos de teste, False caso contrário.
            added_asserts (int): Número de asserts adicionados.
            removed_asserts (int): Número de asserts removidos.
    """
    analizer = PRAnalizer(language)
    dadosDoPR = analizer.retornaEstrutura()
    diff = patch.split("\n")

    for line in diff:
        stripped_line = line.strip() 
        if analizer.checkIfModifier(stripped_line):
            result = analizer.verify(stripped_line)
            modifier_type = analizer.checkModifierType(stripped_line)
            dadosDoPR[result][modifier_type] += 1
            dadosDoPR['all'][modifier_type] += 1

    has_test = check_test_changes(dadosDoPR['tests'])
    added_asserts = dadosDoPR['tests']['added']
    removed_asserts = dadosDoPR['tests']['removed']
    return has_test, added_asserts, removed_asserts


def analyze_files(files):
    """
    Analisa os arquivos fornecidos, verificando alterações em arquivos de teste e contando adições e remoções de asserts.
    Args:
        files (list): Lista de arquivos a serem analisados.
    Returns:
        tuple: (files_with_test, real_code_files, added_asserts, removed_asserts, test_files_with_test)
            files_with_test (int): Número de arquivos com alterações em testes.
            real_code_files (int): Número de arquivos de código real.
            added_asserts (int): Número total de asserts adicionados.
            removed_asserts (int): Número total de asserts removidos.
            test_files_with_test (int): Número de arquivos de teste com alterações.
    """
    files_with_test = 0
    real_code_files = 0
    added_asserts = 0
    removed_asserts = 0
    test_files_with_test = 0

    for file_item in files:
        file_test = False
        if file_item is None:
            continue

        filename = getattr(file_item, "filename", None)
        if not filename or "." not in filename:
            continue

        if "test" in filename.lower() or (getattr(file_item, "new_path", None) and "test" in getattr(file_item, "new_path").lower()) or (getattr(file_item, "old_path", None) and "test" in getattr(file_item, "old_path").lower()):
            file_test = True

        file_extension = filename.split(".")[-1]
        if file_extension not in allowed_extensions:
            continue

        patch = getattr(file_item, "diff", None)
        if patch is None:
            continue

        real_code_files += 1
        language = allowed_extensions[file_extension]
        has_test, file_added_asserts, file_removed_asserts = analyze_diff(language, patch)

        if has_test:
            files_with_test += 1
            if file_test:
                test_files_with_test += 1
                added_asserts += file_added_asserts
                removed_asserts += file_removed_asserts

    return files_with_test, real_code_files, added_asserts, removed_asserts, test_files_with_test
