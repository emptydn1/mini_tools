"""
Map cửa sổ emulator (hwnd) -> port thiết bị, dựa vào tiêu đề cửa sổ.
Cập nhật mỗi 2 giây trong 1 thread nền.
"""

import threading
import time

import win32gui

from .config import devices

windows = {}  # hwnd -> port


def enum_windows():
    windows.clear()

    def callback(hwnd, _):
        title = win32gui.GetWindowText(hwnd).lower()
        for name, port in devices.items():
            if name in title:
                windows[hwnd] = port

    win32gui.EnumWindows(callback, None)


# refresh mapping mỗi 2s (tránh miss khi mở thêm emulator)
def refresh_windows():
    while True:
        enum_windows()
        time.sleep(2)


def start_window_watcher():
    threading.Thread(target=refresh_windows, daemon=True).start()
