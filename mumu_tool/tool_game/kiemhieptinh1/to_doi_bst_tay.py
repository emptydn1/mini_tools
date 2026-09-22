import keyboard
import threading
import time
import win32gui
import win32con

from mumu_tool.config import merge_devices
from mumu_tool.adb_core import check_shells_created, tap_points, input_text, tap, input_text_list
from mumu_tool.window_map import windows
from mumu_tool.tool_game.utils import QuanLyTaiKhoan


def loop_to_doi_bst():
    check_shells_created()

    running_addTeam = threading.Event()
    addTeam_thread = None
    count = 0

    # Set chứa các port đang bị tạm dừng (bấm 'l' để thêm, 'k' để bỏ ra)
    paused_ports = set()
    paused_lock = threading.Lock()

    # ---- Helper: lấy port của emulator đang focus ----
    def get_focused_port():
        hwnd = win32gui.GetForegroundWindow()
        port = windows.get(hwnd)
        return port

    def addTeam():
        nonlocal count
        pointsTeam = [(190, 157), (190, 157), (500, 440), (694, 116), (900, 225)]

        with paused_lock:
            current_paused = set(paused_ports)

        # merge_devices dạng {"clone-13": 16832, ...} → key = tên clone, value = port
        if current_paused:
            active_devices = {name: port for name, port in merge_devices.items() if port not in current_paused}
        else:
            active_devices = merge_devices

        if not active_devices:
            return

        tap_points(pointsTeam, 0.3, active_devices)

    # ---- Vòng lặp chạy liên tục addTeam ----
    def addTeam_loop():
        print("▶ addTeam bắt đầu chạy...")
        while running_addTeam.is_set():
            try:
                addTeam()
            except Exception as e:
                print(f"⚠ Lỗi trong addTeam: {e}")
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

    # ---- 'l': tạm dừng emulator đang focus ----
    def pause_focused_port():
        port = get_focused_port()
        if port is None:
            print("⚠ Không xác định được port của cửa sổ đang focus.")
            return
        with paused_lock:
            paused_ports.add(port)
        print(f"⏸ Đã tạm dừng port {port}")

    # ---- 'k': chạy lại emulator đang focus ----
    def resume_focused_port():
        port = get_focused_port()
        if port is None:
            print("⚠ Không xác định được port của cửa sổ đang focus.")
            return
        with paused_lock:
            paused_ports.discard(port)
        print(f"▶ Đã tiếp tục port {port}")

    def thu_nho_tab():
        hwnd = win32gui.GetForegroundWindow()
        port = windows.get(hwnd)

        if port:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    hotkeys = {
        "i": start_addTeam,
        "o": stop_addTeam,
        "a": pause_focused_port,
        "s": resume_focused_port,
        "v": thu_nho_tab,
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== BST =====")
    print("i: bắt đầu loop tổ đội (tất cả các port)")
    print("o: hủy loop tổ đội")
    print("a: tạm dừng port đang focus")
    print("s: chạy lại port đang focus")
    print("v: thu nhỏ")
    print("q: Thoát")

    try:
        keyboard.wait("q")
    finally:
        stop_addTeam()
        for key in hotkeys:
            keyboard.remove_hotkey(key)


# def loop_to_doi_bst():
#     check_shells_created()
#     running_addTeam = threading.Event()
#     addTeam_thread = None
#     count = 0

#     def addTeam():
#         nonlocal count
#         pointsTeam = [(190, 157), (190, 157), (500, 440), (694, 116), (900, 225)]
#         tap_points(pointsTeam, 0.3, merge_devices)

#     # ---- Vòng lặp chạy liên tục addTeam ----
#     def addTeam_loop():
#         print("▶ addTeam bắt đầu chạy...")
#         while running_addTeam.is_set():
#             try:
#                 addTeam()
#             except Exception as e:
#                 print(f"⚠ Lỗi trong addTeam: {e}")
#             # wait() vừa làm delay vừa cho phép dừng ngay lập tức
#             running_addTeam.wait(0.2)
#         print("⏹ addTeam đã dừng.")

#     def start_addTeam():
#         nonlocal addTeam_thread
#         if not running_addTeam.is_set():
#             running_addTeam.set()
#             addTeam_thread = threading.Thread(target=addTeam_loop, daemon=True)
#             addTeam_thread.start()

#     def stop_addTeam():
#         nonlocal addTeam_thread
#         if running_addTeam.is_set():
#             running_addTeam.clear()
#             if addTeam_thread is not None:
#                 addTeam_thread.join(timeout=1)
#                 addTeam_thread = None

#     hotkeys = {
#         "i": start_addTeam,
#         "o": stop_addTeam,
#     }

#     for key, func in hotkeys.items():
#         keyboard.add_hotkey(key, func)

#     print("\n===== BST =====")
#     print("i: bắt đầu loop tổ đội")
#     print("o: hủy loop tổ đội")
#     print("q: Thoát")

#     try:
#         keyboard.wait("q")
#     finally:
#         # Dừng loop nếu đang chạy trước khi thoát
#         stop_addTeam()
#         # Xóa toàn bộ hotkey
#         for key in hotkeys:
#             keyboard.remove_hotkey(key)


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

    def phu_phuong_tuong_trung_tam():
        pointsPhuongTuongTrungTam = [(801, 300), (300, 335), (300, 335), (300, 290), (300, 290)]
        tap_points(pointsPhuongTuongTrungTam)

    def ban_set_kim_phong():
        def _tick_do(port):
            # tap(port, 855, 60)  # click bản đồ
            # time.sleep(0.5)
            # tap(port, 190, 340)  # click được điểm
            # time.sleep(0.5)
            # tap(port, 855, 60)  #  hủy mở bản đồ
            # time.sleep(3)
            tap(port, 320, 295)  # nhấn nút giao dịch
            time.sleep(0.5)

            tap(port, 775, 480)  # bấm nút bán nhanh
            time.sleep(0.5)
            tap(port, 215, 160)  # tick 6 ô đầu
            tap(port, 275, 160)
            tap(port, 335, 160)
            tap(port, 395, 160)
            tap(port, 455, 160)
            tap(port, 515, 160)
            tap(port, 575, 160)

            tap(port, 215, 255)  # tick 6 ô thứ 2
            tap(port, 275, 255)
            tap(port, 335, 255)
            tap(port, 395, 255)
            tap(port, 455, 255)
            tap(port, 515, 255)
            tap(port, 575, 255)

        threads = []
        for port in merge_devices.values():
            t = threading.Thread(target=_tick_do, args=(port,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def phu_den_boss_sat_thu():
        def _phu(port):
            tap(port, 595, 30)  # click cẩm nang
            time.sleep(0.5)
            tap(port, 250, 275)  # click bst
            time.sleep(0.5)
            tap(port, 860, 470)  # click tham gia

        threads = []
        for port in merge_devices.values():
            t = threading.Thread(target=_phu, args=(port,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    tai_khoan = QuanLyTaiKhoan()

    hotkeys = {
        "w": to_doi,
        "e": cancel_tab_task,
        "a": nhan_va_tra_nhiem_vu,
        "s": switch_tab_nv,
        "d": switch_tab_to_doi,
        ##
        "j": phu_phuong_tuong_trung_tam,
        "k": phu_den_boss_sat_thu,
        "l": ban_set_kim_phong,
        ##
        ".": tai_khoan.nhap_du_lieu_gia_tri_tang_giam,
        "`": tai_khoan.nhap_du_lieu,
        "=": tai_khoan.tang_so_dau,
        "-": tai_khoan.giam_so_dau,
        ##
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

    print("j: phù về phượng tường")
    print("k: cẩm nang -> Boss Sat Thu")
    print("l: bán đồ kim phong")

    print(".: nhập giá trị tăng giảm")
    print("`: nhập dữ liệu")
    print("+: tăng số đầu")
    print("-: giảm số đầu")

    print("v: Thu nhỏ tab")
    print("n: tăng điểm sinh khí ALL")
    print("m: thoát với acc chỉ định")
    print(",: thoát hết")
    print("q: Thoát")

    keyboard.wait("q")

    # Xóa toàn bộ hotkey
    for key in hotkeys:
        keyboard.remove_hotkey(key)
