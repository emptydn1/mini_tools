import socket
import ipaddress
import subprocess
import platform
import re
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
    system = platform.system().lower()
    cmd = ["arp", "-a"]
    output = subprocess.run(cmd, capture_output=True, text=True).stdout

    ip_pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    ips = []
    for line in output.splitlines():
        match = re.search(ip_pattern, line)
        if match:
            ips.append(match.group(1))
    return ips


network = get_local_network()
hosts = [str(ip) for ip in ipaddress.ip_network(network).hosts()]

print(f"Đang ping {len(hosts)} địa chỉ để nạp vào bảng ARP...")
with ThreadPoolExecutor(max_workers=100) as executor:
    list(executor.map(ping, hosts))

print("\nCác IP đang hoạt động (theo bảng ARP hệ thống):\n")
for ip in sorted(set(get_arp_table()), key=lambda x: ipaddress.ip_address(x)):
    if ipaddress.ip_address(ip) in ipaddress.ip_network(network):
        print(ip)
