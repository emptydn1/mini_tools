"""
=====================================================================
 CHUONG TRINH DONG BO CHUOT + BAN PHIM TUYET DOI CHO 4 PC (1 MASTER - 3 SLAVE)
 (BAN SUA LOI: click yeu khi di chuyen chuot nhanh)
=====================================================================

FIX SO VOI BAN GOC:
  - Van de: khi di chuot rat nhanh roi click ngay, lenh KEYDOWN/KEYUP cua
    nut chuot co the toi Slave truoc khi vi tri MOVE moi nhat kip "on dinh"
    (do 2 luong mouse_loop / key_loop poll doc lap nhau + mot so ung dung
    Windows can mot khoang lang de nhan dien vi tri chuot moi truoc khi
    xu ly mouse-down).
  - Fix:
      1) Khi phat hien nut chuot vua nhan/nha (trong key_loop cua Master),
         CHU DONG lay vi tri chuot hien tai va broadcast MOVE ngay lap tuc
         (bo qua co che throttle "chi gui khi doi vi tri"), roi moi
         broadcast lenh KEYDOWN/KEYUP cho nut chuot đó.
      2) O Slave, khi nhan MOVE thi luu lai vi tri; khi nhan lenh nut
         chuot thi dam bao SetCursorPos da duoc goi lai (dam bao dung vi
         tri) va them mot khoang nghi rat nho (vai mili giay) truoc khi
         goi mouse_event(...DOWN), giup Windows/ung dung dich kip nhan
         dien vi tri moi truoc khi xu ly click.
=====================================================================
"""

import socket
import threading
import time
import sys
import argparse
import win32api
import win32con

# ========================= CAU HINH =========================
parser = argparse.ArgumentParser()
parser.add_argument("--role", "-r", required=True, choices=["MASTER", "SLAVE"], help="MASTER hoac SLAVE")
parser.add_argument("--ip", "-i", default="192.168.1.35", help="IP cua may MASTER (dung khi chay SLAVE)")
args = parser.parse_args()


# ROLE = "MASTER"  # "MASTER" hoac "SLAVE" -> DOI O DAY
ROLE = args.role
PORT = 5555

MASTER_BIND_IP = "0.0.0.0"
MASTER_IP = args.ip

MOUSE_POLL_INTERVAL = 0.005
KEY_POLL_INTERVAL = 0.01


# Khoang nghi (giay) o Slave truoc khi thuc hien mouse-down, de dam bao
# Windows/ung dung dich da "nhan dien" vi tri chuot moi. Neu van con bi
# click yeu khi di rat nhanh, co the tang nhe len 0.012 - 0.02.
CLICK_SETTLE_DELAY = 0.008
# ==============================================================

VK_MOUSE_BUTTONS = {
    0x01: "LEFT",
    0x02: "RIGHT",
    0x04: "MIDDLE",
}


def get_screen_size():
    w = win32api.GetSystemMetrics(0)
    h = win32api.GetSystemMetrics(1)
    return w, h


def is_sync_enabled() -> bool:
    return bool(win32api.GetKeyState(win32con.VK_SCROLL) & 1)


