"""
Các hành động thao tác trong game trên nhiều thiết bị cùng lúc.
"""

import time
import threading
import keyboard
import pyautogui
import os
import re
import time

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

from mumu_tool.config import merge_devices
from mumu_tool.adb_core import check_shells_created, tap, swipe, input_text, tap_points, tap_all_devices, input_text_list


class QuanLyTaiKhoan:
    def __init__(self):
        self.da_nhap = False
        self.so_dau = 0
        self.ten = ""
        self.so_bat_dau = 0
        self.so_ket_thuc = 0

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

    def arr_tai_khoan(self):
        return [f"{self.so_dau}{self.ten}{so_thu_tu}" for so_thu_tu in range(self.so_bat_dau, self.so_ket_thuc + 1)]

    def tang_so_dau(self):
        if not self.da_nhap:
            print("Bạn cần nhập dữ liệu trước")
            return

        self.so_dau += 1
        input_text_list(self.arr_tai_khoan())

    def giam_so_dau(self):
        if not self.da_nhap:
            print("Bạn cần nhập dữ liệu trước")
            return

        self.so_dau -= 1
        input_text_list(self.arr_tai_khoan())


def vi_tri_hoa_dang():

    def posHoaDang(name):
        check_shells_created()
        # Danh sách tọa độ % bản đồ cho từng "may" (bộ tài khoản)
        POS_PRESETS = {
            "huy": [[39, 68], [43, 56], [48, 71], [57, 72], [64, 81], [71, 85], [63, 67], [78, 65], [86, 60], [90, 80], [44, 40], [51, 25], [84, 18], [27, 82], [29, 71], [39, 80], [49, 84], [46, 78], [62, 54], [66, 33]],
            "hoang": [[67, 34], [52, 15], [32, 14], [75, 41], [58, 44], [46, 43], [56, 73], [62, 80], [68, 84], [72, 85], [36, 68], [47, 70], [76, 50], [84, 63], [81, 54], [48, 73], [68, 83], [57, 58], [71, 69], [71, 58]],
            "hao": [[68, 33], [51, 25], [47, 37], [31, 49], [41, 55], [53, 57], [63, 65], [71, 67], [37, 67], [47, 68], [66, 82], [71, 84], [47, 26], [32, 15], [85, 19], [36, 68]],
            "may4": [[55, 42], [70, 42], [68, 33], [50, 26], [39, 51], [46, 38], [33, 14], [54, 57], [40, 68], [66, 53], [75, 51], [77, 64], [77, 65], [64, 67], [65, 83], [67, 83], [70, 83], [71, 59], [52, 72], [58, 72]],
            "may5": [[59, 45], [77, 50], [62, 57], [82, 36], [76, 59], [64, 67], [72, 68], [86, 63], [45, 78], [38, 65], [34, 37], [86, 18], [57, 63], [60, 53], [77, 64], [39, 52], [34, 27], [21, 45], [84, 55], [70, 57]],
            "may6": [[65, 35], [90, 22], [63, 44], [79, 38], [42, 40], [32, 37], [40, 56], [64, 53], [70, 58], [80, 56], [78, 64], [67, 64], [56, 63], [48, 63], [40, 64], [42, 75], [56, 71], [39, 38], [47, 65], [85, 63]],
        }
        DEFAULT_POS = POS_PRESETS["huy"]

        pos = POS_PRESETS.get(name, DEFAULT_POS)

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

        for port, (x, y) in zip(merge_devices.values(), pos):
            t = threading.Thread(target=_move_to_coordinate, args=(port, x, y))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def turnOffAuto():
        check_shells_created()

        def _turn_off_auto(port):
            swipe(port, 690, 455, 690, 455, 2000)
            time.sleep(2)
            tap(port, 130, 430)  # click mục nhặt đồ
            time.sleep(2)
            # bên trái
            tap(port, 205, 225)
            tap(port, 205, 260)
            # bên phải
            tap(port, 415, 155)
            tap(port, 415, 190)
            tap(port, 415, 225)
            tap(port, 415, 260)

            time.sleep(2)
            tap(port, 130, 360)  # click mục mua đồ
            time.sleep(2)
            tap(port, 205, 240)
            tap(port, 205, 275)
            tap(port, 385, 350)
            tap(port, 385, 215)

            time.sleep(2)
            tap(port, 130, 255)  # click mục tấn công
            time.sleep(2)
            tap(port, 205, 335)
            tap(port, 205, 380)
            tap(port, 380, 335)
            tap(port, 380, 380)

            time.sleep(2)
            tap(port, 130, 290)  # click mục di chuyển
            time.sleep(2)
            tap(port, 205, 160)

        threads = []
        for port in merge_devices.values():
            t = threading.Thread(target=_turn_off_auto, args=(port,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def logOut():
        pointsLogOut = [(946, 257), (946, 337), (153, 115), (800, 250)]
        tap_points(pointsLogOut, 0.5, merge_devices)

    hotkeys = {
        "z": lambda: posHoaDang("huy"),
        "x": lambda: posHoaDang("hoang"),
        "c": lambda: posHoaDang("hao"),
        "v": lambda: posHoaDang("may4"),
        "b": lambda: posHoaDang("may5"),
        "n": lambda: posHoaDang("may6"),
        "g": lambda: turnOffAuto("tat_nhat_do"),
        "h": lambda: turnOffAuto("tat_mua_do"),
        "j": lambda: turnOffAuto("tat_tan_cong"),
        "k": turnOffAuto,
        "m": logOut,
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== vi tri hoa đăng =====")
    print("z: vị trí map của huy")
    print("x: vị trí map của hoang")
    print("c: vị trí map của hao")
    print("v: vị trí map của may4")
    print("b: vị trí map của may5")
    print("n: vị trí map của may6")
    print("g: tắt nhặt đồ")
    print("h: tắt mua đồ")
    print("j: tắt tự động đánh")
    print("k: tắt hết")

    print("m: Log out")
    print("q: Thoát")

    keyboard.wait("q")

    # Xóa toàn bộ hotkey
    for key in hotkeys:
        keyboard.remove_hotkey(key)


def vut_do_hoa_dang():
    check_shells_created()

    def _vut_do_hoa_dang():
        def _vut_do(port):
            tap(port, 560, 140)  # click đồ đầu tiên
            time.sleep(0.3)
            tap(port, 695, 485)  # vứt túi
            time.sleep(0.3)
            tap(port, 585, 385)  # đồng ý
            time.sleep(0.3)
            tap(port, 685, 430)  # vứt trang bị

        threads = []
        for port in merge_devices.values():
            t = threading.Thread(target=_vut_do, args=(port,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def cancel_popup_task():
        tap_all_devices(323, 100)

    def logOut():
        pointsLogOut = [(946, 257), (946, 337), (153, 115), (800, 250)]
        tap_points(pointsLogOut, 0.5, merge_devices)

    tai_khoan = QuanLyTaiKhoan()

    hotkeys = {
        "a": _vut_do_hoa_dang,
        "w": cancel_popup_task,
        "`": tai_khoan.nhap_du_lieu,
        "u": tai_khoan.tang_so_dau,
        "i": tai_khoan.giam_so_dau,
        "m": logOut,
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== hoa đăng =====")
    print("a: vứt đồ hoa đăng")
    print("w: tắt bảng nhiệm vụ")
    print("`: nhập dữ liệu")
    print("u: tăng số đầu")
    print("i: giảm số đầu")
    print("m: Log out")
    print("q: Thoát Cày Vạn")

    keyboard.wait("q")

    # Xóa toàn bộ hotkey
    for key in hotkeys:
        keyboard.remove_hotkey(key)


def screenshot_mode():
    print("\n========== CHẾ ĐỘ CHỤP HOA ĐĂNG ==========")
    print("dựa vào kết quả của hoa đăng và nhấn 1 2 3 4 5")
    print("Q. Thoát")
    print("==========================================")

    username = os.environ.get("USERNAME") or os.environ.get("USER")

    def add_number_to_file(image_path, number):
        output_path = rf"C:\Users\{username}\Desktop\mini_tools\file\{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{time.time_ns()}.png"
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("arial.ttf", 500)
        x = 1000
        y = 0
        draw.text((x, y), str(number), font=font, fill="red")
        img.save(output_path)

    def take_new_photo():
        folder = rf"C:\Users\{username}\Pictures\Screenshots"
        pattern = re.compile(r"Screenshot \((\d+)\)\.png")
        max_n = 0
        with os.scandir(folder) as entries:
            for entry in entries:
                if not entry.is_file():
                    continue

                match = pattern.match(entry.name)

                if match:
                    n = int(match.group(1))

                    if n > max_n:
                        max_n = n

        return os.path.join(folder, f"Screenshot ({max_n}).png")

    def screenshot(number):
        pyautogui.hotkey("win", "printscreen")
        print(f"Đã chụp {number}")
        time.sleep(2)
        add_number_to_file(take_new_photo(), number)

    while True:
        key = keyboard.read_key().lower()

        if key == "q":
            print("▶ Thoát chế độ chụp.")
            break

        for key in ["1", "2", "3", "4", "5"]:
            if keyboard.is_pressed(key):
                screenshot(key)
                print("→ Nhấn 1-5 để chụp tiếp, Q để thoát.")

        time.sleep(0.01)
