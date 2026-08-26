"""
Entry point của MuMu Tool.
Chạy: python main.py
"""

import sys

sys.dont_write_bytecode = True

from mumu_tool.window_map import start_window_watcher
from menu import run_menu, main_menu

if __name__ == "__main__":
    start_window_watcher()  # refresh mapping cửa sổ -> device mỗi 2s
    run_menu("MuMu Tool", main_menu)
