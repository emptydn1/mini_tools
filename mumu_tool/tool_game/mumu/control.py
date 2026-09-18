import time
import json
import subprocess
import os
import keyboard

from mumu_tool.config import merge_devices, devices
from mumu_tool.adb_core import check_shells_created, tap, input_text, input_text_list
from mumu_tool.tool_game.utils import chon_tu_danh_sach

MUMU_PATH = r"C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe"
# MUMU_PATH = r"C:\Program Files\Netease\MuMuPlayerGlobal-12.0\nx_main\MuMuManager.exe"


def openAllmumuplayer():
    result = subprocess.run([MUMU_PATH, "info", "--vmindex", "all"], capture_output=True, text=True)
    players = json.loads(result.stdout)

    # Tạo map: tên emulator -> index
    name_to_index = {}
    for index, data in players.items():
        name = data.get("name", "")
        name_to_index[name] = index

    # Duyệt qua devices, tìm index tương ứng với từng tên, đưa vào danh sách
    indexes = []
    for name in devices:
        if name in name_to_index:
            indexes.append(name_to_index[name])
        else:
            print(f"Không tìm thấy emulator tên '{name}' trong MuMuManager info")

    for index in indexes:
        print(f"Đang mở emulator index {index} ...")
        subprocess.run([MUMU_PATH, "control", "-v", index, "launch"])
        time.sleep(25)

    check_shells_created()
    for port in devices.values():
        tap(port, 835, 80)
        time.sleep(0.5)
        tap(port, 835, 80)
        time.sleep(0.5)
        tap(port, 560, 120)
        time.sleep(30)


def hoangdnvn():
    check_shells_created()

    pos = ["hoangdnvn10", "hoangdnvn11", "hoangdnvn13", "hoangdnvn14", "hoangdnvn15", "hoangdnvn16", "hoangdnvn17", "hoangdnvn18", "hoangdnvn19", "hoangdnvn20", "hoangdnvn21", "hoangdnvn22", "hoangdnvn23", "hoangdnvn24", "hoangdnvn25", "hoangdnvn26", "hoangdnvn27", "hoangdnvn28", "hoangdnvn29", "hoangdnvn30"]
    input_text_list(pos)


def menu_nhap_theo_danh_sach():
    check_shells_created()

    arr = chon_tu_danh_sach()

    if len(arr) != 3 or not arr[0].isdigit() or not arr[1]:
        print("❌ Sai định dạng! Phải có dạng: 1-huy-1+16")
        input("\nNhấn Enter để tiếp tục...")
        return
    range_part = arr[2].split("+")

    if len(range_part) != 2 or not range_part[0].isdigit() or not range_part[1].isdigit():
        print("❌ Sai định dạng! Phải có dạng: 1-huy-1+16")
        input("\nNhấn Enter để tiếp tục...")
        return

    i_val = int(arr[0])
    name = arr[1]
    start_number = int(range_part[0])
    end_number = int(range_part[1])

    if start_number > end_number:
        print("❌ Số bắt đầu phải nhỏ hơn hoặc bằng số kết thúc!")
        input("\nNhấn Enter để tiếp tục...")
        return

    accounts = [f"{i_val}{name}{j}" for j in range(start_number, end_number + 1)]

    input_text_list(accounts)
