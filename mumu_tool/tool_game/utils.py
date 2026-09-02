import time
import threading
import keyboard
import pyautogui
import sys
import subprocess
from pathlib import Path
import win32gui
import os


from mumu_tool.adb_core import swipe_all_devices, check_shells_created, tap, tap_points, shells
from mumu_tool.window_map import windows


def auto_click():
    clicking = threading.Event()
    click_thread = None

    def _auto_click():
        print("Auto click ON")
        while clicking.is_set():
            pyautogui.click()
            clicking.wait(0.01)
        print("Auto click OFF")

    def start_click():
        nonlocal click_thread
        if not clicking.is_set():
            clicking.set()
            click_thread = threading.Thread(target=_auto_click, daemon=True)
            click_thread.start()

    def stop_click():
        nonlocal click_thread
        if clicking.is_set():
            clicking.clear()
            if click_thread is not None:
                click_thread.join(timeout=1)
                click_thread = None

    hotkeys = {
        "i": start_click,
        "o": stop_click,
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== auto click =====")
    print("i: bắt đầu click")
    print("o: dừng click")
    print("q: Thoát")

    try:
        keyboard.wait("q")
    finally:
        stop_click()
        for key in hotkeys:
            keyboard.remove_hotkey(key)


def auto_luom():
    check_shells_created()
    swiping = threading.Event()
    swipe_thread = None

    def _swipe_loop():
        print("Auto lượm ON")

        while swiping.is_set():
            # Kéo sang phải
            swipe_all_devices(155, 435, 220, 435, 50)
            time.sleep(0.15)

            if not swiping.is_set():
                break

            # Kéo sang trái
            swipe_all_devices(155, 435, 90, 435, 50)
            time.sleep(0.15)

        print("Auto lượm OFF")

    def start_swipe():
        nonlocal swipe_thread

        if not swiping.is_set():
            swiping.set()

            swipe_thread = threading.Thread(target=_swipe_loop, daemon=True)
            swipe_thread.start()

    def stop_swipe():
        nonlocal swipe_thread

        if swiping.is_set():
            swiping.clear()

            if swipe_thread is not None:
                swipe_thread.join(timeout=1)
                swipe_thread = None

    hotkeys = {
        "i": start_swipe,
        "o": stop_swipe,
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== AUTO LƯỢM =====")
    print("i: bắt đầu lượm")
    print("o: dừng lượm")
    print("q: Thoát")

    try:
        keyboard.wait("q")
    finally:
        stop_swipe()

        for key in hotkeys:
            keyboard.remove_hotkey(key)


def test_click():
    subprocess.run(["adb", "connect", f"127.0.0.1:16448"])

    username = os.environ.get("USERNAME") or os.environ.get("USER")

    def tap_drop():
        with open(rf"C:\Users\{username}\Desktop\click.txt", "r", encoding="utf-8") as f:
            x, y = map(int, f.read().split())
        subprocess.run(["adb", "-s", "127.0.0.1:16448", "shell", "input", "tap", str(x), str(y)])

    hotkeys = {
        "z": tap_drop,
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== test click =====")
    print("z: vứt đồ dã tẩu")
    print("q: Thoát")

    keyboard.wait("q")

    # Xóa toàn bộ hotkey
    for key in hotkeys:
        keyboard.remove_hotkey(key)
