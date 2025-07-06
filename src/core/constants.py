# src/core/constants.py
#
# DESCRIÇÃO:
# Armazena constantes globais usadas em todo o projeto para evitar
# repetição e facilitar futuras alterações.

from pathlib import Path

# --- Constantes Globais ---
CONFIG_FILE_NAME = Path("downloader_config.json")
LOG_FILE = Path("downloader.log")
APP_VERSION = "v8.0-Arch" # Versão que reflete a nova arquitetura
