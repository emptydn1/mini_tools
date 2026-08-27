import keyboard
import time
import os
import threading

from mumu_tool.config import merge_devices
from mumu_tool.adb_core import check_shells_created, input_text, tap, tap_points


def giao_dich_van_Hoang():
    check_shells_created()

    username = os.environ.get("USERNAME") or os.environ.get("USER")

    def action_port(port):
        tap(port, 797, 478)

    def action_cancel(port):
        tap(port, 852, 30)

    def agreeGd(port):
        num = open(rf"C:\Users\${username}\Desktop\giao_dich_van.txt", encoding="utf-8").read().strip()
        gdPoints = [(333, 388), (792, 116), (318, 479)]
        for x, y in gdPoints:
            tap(port, x, y)
            time.sleep(0.3)

        input_text(port, num)

        time.sleep(0.3)
        tap(port, 517, 300)

    def run_all(func):
        for port in merge_devices.values():
            threading.Thread(target=func, args=(port,), daemon=True).start()

    hotkeys = {
        "j": lambda: run_all(agreeGd),
        "k": lambda: run_all(action_port),
        "l": lambda: run_all(action_cancel),
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== giao dịch =====")
    print("j: đồng ý giao dịch")
    print("k: xác nhận")
    print("l: tắt form giao dịch")
    print("q: Thoát")

    keyboard.wait("q")

    # Xóa toàn bộ hotkey
    for key in hotkeys:
        keyboard.remove_hotkey(key)


# =========================
# Tool của Huy
# =========================


def giao_dich_van_Huy():
    check_shells_created()

    # default 5 khoảng cách
    STEP = 2

    # default 4 số port chạy cùng lúc
    PORTS_PER_RUN = 8

    # offset:
    # 0 -> 1 6 11 16
    # 1 -> 2 7 12 17
    # 2 -> 3 8 13 18
    offset = 0
    ports = list(merge_devices.values())

    def get_selected_ports():
        result = []
        current = offset
        for _ in range(PORTS_PER_RUN):
            if current >= len(ports):
                break
            result.append(ports[current])
            current += STEP
        return result

    def run_trans():
        selected = get_selected_ports()
        print("\nTRANS")
        print(selected)
        for port in selected:
            tap(port, 770, 275)

    def run_lock():
        selected = get_selected_ports()
        print("\nLOCK")
        print(selected)

        for port in selected:
            tap(port, 790, 475)

    def increase_offset():
        global offset
        max_offset = STEP - 1
        if offset < max_offset:
            offset += 1
        print(f"\nOFFSET = {offset}")

    def decrease_offset():
        global offset
        if offset > 0:
            offset -= 1
        print(f"\nOFFSET = {offset}")

    #################
    #################
    #################
    #################
    #################

    def phimtat_phu():
        points = [
            # (494, 332),  # click đại chưởng quầy
            # (250, 292),  # click nút hỗ trợ tân thủ
            # (250, 292),  # click nút hỗ trợ tân thủ
            # (250, 292),  # click nút hỗ trợ tân thủ
            # (250, 292),  # click nút hỗ trợ tân thủ
            # (890, 263),
            # (670, 143),
            # (698, 439),
            # (680, 236),
            # (924, 209),
            # (924, 209),
            # (869, 95),
            (801, 300),  # phù đến tây sơn thôn
            (157, 335),
            (175, 380),
            (175, 380),
        ]
        tap_points(points, 0.5)

    def tangDiemSinhKhi():
        points = [(60, 60), (455, 440), (680, 223)]

        tap_points(points, 0.4)

        def tang_diem_device(port):
            input_text(port, "9999")
            time.sleep(0.4)
            tap(port, 710, 420)
            time.sleep(0.4)
            tap(port, 870, 95)

        threads = []

        for port in merge_devices.values():
            t = threading.Thread(target=tang_diem_device, args=(port,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def sudung_banh():
        # points = [(890, 263), (721, 140), (696, 345), (869, 95)]
        points = [(890, 263), (721, 140), (698, 380), (740, 236), (869, 95), (869, 95), (869, 95)]
        tap_points(points, 0.3)

    def logOut():
        pointsLogOut = [(946, 257), (946, 337), (153, 115), (800, 250)]
        tap_points(pointsLogOut, 0.5)

    def tap_by_rows():
        points = [
            (291, 218),
            (357, 192),
            (412, 159),
            (476, 143),
            (660, 170),
            (350, 325),
            (418, 355),
            (658, 280),
            (627, 130),
            (728, 205),
        ]

        for row, (x, y) in enumerate(points):
            start = row * STEP
            end = min(start + STEP, len(ports))

            threads = []

            for port in ports[start:end]:
                t = threading.Thread(target=tap, args=(port, x, y))
                t.start()
                threads.append(t)

            for t in threads:
                t.join()

        time.sleep(1)

        threads = []

        for port in ports:
            t = threading.Thread(target=tap, args=(port, 825, 145))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    hotkeys = {
        "j": run_trans,
        "k": run_lock,
        "u": increase_offset,
        "i": decrease_offset,
        "n": tangDiemSinhKhi,
        "m": phimtat_phu,
        ",": sudung_banh,
        "t": tap_by_rows,
        "o": logOut,
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== giao dịch =====")
    print("j: gửi lời mời giao dịch")
    print("k: khóa giao dịch")
    print("u: tăng offset")
    print("i: giảm offset")
    print("n: tăng điểm sinh khí")
    print("m: set phím tắt phù")
    print(",: sử dụng bánh")
    print("t: hiển thị form thông tin nhân vật để giao dịch")
    print("o: thoát acc")
    print("q: Thoát")

    print(f"STEP = {STEP}")
    print(f"PORTS_PER_RUN = {PORTS_PER_RUN}")

    keyboard.wait("q")

    # Xóa toàn bộ hotkey
    for key in hotkeys:
        keyboard.remove_hotkey(key)
