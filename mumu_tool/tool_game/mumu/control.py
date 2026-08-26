import time
import json
import subprocess

from mumu_tool.config import merge_devices, devices
from mumu_tool.adb_core import check_shells_created, tap, input_text, input_text_list

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


def nhap_tai_khoan():
    check_shells_created()

    def _nhap_input(lan):
        while True:
            value = input(f"Nhập lần {lan} (Q để thoát): ").strip()

            if value.lower() == "q":
                return None

            arr = value.split("-")

            if len(arr) != 3 or not arr[0].isdigit() or not arr[2].isdigit() or not arr[1]:
                print("❌ Sai định dạng! Phải có dạng: 1-huy-1")
                continue

            return arr

    arr1 = _nhap_input(1)

    if arr1 is None:
        return

    arr2 = _nhap_input(2)

    if arr2 is None:
        return

    # Kiểm tra tên
    if arr1[1] != arr2[1]:
        print("❌ Tên 2 input phải giống nhau!")
        return

    start = int(arr1[0])
    name = arr1[1]
    end = int(arr2[0])

    start_number = int(arr1[2])
    end_number = int(arr2[2])

    accounts = []
    for i in range(start, end + 1):
        temp = []
        for j in range(start_number, end_number + 1):
            temp.append(f"{i}{name}{j}")
        accounts.append(temp)

    input_text_list(accounts[0])


def hoangdnvn():
    check_shells_created()

    pos = ["hoangdnvn10", "hoangdnvn11", "hoangdnvn13", "hoangdnvn14", "hoangdnvn15", "hoangdnvn16", "hoangdnvn17", "hoangdnvn18", "hoangdnvn19", "hoangdnvn20", "hoangdnvn21", "hoangdnvn22", "hoangdnvn23", "hoangdnvn24", "hoangdnvn25", "hoangdnvn26", "hoangdnvn27", "hoangdnvn28", "hoangdnvn29", "hoangdnvn30"]
    input_text_list(pos)


def menu_nhap_theo_danh_sach():
    check_shells_created()

    try:
        with open(r"C:\Users\huy\Desktop\accounts.txt", "r", encoding="utf-8") as f:
            danh_sach = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Không tìm thấy file 1.txt")
        input("Nhấn Enter để tiếp tục...")
        return

    if not danh_sach:
        print("❌ File 1.txt không có dữ liệu.")
        input("Nhấn Enter để tiếp tục...")
        return

    while True:
        print("\n========== NHẬP THEO DANH SÁCH ==========")

        for i, item in enumerate(danh_sach, 1):
            print(f"{i}. {item}")

        print("Q. Thoát")
        print("==========================================")

        choice = input("Chọn: ").strip().lower()

        if choice == "q":
            break

        if not choice.isdigit():
            print("❌ Lựa chọn không hợp lệ.")
            continue

        index = int(choice) - 1

        if index < 0 or index >= len(danh_sach):
            print("❌ Lựa chọn không hợp lệ.")
            continue

        data = danh_sach[index]

        print(f"▶ Đã chọn: {data}")

        parts = data.split()

        arr1 = parts[0].split("-")
        arr2 = parts[1].split("-")

        start = int(arr1[0])
        name = arr1[1]
        end = int(arr2[0])

        start_number = int(arr1[2])
        end_number = int(arr2[2])

        accounts = []
        for i in range(start, end + 1):
            temp = []
            for j in range(start_number, end_number + 1):
                temp.append(f"{i}{name}{j}")
            accounts.append(temp)

        input_text_list(accounts[0])

        input("\nNhấn Enter để tiếp tục...")
