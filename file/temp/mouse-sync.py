"""
=====================================================================
 CHUONG TRINH DONG BO CHUOT + BAN PHIM TUYET DOI CHO 4 PC (1 MASTER - 3 SLAVE)
 PHIEN BAN 3: chuyen sang co che HOOK (theo su kien), bo hoan toan vong poll
=====================================================================

CACH CHAY (giong ban cu):
    Master: python dong_bo_chuot_ban_phim.py -r MASTER
    Slave : python dong_bo_chuot_ban_phim.py -r SLAVE -i <IP_cua_Master>
    Bat/tat dong bo bang phim Scroll Lock tren Master.

    !!! Giao thuc da doi -> PHAI chep file nay len CA 4 MAY.
    !!! Khong can pywin32 nua (chi dung ctypes co san trong Python).
    Neu game/ung dung chay bang quyen Administrator thi chuong trinh nay
    cung phai chay bang Administrator (Windows chan phan mem quyen thap
    doc/gui phim vao cua so quyen cao).

NHUNG GI DA SUA SO VOI BAN TRUOC:
  1) Master dung low-level hook (WH_KEYBOARD_LL + WH_MOUSE_LL) thay cho
     vong poll 254 phim moi 10ms + GetCursorPos moi 5ms:
       - Luc ranh gan nhu 0% CPU (ban cu goi ~25.000 lan GetAsyncKeyState
         moi giay, ke ca khi khong ai cham vao may).
       - Khong con tre 5-10ms do chu ky poll, khong bo sot lan nhan nhanh.
       - Di chuot / click / cuon / phim di ra DUNG THU TU xay ra that,
         nen khong con canh "lenh click toi Slave truoc vi tri chuot".
  2) Lenh click mang theo toa do cua chinh no (vd: MDOWN L 0.5 0.5).
     Slave dat chuot dung cho roi moi click. Khoang nghi CLICK_SETTLE_DELAY
     chi ap dung khi chuot vua moi doi cho, khong con lam cham moi click.
  3) Gom chuoi MOVE lien tiep: chi gui/ap dung vi tri moi nhat, ghep nhieu
     lenh vao 1 goi TCP -> Slave khong bi do don khi mang cham.
  4) Moi Slave co luong gui rieng: 1 may lag/treo khong keo cham may khac.
  5) Ban phim:
       - Gui kem scan code + co "extended": phim mui ten, Insert/Delete,
         Home/End, Ctrl/Alt ben phai, Enter va "/" cua Numpad... dung han.
       - Het loi Shift/Ctrl/Alt bi gui 2 lan (ban cu gui ca VK_SHIFT lan
         VK_LSHIFT cho cung 1 lan nhan).
       - Giu phim tren Master thi Slave cung tu lap phim (ban cu giu
         Backspace tren Master thi Slave chi xoa 1 ky tu).
       - Phim Scroll Lock khong bi gui sang Slave.
  6) Chong ket phim:
       - Tat dong bo (ScrLk OFF) -> tu nha moi phim/nut dang giu tren Slave.
       - Phim bi "mat" su kien nha (Ctrl+Alt+Del, Win+L, cua so Admin...)
         duoc phat hien va tu nha sau khoang 0.3 giay.
       - Master gui PING moi giay; Slave khong nhan duoc gi trong 3 giay se
         tu nha phim va ket noi lai (Master bi tat / rot mang dot ngot).
  7) Bat DPI awareness: toa do dung tung pixel ca khi man hinh scale
     125%/150%. Sua luon loi lech 1 pixel o mep phai/duoi cua ban cu.
  8) Tat che do QuickEdit cua cua so console: lo click vao cua so den
     khong lam chuong trinh bi dung hinh nua.
=====================================================================
"""

import argparse
import ctypes
import math
import queue
import socket
import sys
import threading
import time
from ctypes import wintypes

if sys.platform != "win32":
    sys.exit("Chuong trinh nay chi chay tren Windows.")

# ========================= CAU HINH =========================
parser = argparse.ArgumentParser(description="Dong bo chuot + ban phim cho nhieu PC")
parser.add_argument("--role", "-r", required=True, type=str.upper, choices=["MASTER", "SLAVE"],
                    help="MASTER hoac SLAVE")
parser.add_argument("--ip", "-i", default="192.168.1.35", help="IP cua may MASTER (dung khi chay SLAVE)")
args = parser.parse_args()

