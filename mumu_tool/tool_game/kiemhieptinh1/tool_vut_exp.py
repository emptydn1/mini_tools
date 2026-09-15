import keyboard
import keyboard
import threading
import time

from mumu_tool.config import merge_devices
from mumu_tool.adb_core import check_shells_created, tap_points, tap, input_text, input_text_list


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


def tool_vut_exp():
    check_shells_created()

    def phim_tat_exp():
        def _tick_do(port):
            tap(port, 890, 263)
            time.sleep(0.5)
            tap(port, 560, 140)
            time.sleep(0.5)
            tap(port, 695, 390)
            time.sleep(0.5)
            tap(port, 680, 236)
            time.sleep(0.5)
            tap(port, 864, 95)
            time.sleep(0.3)
            tap(port, 864, 95)
            time.sleep(0.3)
            tap(port, 864, 95)

        threads = []
        for port in merge_devices.values():
            t = threading.Thread(target=_tick_do, args=(port,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def pos_vut_do():
        def _move_to_coordinate(port, x, y):
            tap(port, 855, 60)  # click bản đồ
            time.sleep(1)
            tap(port, 335, 455)  # click điểm đến
            time.sleep(1)
            tap(port, 380, 260)  # nhập x
            time.sleep(1)
            input_text(port, x)
            time.sleep(1)
            tap(port, 555, 260)  # nhập y
            time.sleep(1)
            input_text(port, y)
            time.sleep(1)
            tap(port, 560, 335)  # đồng ý
            time.sleep(1)
            tap(port, 925, 200)  # click ra ngoài, gần túi, tắt bản đồ

        threads = []
        for port in merge_devices.values():
            t = threading.Thread(target=_move_to_coordinate, args=(port, 63, 48))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def logOut():
        pointsLogOut = [(946, 257), (946, 337), (153, 115), (800, 250)]
        tap_points(pointsLogOut, 0.5, merge_devices)

    tai_khoan = QuanLyTaiKhoan()
    hotkeys = {
        "a": phim_tat_exp,
        "x": pos_vut_do,
        ".": tai_khoan.nhap_du_lieu_gia_tri_tang_giam,
        "`": tai_khoan.nhap_du_lieu,
        "=": tai_khoan.tang_so_dau,
        "-": tai_khoan.giam_so_dau,
        "m": logOut,
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== vứt exp =====")
    print("a: đặt phím tắt exp")
    print("x: đi đến điểm chỉ định")

    print(".: nhập giá trị tăng giảm")
    print("`: nhập dữ liệu")
    print("+: tăng số đầu")
    print("-: giảm số đầu")

    print("m: log out")
    print("q: Thoát")

    keyboard.wait("q")

    # Xóa toàn bộ hotkey
    for key in hotkeys:
        keyboard.remove_hotkey(key)
