# main.py

import tkinter as tk
from src.gui.main_window import MainWindow

def run_app():
    """
    Inicializa e executa a aplicação Super Downloader.
    """
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    run_app()
