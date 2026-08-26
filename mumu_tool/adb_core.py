"""
Các hàm lõi để giao tiếp với thiết bị qua ADB:
- Mở/duy trì shell adb cho từng port
- Gửi lệnh input (tap, swipe, text)
- Tự động reconnect khi lỗi
"""

import subprocess
import threading
import time

from .config import devices1, devices2, merge_devices, devices

shells = {}


def check_shells_created():
    if shells:
        print(f"✅ shells đã có {len(shells)} kết nối, bỏ qua bước connect.")
        return

    print("⚠️ shells đang rỗng, tiến hành connect adb + mở shell...")

    for port in list(devices1.values()) + list(devices2.values()):
        subprocess.run(["adb", "connect", f"127.0.0.1:{port}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for name, port in merge_devices.items():
        shells[port] = subprocess.Popen(["adb", "-s", f"127.0.0.1:{port}", "shell"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True, bufsize=1)
    print(f"✅ Đã mở {len(shells)} shell.")


def reconnect_device(port):
    try:
        if port in shells:
            try:
                shells[port].stdin.close()
                shells[port].terminate()
            except Exception:
                pass

        subprocess.run(["adb", "disconnect", f"127.0.0.1:{port}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)
        subprocess.run(["adb", "connect", f"127.0.0.1:{port}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)

        shells[port] = subprocess.Popen(["adb", "-s", f"127.0.0.1:{port}", "shell"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        print(f"[RECONNECTED] {port}")
    except Exception as e:
        print(f"[RECONNECT ERROR] {port}: {e}")


def send_shell_command(port, command, error_type="ERROR"):
    try:
        shells[port].stdin.write(command + "\n")
        shells[port].stdin.flush()
        return True
    except Exception as e:
        pass
        # print(f"[{error_type}] {port}: {e}")
        # mở cái này khi muốn reconnect_device chứ mà mở hiện tại thì nó sẽ block tiến trình, tool sẽ rất chậm
        # reconnect_device(port)
        # try:
        #     shells[port].stdin.write(command + "\n")
        #     shells[port].stdin.flush()
        #     return True
        # except Exception as e2:
        #     print(f"[RETRY FAILED] {port}: {e2}")
        #     return False


def tap(port, x, y):
    send_shell_command(port, f"input tap {x} {y}", "TAP ERROR")


def input_text(port, text):
    send_shell_command(port, f'input text "{text}"', "TEXT ERROR")


def swipe(port, x1, y1, x2, y2, duration=300):
    send_shell_command(port, f"input swipe {x1} {y1} {x2} {y2} {duration}", "SWIPE ERROR")


def swipe_all_devices(x1, y1, x2, y2, duration=300):
    for port in merge_devices.values():
        threading.Thread(target=swipe, args=(port, x1, y1, x2, y2, duration), daemon=True).start()


# tất cả giả lập đều nhập text song song
def input_text_list(pos):
    threads = []

    for port, text in zip(merge_devices.values(), pos):
        t = threading.Thread(target=input_text, args=(port, text))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


# tất cả giả lập đều tap song song
def tap_all_devices(x, y):
    for port in merge_devices.values():
        threading.Thread(target=tap, args=(port, x, y), daemon=True).start()


# tap song song dựa theo mảng points
def tap_points(points, delay=0.3, devices_dict=None):
    if devices_dict is None:
        devices_dict = devices

    for x, y in points:
        threads = []

        for port in devices_dict.values():
            t = threading.Thread(target=tap, args=(port, x, y))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        time.sleep(delay)
