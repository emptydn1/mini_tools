import keyboard
import time
import threading
import win32gui
import win32con
import pyautogui

from mumu_tool.config import merge_devices
from mumu_tool.window_map import windows
from mumu_tool.adb_core import check_shells_created, tap


def vut_do_da_tau():
    check_shells_created()

    def tap_drop():
        hwnd = win32gui.GetForegroundWindow()
        port = windows.get(hwnd)

        if port:
            pyautogui.click()
            time.sleep(0.08)
            tap(port, 651, 478)

    def thu_nho_tab():
        hwnd = win32gui.GetForegroundWindow()
        port = windows.get(hwnd)

        if port:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    def tap_all():
        for port in merge_devices.values():
            threading.Thread(target=tap, args=(port, 305, 290), daemon=True).start()

    hotkeys = {
        "z": tap_drop,
        "x": tap_all,
        "v": thu_nho_tab,
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== làm dã tẩu =====")
    print("z: vứt đồ dã tẩu")
    print("x: mở rương")
    print("v: thu nhỏ")
    print("q: Thoát")

    keyboard.wait("q")

    # Xóa toàn bộ hotkey
    for key in hotkeys:
        keyboard.remove_hotkey(key)


def lam_da_tau():
    def focused():
        hwnd = win32gui.GetForegroundWindow()
        port = windows.get(hwnd)

        if port:
            tap(port, 651, 478)

    def cancel_task():
        hwnd = win32gui.GetForegroundWindow()
        port = windows.get(hwnd)

        if port:
            tap(port, 780, 120)
            time.sleep(0.2)
            tap(port, 310, 295)
            time.sleep(0.1)
            tap(port, 579, 365)
            time.sleep(0.2)
            tap(port, 755, 343)

    def finish_task():
        hwnd = win32gui.GetForegroundWindow()
        port = windows.get(hwnd)

        if port:
            tap(port, 200, 185)
            time.sleep(0.2)
            tap(port, 235, 180)
            time.sleep(0.1)
            tap(port, 712, 420)

    hotkeys = {
        "z": focused,
        "x": cancel_task,
        "c": finish_task,
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== làm dã tẩu =====")
    print("z: ")
    print("x: hủy nhiệm vụ")
    print("c: hoàn thành nhiệm vụ")
    print("q: Thoát")

    keyboard.wait("q")

    # Xóa toàn bộ hotkey
    for key in hotkeys:
        keyboard.remove_hotkey(key)
