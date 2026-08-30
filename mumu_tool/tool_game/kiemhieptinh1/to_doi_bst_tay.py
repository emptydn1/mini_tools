import keyboard
import threading
import time
import win32gui
import win32con

from mumu_tool.config import merge_devices
from mumu_tool.adb_core import check_shells_created, tap_points, input_text, tap
from mumu_tool.window_map import windows


def loop_to_doi_bst():
    check_shells_created()
    running_addTeam = threading.Event()
    addTeam_thread = None
    count = 0

    def addTeam():
        nonlocal count
        pointsTeam = [(190, 157), (190, 157), (500, 440), (694, 116), (900, 225)]
        tap_points(pointsTeam, 0.3, merge_devices)
        if count >= 10:
            pointsTeam = [(900, 225), (900, 225), (900, 225)]
            tap_points(pointsTeam, 0.3, merge_devices)
            count = 0
        else:
            count += 1

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


def to_doi_bst_tay():
    check_shells_created()

    def to_doi():
        hwnd = win32gui.GetForegroundWindow()
        port = windows.get(hwnd)

        if port:
            tap(port, 190, 157)
            time.sleep(0.2)
            tap(port, 140, 250)

    def cancel_tab_task():
        hwnd = win32gui.GetForegroundWindow()
        port = windows.get(hwnd)

        if port:
            tap(port, 855, 60)

    def tang_diem_sinh_khi():
        points = [(60, 60), (455, 440), (680, 223)]
        tap_points(points, 0.4)

        def _input_diem_sinh_khi(port):
            input_text(port, "9999")
            time.sleep(0.4)
            tap(port, 710, 420)
            time.sleep(0.4)
            tap(port, 870, 95)

        threads = []
        for port in merge_devices.values():
            t = threading.Thread(target=_input_diem_sinh_khi, args=(port,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def logout_and_login(port):
        tap(port, 925, 200)
        time.sleep(0.5)
        tap(port, 925, 200)
        time.sleep(0.5)
        tap(port, 946, 257)
        time.sleep(0.5)
        tap(port, 946, 337)
        time.sleep(0.5)
        tap(port, 153, 115)
        time.sleep(0.5)
        tap(port, 800, 250)
        time.sleep(0.5)

        tap(port, 490, 395)
        time.sleep(0.8)
        tap(port, 585, 360)

    def logout_and_login_1_tab():
        hwnd = win32gui.GetForegroundWindow()
        port = windows.get(hwnd)

        if port:
            threading.Thread(target=logout_and_login, args=(port,), daemon=True).start()

    def nhan_nv_worker(port):
        tap(port, 190, 157)  # to doi
        time.sleep(0.4)
        tap(port, 190, 157)  # to doi
        time.sleep(0.4)

        tap(port, 184, 111)  # huy? hien thong tin chu pt
        time.sleep(0.4)
        tap(port, 400, 440)  # roi doi
        time.sleep(0.4)
        tap(port, 820, 270)  # nc npc
        time.sleep(0.4)
        tap(port, 180, 295)  # click tham gia nv
        time.sleep(0.4)

        for _ in range(6):
            tap(port, 730, 460)
            time.sleep(0.3)

    def nhan_va_tra_nhiem_vu():
        hwnd = win32gui.GetForegroundWindow()
        port = windows.get(hwnd)

        if port:
            threading.Thread(target=nhan_nv_worker, args=(port,), daemon=True).start()

    def switch_tab_nv():
        hwnd = win32gui.GetForegroundWindow()
        port = windows.get(hwnd)

        if port:
            tap(port, 60, 155)

    def switch_tab_to_doi():
        hwnd = win32gui.GetForegroundWindow()
        port = windows.get(hwnd)

        if port:
            tap(port, 190, 157)

    def thu_nho_tab():
        hwnd = win32gui.GetForegroundWindow()
        port = windows.get(hwnd)

        if port:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    def logOut():
        pointsLogOut = [(946, 257), (946, 337), (153, 115), (800, 250)]
        tap_points(pointsLogOut, 0.5, merge_devices)

    hotkeys = {
        "w": to_doi,
        "e": cancel_tab_task,
        "a": nhan_va_tra_nhiem_vu,
        "s": switch_tab_nv,
        "d": switch_tab_to_doi,
        "v": thu_nho_tab,
        "n": tang_diem_sinh_khi,
        "m": logout_and_login_1_tab,
        ",": logOut,
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== BST =====")
    print("w: tổ đội")
    print("e: Hủy tab nhiệm vụ")

    print("a: Nhận và trả nhiệm vụ")
    print("s: Chuyển qua mục nhiệm vụ")
    print("d: Chuyển qua mục tổ đội")

    print("v: Thu nhỏ tab")
    print("n: tăng điểm sinh khí ALL")
    print("m: thoát với acc chỉ định")
    print(",: thoát hết")
    print("q: Thoát")

    keyboard.wait("q")

    # Xóa toàn bộ hotkey
    for key in hotkeys:
        keyboard.remove_hotkey(key)
