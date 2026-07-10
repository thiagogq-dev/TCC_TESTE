# logger_config.py
import os
import logging

# Garantir diretório de logs
if not os.path.exists("logs"):
    os.makedirs("logs")

# === Configuração Geral ===
def setup_loggers(repo_name="default"):
    """"
    Configura loggers para diferentes níveis de log (info, error, warning) e cria arquivos de log separados para cada nível.
    Args:
        repo_name (str): Nome do repositório, usado para nomear os arquivos de log.
    Returns:
        dict: Dicionário contendo os loggers configurados para info, error e warning.
    """
    # General Log
    general_log = logging.getLogger("general_log")
    general_log.setLevel(logging.INFO)
    general_log.handlers.clear() # Limpa handlers antigos
    general_handler = logging.FileHandler(f"logs/{repo_name}_info.log")
    general_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    general_log.addHandler(general_handler)

    # Error Log
    error_log = logging.getLogger("error_log")
    error_log.setLevel(logging.ERROR)
    error_log.handlers.clear() # Limpa handlers antigos
    error_handler = logging.FileHandler(f"logs/{repo_name}_error.log")
    error_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    error_log.addHandler(error_handler)

    # Warning Log
    warning_log = logging.getLogger("warning_log")
    warning_log.setLevel(logging.WARNING)
    warning_log.handlers.clear() # Limpa handlers antigos
    warning_handler = logging.FileHandler(f"logs/{repo_name}_warning.log")
    warning_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    warning_log.addHandler(warning_handler)

    return {
        "info": general_log,
        "error": error_log,
        "warning": warning_log
    }

def log_message(message, level):
    """"
    Registra uma mensagem em um logger específico com base no nível fornecido.
    Args:
        message (str): Mensagem a ser registrada.
        level (str): Nível de log ("info", "error", "warning").
    """
    loggers = {
        "info": logging.getLogger("general_log"),
        "error": logging.getLogger("error_log"),
        "warning": logging.getLogger("warning_log"),
    }

    logger = loggers.get(level)
    if logger:
        getattr(logger, level)(message)