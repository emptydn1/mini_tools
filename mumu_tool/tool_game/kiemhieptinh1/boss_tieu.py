import keyboard
import time
import os
import threading

from mumu_tool.config import merge_devices
from mumu_tool.adb_core import check_shells_created, tap_points, tap_all_devices, input_text, tap, swipe, input_text_list


def boss_tieu():
    check_shells_created()
    
    def run_menu(title, menu_dict):
        while True:
            print(f"\n========== {title} ==========")
            for key, (text, _) in menu_dict.items():
                print(f"{key}. {text}")
            print("Q. Thoát")
            print("============================")

            choice = input("Chọn: ").strip().lower()

            if choice in ("q"):
                break

            if choice not in menu_dict:
                print("❌ Lựa chọn không hợp lệ.")
                continue

            text, func = menu_dict[choice]
            print(f"▶ Đang chạy: {text}")

            try:
                func()
            except Exception as e:
                print(f"Lỗi: {e}")

            print("\n✅ Hoàn thành!")
            input("Nhấn Enter để tiếp tục...")

    posMonPhai = {
        "vo dang": {"boss1": 23.72, "boss2": 63.36, "boss3": 78.45},
        "con lon": {"boss1": 12.40, "boss2": 73.85, "boss3": 115.37},
        "thien nhan": {"boss1": 17.30, "boss2": 39.21, "boss3": 36.9},
        "cai bang": {"boss1": 68.9, "boss2": 44.3, "boss3": 72.28},
        "nga my": {"boss1": 15.61, "boss2": 130.70, "boss3": 162.81},
        "duong mon": {"boss1": 98.55, "boss2": 138.121, "boss3": 72.110},
        "ngu doc": {"boss1": 126.82, "boss2": 77.61, "boss3": 137.25},
        "thuy yen": {"boss1": 95.98, "boss2": 36.52, "boss3": 61.24},
        "thieu lam": {"boss1": 83.53, "boss2": 132.53, "boss3": 72.20},
    }

    def chon_boss(mon_phai, boss):
        gia_tri = posMonPhai[mon_phai][boss]
        result = str(gia_tri).split(".")

        print()
        print("================================")
        print(f"Môn phái : {mon_phai}")
        print(f"Boss     : {boss}")
        print(f"Giá trị  : {gia_tri}")
        print("================================")

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
            t = threading.Thread(target=_move_to_coordinate, args=(port, result[0], result[1]))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def menu_mon_phai():
        menu = {}

        for index, mon_phai in enumerate(posMonPhai.keys(), start=1):

            def tao_func(mon_phai=mon_phai):
                return menu_boss(mon_phai)

            menu[str(index)] = (mon_phai, tao_func)

        run_menu("BOSS TIỂU", menu)

    def menu_boss(mon_phai):
        menu = {}

        for index, boss in enumerate(posMonPhai[mon_phai].keys(), start=1):

            def tao_func(boss=boss):
                chon_boss(mon_phai, boss)

            gia_tri = posMonPhai[mon_phai][boss]

            menu[str(index)] = (f"{boss} - {gia_tri}", tao_func)

        run_menu(mon_phai.upper(), menu)

    menu_mon_phai()

    # def phu_phuong_tuong_trung_tam():
    #     pointsPhuongTuongTrungTam = [(801, 300), (300, 335), (300, 335), (300, 290), (300, 290)]
    #     tap_points(pointsPhuongTuongTrungTam)

    # def logOut():
    #     pointsLogOut = [(946, 257), (946, 337), (153, 115), (800, 250)]
    #     tap_points(pointsLogOut, 0.5, merge_devices)

    # hotkeys = {
    #     "r": phu_phuong_tuong_trung_tam,
    #     "m": logOut,
    # }

    # for key, func in hotkeys.items():
    #     keyboard.add_hotkey(key, func)

    # print("\n===== BOSS TIỂU =====")
    # print("m: Log out")
    # print("m: Log out")
    # print("q: Thoát")

    # keyboard.wait("q")

    # # Xóa toàn bộ hotkey
    # for key in hotkeys:
    #     keyboard.remove_hotkey(key)