ROLE = args.role
PORT = 5555
MASTER_BIND_IP = "0.0.0.0"
MASTER_IP = args.ip

# Khoang nghi (giay) o Slave truoc khi mouse-down, CHI ap dung khi chuot vua
# moi doi vi tri (de ung dung/game kip nhan vi tri moi). Neu van con click
# yeu khi di rat nhanh, co the tang nhe len 0.012 - 0.02.
CLICK_SETTLE_DELAY = 0.008

IDLE_POLL_INTERVAL = 0.05    # Master: chu ky kiem tra luc ranh (ScrLk, chuot bi phan mem dich chuyen)
STUCK_CHECK_INTERVAL = 0.1   # Master: chu ky kiem tra phim bi ket
STUCK_MIN_AGE = 0.3          # chi coi la ket neu phim da duoc giu lau hon muc nay (giay)
HEARTBEAT_INTERVAL = 1.0     # Master gui PING neu khong co gi de gui trong ngan nay giay
HEARTBEAT_TIMEOUT = 3.0      # Slave: khong nhan duoc gi trong ngan nay giay -> coi nhu mat ket noi
CLIENT_QUEUE_MAX = 5000      # so goi cho gui toi da cho 1 Slave truoc khi coi Slave do da "chet"
# ==============================================================


# ===================================================================
#                 WIN32 API (qua ctypes, khong can pywin32)
# ===================================================================
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

ULONG_PTR = ctypes.c_size_t
LRESULT = ctypes.c_ssize_t
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14
HC_ACTION = 0
WM_QUIT = 0x0012
PM_NOREMOVE = 0x0000

WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0201, 0x0202
WM_RBUTTONDOWN, WM_RBUTTONUP = 0x0204, 0x0205
WM_MBUTTONDOWN, WM_MBUTTONUP = 0x0207, 0x0208
WM_MOUSEWHEEL = 0x020A
WM_XBUTTONDOWN, WM_XBUTTONUP = 0x020B, 0x020C
WM_MOUSEHWHEEL = 0x020E

LLKHF_EXTENDED = 0x01
LLKHF_UP = 0x80

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004
MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP = 0x0008, 0x0010
MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP = 0x0020, 0x0040
MOUSEEVENTF_XDOWN, MOUSEEVENTF_XUP = 0x0080, 0x0100
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000
XBUTTON1, XBUTTON2 = 0x0001, 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
MAPVK_VK_TO_VSC = 0

VK_SCROLL = 0x91
VK_PACKET = 0xE7
SM_CXSCREEN, SM_CYSCREEN = 0, 1
SM_SWAPBUTTON = 23
SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77
SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79
THREAD_PRIORITY_HIGHEST = 2
STD_INPUT_HANDLE = 0xFFFFFFF6        # (DWORD)-10
ENABLE_QUICK_EDIT_MODE = 0x0040
ENABLE_EXTENDED_FLAGS = 0x0080


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD), ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("pt", wintypes.POINT), ("mouseData", wintypes.DWORD), ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


def _sig(func, restype, *argtypes):
    func.restype = restype
    func.argtypes = list(argtypes)


