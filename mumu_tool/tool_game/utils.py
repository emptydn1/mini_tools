import time
import threading
import keyboard
import pyautogui
import sys
import subprocess
from pathlib import Path
import win32gui
import os
import re


from mumu_tool.adb_core import swipe_all_devices, check_shells_created, tap, tap_points, shells, input_text_list
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
        arr = chon_tu_danh_sach()

        if len(arr) != 3:
            print("❌ Sai định dạng! Phải có dạng: 1-huy-1+16")
            return False

        try:
            self.so_dau = int(arr[0])
            self.ten = arr[1]

            range_part = arr[2].split("+")

            if len(range_part) != 2:
                print("❌ Sai định dạng! Phải có dạng: 1-huy-1+16")
                return False

            self.so_bat_dau = int(range_part[0])
            self.so_ket_thuc = int(range_part[1])
        except ValueError:
            print("❌ Sai định dạng! Phải có dạng: 1-huy-1+16")
            return False

        if not self.ten:
            print("❌ Tên không được để trống.")
            return False

        if self.so_bat_dau > self.so_ket_thuc:
            print("❌ Số bắt đầu phải nhỏ hơn hoặc bằng số kết thúc.")
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


def chon_tu_danh_sach():
    username = os.environ.get("USERNAME") or os.environ.get("USER")
    file_path = rf"C:\Users\{username}\Desktop\tai_khoan.txt"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            danh_sach = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Không tìm thấy file tai_khoan.txt")
        return False

    if not danh_sach:
        print("❌ File tai_khoan.txt không có dữ liệu.")
        return False

    # Hiển thị danh sách
    print("\n========== CHỌN TÀI KHOẢN ==========")

    for i, item in enumerate(danh_sach, 1):
        print(f"{i}. {item}")

    print("Q. Thoát")
    print("=====================================")

    choice = input("Chọn: ").strip().lower()

    if choice == "q":
        return False

    if not choice.isdigit():
        print("❌ Lựa chọn không hợp lệ.")
        return False

    index = int(choice) - 1

    if index < 0 or index >= len(danh_sach):
        print("❌ Lựa chọn không hợp lệ.")
        return False

    # Lấy dữ liệu được chọn
    value = danh_sach[index]

    print(f"▶ Đã chọn: {value}")

    arr = value.split("-")
    return arr


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
            content = f.read()

        positions = []

        for line in content.splitlines():
            numbers = re.findall(r"\d+", line)

            if len(numbers) >= 2:
                x = int(numbers[0])
                y = int(numbers[-1])
                positions.append((x, y))

        for x, y in positions:
            subprocess.run(["adb", "-s", "127.0.0.1:16448", "shell", "input", "tap", str(x), str(y)])
            time.sleep(0.4)

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
