import keyboard
import time
import threading

from mumu_tool.config import merge_devices
from mumu_tool.adb_core import check_shells_created, tap_points, tap_all_devices, input_text, tap, swipe


def cay_van():
    check_shells_created()

    def cancel_popup_task():
        tap_all_devices(323, 100)

    def cancel_tab_task():
        tap_all_devices(855, 60)

    def phu_phuong_tuong_trung_tam():
        pointsPhuongTuongTrungTam = [(801, 300), (300, 335), (300, 335), (300, 290), (300, 290)]
        tap_points(pointsPhuongTuongTrungTam)

    def ban_set_kim_phong():
        def _tick_do(port):
            tap(port, 705, 125)  # đi đến tiệm dược điếm
            time.sleep(2)

            # tap(port, 855, 60)  # click bản đồ
            # time.sleep(1)
            # tap(port, 190, 120)  # click tiệm dược điếm
            # time.sleep(2)

            tap(port, 835, 255)  # nhấn nút nói chuyện
            time.sleep(0.5)
            tap(port, 320, 295)  # giao dịch
            time.sleep(0.5)
            tap(port, 775, 465)  # bấm nút bán nhanh
            time.sleep(0.3)
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

    def nv1_bst():
        n1_bst = [(60, 155), (180, 210), (815, 460)]
        tap_points(n1_bst, 0.3, merge_devices)

    def nv2_bst():
        n2_bst = [(60, 155), (185, 245), (815, 460)]
        tap_points(n2_bst, 0.3, merge_devices)

    def nv3_bst_suphu():
        n2_bst = [(60, 155), (185, 175), (815, 460)]
        tap_points(n2_bst, 0.3, merge_devices)

    def nhan_nv():
        tap_all_devices(310, 290)

    def logOut():
        pointsLogOut = [(946, 257), (946, 337), (153, 115), (800, 250)]
        tap_points(pointsLogOut, 0.5, merge_devices)

    def turnOffAuto(mode=None):
        check_shells_created()

        def _pick_items(port):
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

        def _buy_items(port):
            tap(port, 130, 360)  # click mục mua đồ
            time.sleep(2)
            tap(port, 205, 240)
            tap(port, 205, 275)
            tap(port, 385, 350)
            tap(port, 385, 215)

        def _attack(port):
            tap(port, 130, 255)  # click mục tấn công
            time.sleep(2)
            tap(port, 205, 335)
            tap(port, 205, 380)
            tap(port, 380, 335)
            tap(port, 380, 380)

        def _move(port):
            tap(port, 130, 290)  # click mục di chuyển
            time.sleep(2)
            tap(port, 205, 160)

        def _turn_off_auto(port):
            swipe(port, 690, 455, 690, 455, 2000)
            time.sleep(2)

            if mode == "tat_nhat_do":
                _pick_items(port)
                return

            if mode == "tat_mua_do":
                _buy_items(port)
                return

            if mode == "tat_tan_cong":
                _attack(port)
                return

            if mode == "tat_di_chuyen":
                _move(port)
                return

            # mode = None -> chạy toàn bộ
            _pick_items(port)
            time.sleep(2)
            _buy_items(port)
            time.sleep(2)
            _attack(port)
            time.sleep(2)
            _move(port)

        threads = []
        for port in merge_devices.values():
            t = threading.Thread(target=_turn_off_auto, args=(port,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def nang_skill():
        print("")

    hotkeys = {
        "w": cancel_popup_task,
        "e": cancel_tab_task,
        "r": phu_phuong_tuong_trung_tam,
        "t": tang_diem_sinh_khi,
        "b": ban_set_kim_phong,
        "a": nv1_bst,
        "s": nv2_bst,
        "d": nv3_bst_suphu,
        "z": nhan_nv,
        "g": turnOffAuto("tat_nhat_do"),
        "h": turnOffAuto("tat_mua_do"),
        "j": turnOffAuto("tat_tan_cong"),
        "k": turnOffAuto(),
        "l": nang_skill(),
        "m": logOut,
    }

    for key, func in hotkeys.items():
        keyboard.add_hotkey(key, func)

    print("\n===== CÀY VẠN =====")
    print("w: Hủy popup nhiệm vụ")
    print("e: Hủy tab nhiệm vụ")
    print("r: phù về phượng tường trung tâm")
    print("t: tăng điểm sinh khí")
    print("b: bán đồ kim phong")
    print("a: NV1")
    print("s: NV2")
    print("d: NV3 Sư phụ")
    print("z: Nhận nhiệm vụ")

    print("g: tắt nhặt đồ")
    print("h: tắt mua đồ")
    print("j: tắt tự động đánh")
    print("k: tắt hết")

    print("l: nâng skill")

    print("m: Log out")
    print("q: Thoát")

    keyboard.wait("q")

    # Xóa toàn bộ hotkey
    for key in hotkeys:
        keyboard.remove_hotkey(key)
