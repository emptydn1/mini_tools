import os
import sys
import subprocess
import socket
import ipaddress
import platform
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


def get_local_network():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return str(ipaddress.ip_network(ip + "/24", strict=False))


def ping(ip):
    cmd = ["ping", "-n", "1", "-w", "800", ip] if platform.system().lower() == "windows" else ["ping", "-c", "1", "-W", "1", ip]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_arp_table():
    output = subprocess.run(["arp", "-a"], capture_output=True, text=True).stdout
    ip_pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    ips = []
    for line in output.splitlines():
        match = re.search(ip_pattern, line)
        if match:
            ips.append(match.group(1))
    return ips


def scan_lan_ips():
    """Quét mạng LAN, trả về danh sách IP đang hoạt động (đã sort)."""
    network = get_local_network()
    hosts = [str(ip) for ip in ipaddress.ip_network(network).hosts()]

    print(f"Đang quét {len(hosts)} địa chỉ trong mạng LAN...")
    with ThreadPoolExecutor(max_workers=100) as executor:
        list(executor.map(ping, hosts))

    net = ipaddress.ip_network(network)
    active_ips = sorted({ip for ip in get_arp_table() if ipaddress.ip_address(ip) in net}, key=lambda x: ipaddress.ip_address(x))
    return active_ips


def sync_mouse_keyboard(role):
    CREATE_NEW_CONSOLE = 0x00000010
    file_path = Path(__file__).parent / "sync.py"

    if role == "MASTER":
        subprocess.Popen([sys.executable, file_path, "--role", role, "--ip", "192.168.1.35"], creationflags=CREATE_NEW_CONSOLE)

    elif role == "SLAVE":
        danh_sach = scan_lan_ips()

        if not danh_sach:
            print("❌ Không tìm thấy IP nào đang hoạt động trong mạng LAN.")
            input("Nhấn Enter để tiếp tục...")
            return

        while True:
            print("\n========== CHỌN IP TRONG MẠNG LAN ==========")

            for i, item in enumerate(danh_sach, 1):
                print(f"{i}. {item}")

            print("R. Quét lại")
            print("Q. Thoát")
            print("=============================================")

            choice = input("Chọn: ").strip().lower()

            if choice == "q":
                break

            if choice == "r":
                danh_sach = scan_lan_ips()
                continue

            if not choice.isdigit():
                print("❌ Lựa chọn không hợp lệ.")
                continue

            index = int(choice) - 1

            if index < 0 or index >= len(danh_sach):
                print("❌ Lựa chọn không hợp lệ.")
                continue

            data = danh_sach[index]

            print(f"▶ Đã chọn: {data}")

            subprocess.Popen([sys.executable, file_path, "--role", role, "--ip", data], creationflags=CREATE_NEW_CONSOLE)

            input("\nNhấn Enter để tiếp tục...")
