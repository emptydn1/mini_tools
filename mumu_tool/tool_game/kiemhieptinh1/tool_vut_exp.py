import keyboard
import keyboard
import threading
import time

from mumu_tool.config import merge_devices
from mumu_tool.adb_core import check_shells_created, tap_points, tap, input_text


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

    hotkeys = {
        "a": phim_tat_exp,
        "s": pos_vut_do,
        "m": logOut,
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== vứt exp =====")
    print("a: đặt phím tắt exp")
    print("s: đi đến điểm chỉ định")
    print("m: log out")
    print("q: Thoát")

    keyboard.wait("q")

    # Xóa toàn bộ hotkey
    for key in hotkeys:
        keyboard.remove_hotkey(key)