_sig(user32.GetSystemMetrics, ctypes.c_int, ctypes.c_int)
_sig(user32.GetCursorPos, wintypes.BOOL, ctypes.POINTER(wintypes.POINT))
_sig(user32.SetCursorPos, wintypes.BOOL, ctypes.c_int, ctypes.c_int)
_sig(user32.GetKeyState, ctypes.c_short, ctypes.c_int)
_sig(user32.GetAsyncKeyState, ctypes.c_short, ctypes.c_int)
_sig(user32.SendInput, wintypes.UINT, wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
_sig(user32.MapVirtualKeyW, wintypes.UINT, wintypes.UINT, wintypes.UINT)
_sig(user32.SetWindowsHookExW, wintypes.HHOOK, ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD)
_sig(user32.CallNextHookEx, LRESULT, wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
_sig(user32.UnhookWindowsHookEx, wintypes.BOOL, wintypes.HHOOK)
_sig(user32.GetMessageW, wintypes.BOOL, ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT)
_sig(user32.PeekMessageW, wintypes.BOOL, ctypes.POINTER(wintypes.MSG), wintypes.HWND,
     wintypes.UINT, wintypes.UINT, wintypes.UINT)
_sig(user32.PostThreadMessageW, wintypes.BOOL, wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
_sig(kernel32.GetModuleHandleW, wintypes.HMODULE, wintypes.LPCWSTR)
_sig(kernel32.GetCurrentThreadId, wintypes.DWORD)
_sig(kernel32.GetCurrentThread, wintypes.HANDLE)
_sig(kernel32.SetThreadPriority, wintypes.BOOL, wintypes.HANDLE, ctypes.c_int)
_sig(kernel32.GetStdHandle, wintypes.HANDLE, wintypes.DWORD)
_sig(kernel32.GetConsoleMode, wintypes.BOOL, wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
_sig(kernel32.SetConsoleMode, wintypes.BOOL, wintypes.HANDLE, wintypes.DWORD)


# ===================================================================
#                           HAM TIEN ICH
# ===================================================================
def get_screen_size():
    return user32.GetSystemMetrics(SM_CXSCREEN), user32.GetSystemMetrics(SM_CYSCREEN)


def get_virtual_screen():
    """Hinh chu nhat bao tat ca man hinh (x, y, rong, cao)."""
    return (user32.GetSystemMetrics(SM_XVIRTUALSCREEN), user32.GetSystemMetrics(SM_YVIRTUALSCREEN),
            user32.GetSystemMetrics(SM_CXVIRTUALSCREEN), user32.GetSystemMetrics(SM_CYVIRTUALSCREEN))


def get_cursor_pos():
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def is_sync_enabled() -> bool:
    return bool(user32.GetKeyState(VK_SCROLL) & 1)


def is_physically_down(vk: int) -> bool:
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def mouse_input(flags: int, data: int = 0) -> INPUT:
    # data co the am (cuon xuong / sang trai) -> doi sang DWORD bu 2
    return INPUT(type=INPUT_MOUSE, u=_INPUTUNION(mi=MOUSEINPUT(0, 0, data & 0xFFFFFFFF, flags, 0, 0)))


def key_input(vk: int, scan: int, flags: int) -> INPUT:
    return INPUT(type=INPUT_KEYBOARD, u=_INPUTUNION(ki=KEYBDINPUT(vk, scan, flags, 0, 0)))


def send_inputs(inputs):
    n = len(inputs)
    if n:
        user32.SendInput(n, (INPUT * n)(*inputs), ctypes.sizeof(INPUT))


def enable_dpi_awareness():
    """Dung toa do pixel that, khong bi Windows 'scale ao' khi man hinh 125%/150%."""
    try:
        if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):  # PER_MONITOR_AWARE_V2 (Win10 1703+)
            return
    except AttributeError:
        pass
    try:
        ctypes.WinDLL("shcore").SetProcessDpiAwareness(2)  # PER_MONITOR_AWARE (Win 8.1+)
        return
    except (AttributeError, OSError):
        pass
    try:
        user32.SetProcessDPIAware()  # Win Vista / 7
    except AttributeError:
        pass


def disable_quick_edit():
    """Click nham vao cua so console dang o che do QuickEdit se lam moi lenh
    print() bi treo -> chuong trinh 'dung hinh'. Tat che do nay di."""
    handle = kernel32.GetStdHandle(STD_INPUT_HANDLE)
    mode = wintypes.DWORD()
    if handle and kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        kernel32.SetConsoleMode(handle, (mode.value & ~ENABLE_QUICK_EDIT_MODE) | ENABLE_EXTENDED_FLAGS)


def raise_thread_priority():
    kernel32.SetThreadPriority(kernel32.GetCurrentThread(), THREAD_PRIORITY_HIGHEST)


def set_timer_resolution():
    """Giup time.sleep() vai mili giay chinh xac (mac dinh Windows lam tron len ~15ms)."""
    try:
        ctypes.WinDLL("winmm").timeBeginPeriod(1)
    except (AttributeError, OSError):
        pass


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
#                             GIAO THUC
# ===================================================================
# Moi lenh la 1 dong text ket thuc bang "\n". Toa do gui di dang ty le
# (0..1) theo man hinh chinh, nen cac may khac do phan giai van dung.
#   MOVE rx ry                 di chuot
#   MDOWN <nut> rx ry          nhan nut chuot TAI toa do do   (nut: L R M X1 X2)
#   MUP <nut> rx ry            nha nut chuot TAI toa do do
#   WHEEL delta / HWHEEL delta cuon doc / cuon ngang (120 = 1 nac)
#   KEYDOWN vk scan ext        nhan phim (ext = 1 neu la phim "extended")
#   KEYUP vk scan ext          nha phim
#   PING                       giu ket noi, Slave bo qua

# Ten nut -> (co DOWN, co UP, mouseData, ma VK dung de kiem tra nut that)
MOUSE_BUTTONS = {
    "L": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP, 0, 0x01),
    "R": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP, 0, 0x02),
    "M": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP, 0, 0x04),
    "X1": (MOUSEEVENTF_XDOWN, MOUSEEVENTF_XUP, XBUTTON1, 0x05),  # nut phu Back
    "X2": (MOUSEEVENTF_XDOWN, MOUSEEVENTF_XUP, XBUTTON2, 0x06),  # nut phu Forward
}

