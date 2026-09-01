import keyboard
import threading
import time
import win32gui
import win32con

from mumu_tool.config import merge_devices
from mumu_tool.adb_core import check_shells_created, tap_points, input_text, tap, input_text_list
from mumu_tool.window_map import windows


class QuanLyTaiKhoan:
    def __init__(self):
        self.da_nhap = False
        self.so_dau = 0
        self.ten = ""
        self.so_bat_dau = 0
        self.so_ket_thuc = 0
        self.gia_tri_tang_giam = 3

    def nhap_du_lieu(self):
        value = input("Nhập dữ liệu (ví dụ 1-huy-1+16): ").strip()

        arr = value.split("-")

        if len(arr) != 3:
            print("Sai định dạng!")
            return False

        try:
            self.so_dau = int(arr[0])
            self.ten = arr[1]
            self.so_bat_dau, self.so_ket_thuc = map(int, arr[2].split("+"))

        except ValueError:
            print("Sai định dạng!")
            return False

        self.da_nhap = True
        return True

    def nhap_du_lieu_gia_tri_tang_giam(self):
        value = input("Nhập giá trị tăng giảm: ").strip()

        if value.isdigit():
            self.gia_tri_tang_giam = int(value)
        else:
            print("Sai định dạng, vui lòng nhập số")

    def arr_tai_khoan(self):
        return [f"{self.so_dau}{self.ten}{so_thu_tu}" for so_thu_tu in range(self.so_bat_dau, self.so_ket_thuc + 1)]

    def tang_so_dau(self):
        if not self.da_nhap:
            print("Bạn cần nhập dữ liệu trước")
            return

        self.so_dau += self.gia_tri_tang_giam
        input_text_list(self.arr_tai_khoan())

    def giam_so_dau(self):
        if not self.da_nhap:
            print("Bạn cần nhập dữ liệu trước")
            return

        self.so_dau -= self.gia_tri_tang_giam
        input_text_list(self.arr_tai_khoan())


def loop_to_doi_bst():
    check_shells_created()
    running_addTeam = threading.Event()
    addTeam_thread = None
    count = 0

    def addTeam():
        nonlocal count
        pointsTeam = [(190, 157), (190, 157), (500, 440), (694, 116), (900, 225)]
        tap_points(pointsTeam, 0.3, merge_devices)
        if count >= 8:
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
