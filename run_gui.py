# run_gui.py
#
# DESCRIÇÃO:
# Ponto de entrada principal para a aplicação Super Downloader.
# Executar este arquivo inicia a interface gráfica.

import logging
from src.gui.main_window import DownloaderApp
from src.core.constants import LOG_FILE

def setup_logging():
    """Configura o logging para a aplicação GUI."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8', mode='w'),
            logging.StreamHandler() # Mostra logs no console onde a GUI foi iniciada
        ]
    )

if __name__ == "__main__":
    setup_logging()
    app = DownloaderApp()
    app.mainloop()