# Message cua mouse hook -> (ten nut, la DOWN?). "X" duoc tach thanh X1/X2 sau.
BUTTON_MESSAGES = {
    WM_LBUTTONDOWN: ("L", True), WM_LBUTTONUP: ("L", False),
    WM_RBUTTONDOWN: ("R", True), WM_RBUTTONUP: ("R", False),
    WM_MBUTTONDOWN: ("M", True), WM_MBUTTONUP: ("M", False),
    WM_XBUTTONDOWN: ("X", True), WM_XBUTTONUP: ("X", False),
}

# Loai su kien noi bo cua Master (hook -> luong dieu phoi)
EV_MOVE, EV_BUTTON, EV_WHEEL, EV_KEY, EV_STOP = range(5)


# ===================================================================
#                              MASTER
# ===================================================================
class SlaveConn:
    """Ket noi toi 1 Slave, co hang doi + luong gui rieng.
    Slave nao cham/treo thi chi hang doi cua no day len, khong anh huong may khac."""

    def __init__(self, sock, addr, on_close):
        self.sock = sock
        self.addr = addr
        self.on_close = on_close
        self.queue = queue.Queue(maxsize=CLIENT_QUEUE_MAX)
        self.closed = False
        self._lock = threading.Lock()
        self.thread = threading.Thread(target=self._send_loop, daemon=True)
        self.thread.start()

    def push(self, data: bytes):
        if self.closed:
            return
        try:
            self.queue.put_nowait(data)
        except queue.Full:
            self.close("Slave qua cham, hang doi gui bi day")

    def finish(self):
        """Gui het du lieu con trong hang doi roi dong ket noi."""
        try:
            self.queue.put_nowait(None)
        except queue.Full:
            self.close("dong chuong trinh")

    def _send_loop(self):
        reason = "dong chuong trinh"
        try:
            while True:
                item = self.queue.get()
                if item is None:
                    break
                # Gom tat ca goi dang cho thanh 1 lan gui
                chunks = [item]
                done = False
                while True:
                    try:
                        item = self.queue.get_nowait()
                    except queue.Empty:
                        break
                    if item is None:
                        done = True
                        break
                    chunks.append(item)
                self.sock.sendall(chunks[0] if len(chunks) == 1 else b"".join(chunks))
                if done:
                    break
        except OSError as e:
            reason = str(e)
        self.close(reason)

    def close(self, reason: str = ""):
        with self._lock:
            if self.closed:
                return
            self.closed = True
        try:
            self.sock.close()
        except OSError:
            pass
        try:
            self.queue.put_nowait(None)  # danh thuc luong gui neu no dang cho
        except queue.Full:
            pass
        self.on_close(self, reason)