def get_local_ip() -> str:
    """Lay IP LAN cua may hien tai."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


# ===================================================================
#                              MASTER
# ===================================================================
class MasterServer:
    def __init__(self):
        self.clients = []
        self.clients_lock = threading.Lock()
        self.running = True
        self.screen_w, self.screen_h = get_screen_size()
        self.last_pos = None
        self.last_sent_pos = None
        self.key_states = {}

    def start(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((MASTER_BIND_IP, PORT))
        server_sock.listen(8)
        print(f"[MASTER] Dang lang nghe tren cong {PORT}. Do phan giai man hinh Master: {self.screen_w}x{self.screen_h}")

        threading.Thread(target=self.accept_loop, args=(server_sock,), daemon=True).start()
        threading.Thread(target=self.mouse_loop, daemon=True).start()
        threading.Thread(target=self.key_loop, daemon=True).start()
        threading.Thread(target=self.sync_status_loop, daemon=True).start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[MASTER] Dang dung chuong trinh...")
        finally:
            self.release_all_keys()
            time.sleep(0.1)
            self.running = False
            try:
                server_sock.close()
            except OSError:
                pass
            with self.clients_lock:
                for c in self.clients:
                    try:
                        c.close()
                    except OSError:
                        pass
            print("[MASTER] Da dong. Tam biet.")

    def release_all_keys(self):
        pressed = [vk for vk, down in self.key_states.items() if down]
        if not pressed:
            return
        print(f"[MASTER] Dang tu dong nha {len(pressed)} phim con giu: {pressed}")
        for vk in pressed:
            self.key_states[vk] = False
            self.broadcast(f"KEYUP {vk}")

    def accept_loop(self, server_sock):
        while self.running:
            try:
                conn, addr = server_sock.accept()
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                with self.clients_lock:
                    self.clients.append(conn)
                print(f"[MASTER] Slave da ket noi: {addr}")
            except OSError:
                break

    def broadcast(self, message: str):
        data = (message + "\n").encode("utf-8")
        dead = []
        with self.clients_lock:
            for c in self.clients:
                try:
                    c.sendall(data)
                except OSError:
                    dead.append(c)
            for d in dead:
                self.clients.remove(d)
                try:
                    d.close()
                except OSError:
                    pass

    def send_current_pos(self, force: bool = False):
        """Gui vi tri chuot HIEN TAI ngay lap tuc.
        force=True: bo qua throttle, luon gui (dung truoc khi click)."""
        x, y = win32api.GetCursorPos()
        if not force and (x, y) == self.last_sent_pos:
            return
        self.last_pos = (x, y)
        self.last_sent_pos = (x, y)
        if is_sync_enabled():
            rx = x / self.screen_w
            ry = y / self.screen_h
            self.broadcast(f"MOVE {rx:.6f} {ry:.6f}")

    def mouse_loop(self):
        while self.running:
            x, y = win32api.GetCursorPos()
            if (x, y) != self.last_pos:
                self.last_pos = (x, y)
                if is_sync_enabled():
                    self.last_sent_pos = (x, y)
                    rx = x / self.screen_w
                    ry = y / self.screen_h
                    self.broadcast(f"MOVE {rx:.6f} {ry:.6f}")
            time.sleep(MOUSE_POLL_INTERVAL)

    def key_loop(self):
        vk_codes = list(range(1, 255))
        for vk in vk_codes:
            self.key_states[vk] = False

        while self.running:
            sync_on = is_sync_enabled()
            for vk in vk_codes:
                state = win32api.GetAsyncKeyState(vk)
                is_down = bool(state & 0x8000)
                was_down = self.key_states[vk]

                if is_down and not was_down:
                    self.key_states[vk] = True
                    if sync_on:
                        # FIX: neu la nut chuot, ep gui vi tri hien tai
                        # NGAY TRUOC khi gui lenh KEYDOWN, dam bao Slave
                        # luon co vi tri moi nhat truoc khi click.
                        if vk in VK_MOUSE_BUTTONS:
                            self.send_current_pos(force=True)
                        self.broadcast(f"KEYDOWN {vk}")
                elif not is_down and was_down:
                    self.key_states[vk] = False
                    if sync_on:
                        if vk in VK_MOUSE_BUTTONS:
                            self.send_current_pos(force=True)
                        self.broadcast(f"KEYUP {vk}")
            time.sleep(KEY_POLL_INTERVAL)

    def sync_status_loop(self):
        last_state = None
        while self.running:
            state = is_sync_enabled()
            if state != last_state:
                last_state = state
                trang_thai = "BAT (ScrLk ON)" if state else "TAT (ScrLk OFF)"
                print(f"[MASTER] >>> Dong bo chuot/ban phim: {trang_thai}")
            time.sleep(0.1)


# ===================================================================
#                              SLAVE
# ===================================================================
class SlaveClient:
    def __init__(self):
        self.screen_w, self.screen_h = get_screen_size()
        self.pressed_keys = set()
        self.last_pos = None  # vi tri x,y cuoi cung da SetCursorPos

    def start(self):
        while True:
            try:
                self.connect_and_run()
            except (ConnectionRefusedError, ConnectionResetError, OSError) as e:
                print(f"[SLAVE] Mat ket noi ({e}).")
                self.release_all_local_keys()
                print("[SLAVE] Thu lai sau 2 giay...")
                time.sleep(2)

    def connect_and_run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((MASTER_IP, PORT))
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        print(f"[SLAVE] Da ket noi toi Master {MASTER_IP}:{PORT}. Do phan giai man hinh: {self.screen_w}x{self.screen_h}")

        buffer = ""
        while True:
            data = sock.recv(4096)
            if not data:
                raise ConnectionResetError("Master da dong ket noi")
            buffer += data.decode("utf-8", errors="ignore")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                self.handle_line(line.strip())

    def handle_line(self, line: str):
        if not line:
            return
        parts = line.split(" ")
        cmd = parts[0]

        if cmd == "MOVE":
            rx, ry = float(parts[1]), float(parts[2])
            x = int(rx * self.screen_w)
            y = int(ry * self.screen_h)
            self.last_pos = (x, y)
            win32api.SetCursorPos((x, y))

        elif cmd == "KEYDOWN":
            self.apply_key(int(parts[1]), down=True)

        elif cmd == "KEYUP":
            self.apply_key(int(parts[1]), down=False)

    def apply_key(self, vk: int, down: bool):
        if down:
            self.pressed_keys.add(vk)
        else:
            self.pressed_keys.discard(vk)

        if vk in VK_MOUSE_BUTTONS:
            self.apply_mouse_button(vk, down)
        else:
            scan = win32api.MapVirtualKey(vk, 0)
            flags = 0 if down else win32con.KEYEVENTF_KEYUP
            win32api.keybd_event(vk, scan, flags, 0)

    def apply_mouse_button(self, vk: int, down: bool):
        # FIX: truoc khi mouse-down, dam bao vi tri chuot da duoc
        # "chot" lai (goi SetCursorPos lan nua) va cho mot khoang rat
        # nho de he thong/ung dung dich kip nhan dien vi tri moi truoc
        # khi xu ly click. Giup tranh tinh trang click "khong an" khi
        # Master di chuot rat nhanh roi click ngay.
        if down and self.last_pos is not None:
            win32api.SetCursorPos(self.last_pos)
            time.sleep(CLICK_SETTLE_DELAY)

        if vk == 0x01:
            flag = win32con.MOUSEEVENTF_LEFTDOWN if down else win32con.MOUSEEVENTF_LEFTUP
        elif vk == 0x02:
            flag = win32con.MOUSEEVENTF_RIGHTDOWN if down else win32con.MOUSEEVENTF_RIGHTUP
        elif vk == 0x04:
            flag = win32con.MOUSEEVENTF_MIDDLEDOWN if down else win32con.MOUSEEVENTF_MIDDLEUP
        else:
            return
        win32api.mouse_event(flag, 0, 0, 0, 0)

    def release_all_local_keys(self):
        if not self.pressed_keys:
            return
        print(f"[SLAVE] Tu dong nha {len(self.pressed_keys)} phim dang giu de tranh liet phim: {sorted(self.pressed_keys)}")
        for vk in list(self.pressed_keys):
            self.apply_key(vk, down=False)


# ===================================================================
#                               MAIN
# ===================================================================
if __name__ == "__main__":
    if ROLE == "MASTER":
        print(f"[{ROLE}] IP LAN cua may nay: {get_local_ip()}")
        MasterServer().start()
    elif ROLE == "SLAVE":
        SlaveClient().start()
    else:
        print("ROLE khong hop le. Dat ROLE = 'MASTER' hoac 'SLAVE' o dau file.")
        sys.exit(1)
