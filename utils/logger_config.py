# logger_config.py
import os
import logging

# Garantir diretório de logs
if not os.path.exists("logs"):
    os.makedirs("logs")

# === Configuração Geral ===
def setup_loggers():
    # General Log
    general_log = logging.getLogger("general_log")
    general_log.setLevel(logging.INFO)
    general_handler = logging.FileHandler("logs/info.log")
    general_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    general_log.addHandler(general_handler)

    # Error Log
    error_log = logging.getLogger("error_log")
    error_log.setLevel(logging.ERROR)
    error_handler = logging.FileHandler("logs/error.log")
    error_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    error_log.addHandler(error_handler)

    # Warning Log
    warning_log = logging.getLogger("warning_log")
    warning_log.setLevel(logging.WARNING)
    warning_handler = logging.FileHandler("logs/warning.log")
    warning_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    warning_log.addHandler(warning_handler)

    return {
        "info": general_log,
        "error": error_log,
        "warning": warning_log
    }

# === Função para logar ===
def log_message(message, level):
    loggers = {
        "info": logging.getLogger("general_log"),
        "error": logging.getLogger("error_log"),
        "warning": logging.getLogger("warning_log"),
    }

    logger = loggers.get(level)
    if logger:
        getattr(logger, level)(message)