class MasterServer:
    def __init__(self):
        self.screen_w, self.screen_h = get_screen_size()
        self.vx, self.vy, self.vw, self.vh = get_virtual_screen()
        self.events = queue.Queue()          # hook -> luong dieu phoi
        self.clients = []
        self.clients_lock = threading.Lock()
        self.hook_tid = None
        self.hook_ok = False
        self.hook_ready = threading.Event()
        self.dispatch_done = threading.Event()
        self._hook_callbacks = []            # giu tham chieu callback, tranh bi GC thu hoi
        # --- Trang thai duoi day CHI luong dieu phoi dung -> khong can khoa ---
        self.sync_on = None
        self.last_sent_pos = None
        self.pending_move = None
        self.keys_down = {}                  # vk -> (scan, ext, thoi diem nhan) da gui KEYDOWN
        self.buttons_down = {}               # ten nut -> thoi diem nhan, da gui MDOWN
        self.last_send_time = 0.0
        self.last_stuck_check = 0.0

    # ------------------------------------------------------------------
    def start(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((MASTER_BIND_IP, PORT))
        server_sock.listen(8)
        print(f"[MASTER] Dang lang nghe tren cong {PORT}. Do phan giai man hinh Master: "
              f"{self.screen_w}x{self.screen_h}")

        threading.Thread(target=self.hook_loop, daemon=True).start()
        self.hook_ready.wait(5)
        if not self.hook_ok:
            server_sock.close()
            sys.exit("[MASTER] Khong cai duoc hook ban phim/chuot -> thoat.")

        threading.Thread(target=self.dispatch_loop, daemon=True).start()
        threading.Thread(target=self.accept_loop, args=(server_sock,), daemon=True).start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[MASTER] Dang dung chuong trinh...")
        finally:
            if self.hook_tid:
                user32.PostThreadMessageW(self.hook_tid, WM_QUIT, 0, 0)
            self.events.put((EV_STOP,))          # luong dieu phoi se nha het phim tren Slave
            self.dispatch_done.wait(1.0)
            with self.clients_lock:
                clients = list(self.clients)
            for c in clients:
                c.finish()
            for c in clients:
                c.thread.join(timeout=1.0)
            try:
                server_sock.close()
            except OSError:
                pass
            print("[MASTER] Da dong. Tam biet.")

    # ------------------------------------------------------------------
    def accept_loop(self, server_sock):
        while True:
            try:
                conn, addr = server_sock.accept()
            except OSError:
                break
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            client = SlaveConn(conn, addr, self._remove_client)
            if is_sync_enabled():
                # Dua chuot cua Slave moi ket noi ve dung vi tri hien tai ngay
                x, y = self._clamp(*get_cursor_pos())
                client.push(f"MOVE {self._norm(x, y)}\n".encode("ascii"))
            with self.clients_lock:
                self.clients.append(client)
                total = len(self.clients)
            print(f"[MASTER] Slave da ket noi: {addr} (dang co {total} may)")

    def _remove_client(self, client, reason):
        with self.clients_lock:
            if client in self.clients:
                self.clients.remove(client)
            total = len(self.clients)
        print(f"[MASTER] Slave {client.addr} ngat ket noi ({reason}). Con {total} may.")

    # ------------------------------------------------------------------
    #   HOOK: chi doc su kien va day vao hang doi, tra ve NGAY LAP TUC.
    #   (Windows tu go hook neu callback xu ly qua lau.)
    # ------------------------------------------------------------------
    def hook_loop(self):
        raise_thread_priority()
        self.hook_tid = kernel32.GetCurrentThreadId()
        msg = wintypes.MSG()
        user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_NOREMOVE)  # tao hang doi message cho luong

        kb_cb = HOOKPROC(self._keyboard_proc)
        ms_cb = HOOKPROC(self._mouse_proc)
        self._hook_callbacks = [kb_cb, ms_cb]
        hmod = kernel32.GetModuleHandleW(None)
        kb_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, kb_cb, hmod, 0)
        ms_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, ms_cb, hmod, 0)
        if not kb_hook or not ms_hook:
            print(f"[MASTER] LOI: khong cai duoc hook (ma loi {ctypes.get_last_error()}).")
            for h in (kb_hook, ms_hook):
                if h:
                    user32.UnhookWindowsHookEx(h)
            self.hook_ready.set()
            return

        self.hook_ok = True
        print("[MASTER] Da cai hook ban phim + chuot (di chuot, click, cuon doc/ngang, nut phu).")
        self.hook_ready.set()
        try:
            # Vong lap message bat buoc de Windows goi duoc cac ham hook
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                pass
        finally:
            user32.UnhookWindowsHookEx(kb_hook)
            user32.UnhookWindowsHookEx(ms_hook)

    def _keyboard_proc(self, n_code, w_param, l_param):
        if n_code == HC_ACTION:
            try:
                k = KBDLLHOOKSTRUCT.from_address(l_param)
                vk = k.vkCode
                if vk != VK_SCROLL and vk != VK_PACKET:   # ScrLk dung de bat/tat dong bo, khong gui
                    self.events.put((EV_KEY, vk, k.scanCode, k.flags & LLKHF_EXTENDED,
                                     bool(k.flags & LLKHF_UP)))
            except Exception:
                pass
        return user32.CallNextHookEx(None, n_code, w_param, l_param)

    def _mouse_proc(self, n_code, w_param, l_param):
        if n_code == HC_ACTION:
            try:
                m = MSLLHOOKSTRUCT.from_address(l_param)
                if w_param == WM_MOUSEMOVE:
                    self.events.put((EV_MOVE, m.pt.x, m.pt.y))
                elif w_param == WM_MOUSEWHEEL or w_param == WM_MOUSEHWHEEL:
                    # delta nam o HIWORD cua mouseData, la so co dau (vd +120 / -120)
                    delta = ctypes.c_short((m.mouseData >> 16) & 0xFFFF).value
                    if delta:
                        self.events.put((EV_WHEEL, w_param == WM_MOUSEHWHEEL, delta))
                else:
                    btn = BUTTON_MESSAGES.get(w_param)
                    if btn is not None:
                        name, down = btn
                        if name == "X":
                            name = "X1" if ((m.mouseData >> 16) & 0xFFFF) == XBUTTON1 else "X2"
                        # Toa do click lay tu chinh su kien click -> luon dung cho
                        self.events.put((EV_BUTTON, name, down, m.pt.x, m.pt.y))
            except Exception:
                pass
        return user32.CallNextHookEx(None, n_code, w_param, l_param)

    # ------------------------------------------------------------------
    #   LUONG DIEU PHOI: gom su kien, loc theo ScrLk, ma hoa, gui di
    # ------------------------------------------------------------------
    def dispatch_loop(self):
        raise_thread_priority()
        stopping = False
        while not stopping:
            try:
                batch = [self.events.get(timeout=IDLE_POLL_INTERVAL)]
                while True:
                    try:
                        batch.append(self.events.get_nowait())
                    except queue.Empty:
                        break
            except queue.Empty:
                batch = []

            out = []
            sync = is_sync_enabled()
            if sync != self.sync_on:
                self._on_sync_changed(sync, out)

            stopping = self._process_batch(batch, out)

            now = time.monotonic()
            if stopping:
                self._release_all(out)
            else:
                if now - self.last_stuck_check >= STUCK_CHECK_INTERVAL:
                    self.last_stuck_check = now
                    self._release_stuck(out, now)
                if not batch and self.sync_on:
                    # Luc ranh: bat ca truong hop chuot bi phan mem/game dich chuyen (SetCursorPos)
                    self._emit_move(get_cursor_pos(), out)
                if not out and now - self.last_send_time >= HEARTBEAT_INTERVAL:
                    out.append("PING")
            if out:
                self._broadcast(out, now)
        self.dispatch_done.set()

    def _process_batch(self, batch, out) -> bool:
        sync = self.sync_on
        stopping = False
        for ev in batch:
            kind = ev[0]
            if kind == EV_MOVE:
                if sync:
                    self.pending_move = (ev[1], ev[2])   # chi giu vi tri moi nhat
            elif kind == EV_BUTTON:
                if self._handle_button(ev, sync, out):
                    self.pending_move = None   # lenh click da mang toa do moi hon cac MOVE truoc no
            elif kind == EV_KEY:
                self._flush_move(out)
                self._handle_key(ev, sync, out)
            elif kind == EV_WHEEL:
                if sync:
                    self._flush_move(out)      # cuon tai dung vi tri chuot
                    out.append(f"{'HWHEEL' if ev[1] else 'WHEEL'} {ev[2]}")
            elif kind == EV_STOP:
                stopping = True
        self._flush_move(out)
        return stopping

    def _handle_button(self, ev, sync, out) -> bool:
        _, name, down, x, y = ev
        if down:
            if not sync:
                return False
            self.buttons_down[name] = time.monotonic()
        elif self.buttons_down.pop(name, None) is None:
            return False   # nut nay duoc nhan luc chua bat dong bo -> khong gui UP
        x, y = self._clamp(x, y)
        self.last_sent_pos = (x, y)
        out.append(f"{'MDOWN' if down else 'MUP'} {name} {self._norm(x, y)}")
        return True

    def _handle_key(self, ev, sync, out):
        _, vk, scan, ext, up = ev
        if up:
            if self.keys_down.pop(vk, None) is None:
                return     # phim nay duoc nhan luc chua bat dong bo -> khong gui UP
        else:
            if not sync:
                return
            if vk not in self.keys_down:
                self.keys_down[vk] = (scan, ext, time.monotonic())
            # neu da co trong keys_down: day la phim tu lap (giu phim) -> van gui KEYDOWN
        out.append(f"{'KEYUP' if up else 'KEYDOWN'} {vk} {scan} {ext}")

    def _on_sync_changed(self, sync, out):
        first = self.sync_on is None
        self.sync_on = sync
        state = "BAT (ScrLk ON)" if sync else "TAT (ScrLk OFF)"
        print(f"[MASTER] >>> Dong bo chuot/ban phim: {state}")
        if sync:
            self.last_sent_pos = None
            self._emit_move(get_cursor_pos(), out)   # Slave nhay ngay toi vi tri hien tai
        else:
            self.pending_move = None
            if not first:
                self._release_all(out)

    def _release_all(self, out):
        """Nha moi phim/nut ma Slave dang giu theo lenh cua Master."""
        total = len(self.keys_down) + len(self.buttons_down)
        if not total:
            return
        print(f"[MASTER] Tu dong nha {total} phim/nut dang giu tren Slave.")
        pos = self.last_sent_pos or self._clamp(*get_cursor_pos())
        for name in self.buttons_down:
            out.append(f"MUP {name} {self._norm(*pos)}")
        for vk, (scan, ext, _) in self.keys_down.items():
            out.append(f"KEYUP {vk} {scan} {ext}")
        self.buttons_down.clear()
        self.keys_down.clear()

    def _release_stuck(self, out, now):
        """Phim/nut ma hook khong thay su kien nha (Ctrl+Alt+Del, Win+L, cua so
        Admin...) nhung thuc te da duoc nha -> tu gui lenh nha cho Slave."""
        if not self.keys_down and not self.buttons_down:
            return
        for vk, (scan, ext, t) in list(self.keys_down.items()):
            if now - t >= STUCK_MIN_AGE and not is_physically_down(vk):
                del self.keys_down[vk]
                out.append(f"KEYUP {vk} {scan} {ext}")
        swapped = user32.GetSystemMetrics(SM_SWAPBUTTON) != 0
        for name, t in list(self.buttons_down.items()):
            check = name
            if swapped and name in ("L", "R"):   # GetAsyncKeyState doc nut VAT LY
                check = "R" if name == "L" else "L"
            if now - t >= STUCK_MIN_AGE and not is_physically_down(MOUSE_BUTTONS[check][3]):
                del self.buttons_down[name]
                pos = self.last_sent_pos or self._clamp(*get_cursor_pos())
                out.append(f"MUP {name} {self._norm(*pos)}")

    def _flush_move(self, out):
        if self.pending_move is not None:
            self._emit_move(self.pending_move, out)
            self.pending_move = None

    def _emit_move(self, pos, out):
        x, y = self._clamp(*pos)
        if (x, y) != self.last_sent_pos:
            self.last_sent_pos = (x, y)
            out.append(f"MOVE {self._norm(x, y)}")

    def _clamp(self, x, y):
        # Toa do tu hook co the vuot ra ngoai man hinh mot chut khi dua chuot sat mep
        x = min(max(x, self.vx), self.vx + self.vw - 1)
        y = min(max(y, self.vy), self.vy + self.vh - 1)
        return x, y

    def _norm(self, x, y) -> str:
        # Lay TAM pixel (+0.5) de Slave cung do phan giai quy doi ve dung pixel cu
        return f"{(x + 0.5) / self.screen_w:.6f} {(y + 0.5) / self.screen_h:.6f}"

    def _broadcast(self, out, now):
        data = ("\n".join(out) + "\n").encode("ascii")
        with self.clients_lock:
            clients = list(self.clients)
        for c in clients:
            c.push(data)
        self.last_send_time = now


