import keyboard
import threading
import time
import win32gui
import win32con
import subprocess
import pyperclip

from mumu_tool.config import merge_devices
from mumu_tool.adb_core import check_shells_created, shells, tap_points, input_text, tap, input_text_list, send_shell_command


def rao_ban():
    running_addTeam = threading.Event()
    addTeam_thread = None
    count = 0
    devices1 = {
        "clone-1": 16448,
    }

    for port in list(devices1.values()):
        subprocess.run(["adb", "connect", f"127.0.0.1:{port}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for name, port in merge_devices.items():
        shells[port] = subprocess.Popen(["adb", "-s", f"127.0.0.1:{port}", "shell"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True, bufsize=1)
    print(f"✅ Đã mở {len(shells)} shell.")

    def addTeam():
        nonlocal count
        pointsTeam = [(365, 473), (72, 509)]
        tap_points(pointsTeam, 0.3, devices1)

        pyperclip.copy("thu mua phúc duyên sll 1.5/1 ai bán pmmmmmmmmm")
        time.sleep(0.3)
        for port in devices1.values():
            send_shell_command(port, "input keyevent 279", "PASTE ERROR")

        time.sleep(0.4)
        pointsTeam2 = [(265, 382), (265, 382), (346, 511), (512, 261)]
        tap_points(pointsTeam2, 0.3, devices1)
        time.sleep(60)

    # ---- Vòng lặp chạy liên tục addTeam ----
    def addTeam_loop():
        print("▶ addTeam bắt đầu chạy...")
        while running_addTeam.is_set():
            try:
                addTeam()
            except Exception as e:
                print(f"⚠ Lỗi trong addTeam: {e}")
            # wait() vừa làm delay vừa cho phép dừng ngay lập tức
            running_addTeam.wait(0.2)
        print("⏹ addTeam đã dừng.")

    def start_addTeam():
        nonlocal addTeam_thread
        if not running_addTeam.is_set():
            running_addTeam.set()
            addTeam_thread = threading.Thread(target=addTeam_loop, daemon=True)
            addTeam_thread.start()

    def stop_addTeam():
        nonlocal addTeam_thread
        if running_addTeam.is_set():
            running_addTeam.clear()
            if addTeam_thread is not None:
                addTeam_thread.join(timeout=1)
                addTeam_thread = None

    hotkeys = {
        "i": start_addTeam,
        "o": stop_addTeam,
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== BST =====")
    print("i: bắt đầu loop tổ đội")
    print("o: hủy loop tổ đội")
    print("q: Thoát")

    try:
        keyboard.wait("q")
    finally:
        # Dừng loop nếu đang chạy trước khi thoát
        stop_addTeam()
        # Xóa toàn bộ hotkey
        for key in hotkeys:
            keyboard.remove_hotkey(key)