# ===================================================================
#                              SLAVE
# ===================================================================
class SlaveClient:
    def __init__(self):
        self.screen_w, self.screen_h = get_screen_size()
        self.keys_down = {}          # vk -> (scan, ext) dang bi giu tren may nay
        self.buttons_down = set()    # nut chuot dang bi giu tren may nay
        self.last_move_time = 0.0

    def start(self):
        raise_thread_priority()
        set_timer_resolution()
        try:
            while True:
                try:
                    self.connect_and_run()
                except OSError as e:
                    print(f"[SLAVE] Mat ket noi ({e}).")
                finally:
                    self.release_all()
                print("[SLAVE] Thu lai sau 2 giay...")
                time.sleep(2)
        except KeyboardInterrupt:
            self.release_all()
            print("[SLAVE] Da dong. Tam biet.")

    def connect_and_run(self):
        self.screen_w, self.screen_h = get_screen_size()
        sock = socket.create_connection((MASTER_IP, PORT), timeout=3)
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.settimeout(HEARTBEAT_TIMEOUT)
            print(f"[SLAVE] Da ket noi toi Master {MASTER_IP}:{PORT}. "
                  f"Do phan giai man hinh: {self.screen_w}x{self.screen_h}")
            buf = b""
            while True:
                try:
                    data = sock.recv(65536)
                except socket.timeout:
                    raise ConnectionResetError(
                        f"khong nhan duoc gi tu Master trong {HEARTBEAT_TIMEOUT:g} giay")
                if not data:
                    raise ConnectionResetError("Master da dong ket noi")
                buf += data
                if b"\n" in data:
                    lines = buf.split(b"\n")
                    buf = lines.pop()          # phan cuoi chua tron dong, de lan sau
                    self.handle_lines(lines)
        finally:
            sock.close()

    def handle_lines(self, lines):
        pending = None   # chuoi MOVE lien tiep chi can ap dung vi tri cuoi cung
        for raw in lines:
            parts = raw.split()
            if not parts:
                continue
            cmd = parts[0]
            try:
                if cmd == b"MOVE":
                    pending = self.to_pixels(parts[1], parts[2])
                    continue
                if cmd == b"MDOWN" or cmd == b"MUP":
                    pending = None   # lenh click tu mang toa do moi nhat
                    self.mouse_button(parts[1].decode("ascii"), cmd == b"MDOWN",
                                      self.to_pixels(parts[2], parts[3]))
                    continue
                if pending is not None:
                    self.move_to(pending)
                    pending = None
                if cmd == b"KEYDOWN" or cmd == b"KEYUP":
                    self.key(int(parts[1]), int(parts[2]), int(parts[3]), cmd == b"KEYDOWN")
                elif cmd == b"WHEEL":
                    send_inputs([mouse_input(MOUSEEVENTF_WHEEL, int(parts[1]))])
                elif cmd == b"HWHEEL":
                    send_inputs([mouse_input(MOUSEEVENTF_HWHEEL, int(parts[1]))])
                # PING: khong can lam gi
            except (IndexError, ValueError, UnicodeDecodeError):
                print(f"[SLAVE] Bo qua lenh khong hop le: {raw!r}")
        if pending is not None:
            self.move_to(pending)

    def to_pixels(self, rx, ry):
        return math.floor(float(rx) * self.screen_w), math.floor(float(ry) * self.screen_h)

    def move_to(self, pos):
        user32.SetCursorPos(pos[0], pos[1])
        self.last_move_time = time.perf_counter()

    def mouse_button(self, name, down, pos):
        spec = MOUSE_BUTTONS.get(name)
        if spec is None:
            return
        down_flag, up_flag, data, _ = spec
        if get_cursor_pos() != pos:
            self.move_to(pos)
        if down:
            # Chuot vua doi cho -> cho ung dung kip nhan vi tri moi roi moi click
            wait = CLICK_SETTLE_DELAY - (time.perf_counter() - self.last_move_time)
            if wait > 0:
                time.sleep(wait)
            self.buttons_down.add(name)
        else:
            self.buttons_down.discard(name)
        send_inputs([mouse_input(down_flag if down else up_flag, data)])

    def key(self, vk, scan, ext, down):
        if not scan:
            scan = user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)
        flags = KEYEVENTF_EXTENDEDKEY if ext else 0
        if down:
            self.keys_down[vk] = (scan, ext)
        else:
            self.keys_down.pop(vk, None)
            flags |= KEYEVENTF_KEYUP
        send_inputs([key_input(vk, scan, flags)])

    def release_all(self):
        """Nha moi phim/nut dang giu de tranh liet phim khi mat ket noi."""
        total = len(self.keys_down) + len(self.buttons_down)
        if not total:
            return
        print(f"[SLAVE] Tu dong nha {total} phim/nut dang giu de tranh liet phim.")
        inputs = [mouse_input(MOUSE_BUTTONS[n][1], MOUSE_BUTTONS[n][2]) for n in self.buttons_down]
        inputs += [key_input(vk, scan, (KEYEVENTF_EXTENDEDKEY if ext else 0) | KEYEVENTF_KEYUP)
                   for vk, (scan, ext) in self.keys_down.items()]
        self.buttons_down.clear()
        self.keys_down.clear()
        send_inputs(inputs)


# ===================================================================
#                               MAIN
# ===================================================================
if __name__ == "__main__":
    enable_dpi_awareness()
    disable_quick_edit()
    if ROLE == "MASTER":
        print(f"[MASTER] IP LAN cua may nay: {get_local_ip()}")
        MasterServer().start()
    else:
        SlaveClient().start()