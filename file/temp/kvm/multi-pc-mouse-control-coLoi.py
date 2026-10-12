# -*- coding: utf-8 -*-
"""
MiniKVM - 1 chuột + 1 bàn phím điều khiển nhiều PC Windows qua mạng LAN.
Nhẹ: không mã hóa, không cần cài thư viện (chỉ Python 3.8+ và Win32 API qua ctypes).

Copy CÙNG MỘT file này sang mọi máy rồi chạy:
    python kvm.py            -> tự nhận vai trò (IP có trong ipTable = client, còn lại = master)
    python kvm.py master     -> ép chạy master
    python kvm.py client     -> ép chạy client
Nên chạy bằng quyền Administrator (để điều khiển được cả cửa sổ đang chạy quyền admin).

Scroll Lock BẬT  = khóa chuột ở màn hình hiện tại (không chuyển máy)
Scroll Lock TẮT  = đưa chuột ra cạnh màn hình để chuyển sang máy bên cạnh
"""

# =============================== CẤU HÌNH ===============================
ipTable = [
    [None, "192.168.1.102", None],
    ["192.168.1.23", "MASTER", "192.168.1.106"],
    [None, "192.168.1.108", None],
]
PORT = 24900          # cổng TCP: client lắng nghe, master kết nối tới (mở firewall trên client)
MASTER_IP = None      # vd "192.168.1.10": client chỉ nhận kết nối từ máy này (None = nhận mọi máy)
MAX_CLIP_MB = 50      # giới hạn dung lượng clipboard mỗi lần chuyển (ảnh chụp màn hình...)
FILE_KEY = 0x13       # phím BẬT/TẮT copy file ở master: 0x13 = Pause/Break (muốn dùng F12 thì đặt 0x7B)
MAX_FILE_MB = 2048    # giới hạn tổng dung lượng mỗi lần copy file/thư mục
HIDE_MASTER_CURSOR = True   # ẩn con trỏ của master khi đang điều khiển máy khác
# ========================================================================

import ctypes
import itertools
import os
import queue
import shutil
import tempfile
import socket
import struct
import sys
import threading
import time
import traceback
from ctypes import wintypes as wt

# ----------------------------- Win32 qua ctypes -----------------------------
windll = getattr(ctypes, "windll", None)
WINFUNCTYPE = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)

DWORD, WORD, LONG, UINT = ctypes.c_uint32, ctypes.c_uint16, ctypes.c_int32, ctypes.c_uint32
BOOL, LRESULT, ULONG_PTR = ctypes.c_int, ctypes.c_ssize_t, ctypes.c_size_t
VOIDP = ctypes.c_void_p


class POINT(ctypes.Structure):
    _fields_ = [("x", LONG), ("y", LONG)]


class RECT(ctypes.Structure):
    _fields_ = [("left", LONG), ("top", LONG), ("right", LONG), ("bottom", LONG)]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("pt", POINT), ("mouseData", DWORD), ("flags", DWORD),
                ("time", DWORD), ("dwExtraInfo", ULONG_PTR)]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", DWORD), ("scanCode", DWORD), ("flags", DWORD),
                ("time", DWORD), ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", LONG), ("dy", LONG), ("mouseData", DWORD), ("dwFlags", DWORD),
                ("time", DWORD), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", WORD), ("wScan", WORD), ("dwFlags", DWORD),
                ("time", DWORD), ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", DWORD), ("wParamL", WORD), ("wParamH", WORD)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", DWORD), ("u", _INPUTUNION)]


HOOKPROC = WINFUNCTYPE(LRESULT, ctypes.c_int, wt.WPARAM, wt.LPARAM)
WNDPROC = WINFUNCTYPE(LRESULT, VOIDP, UINT, wt.WPARAM, wt.LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [("style", UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int), ("hInstance", VOIDP), ("hIcon", VOIDP), ("hCursor", VOIDP),
                ("hbrBackground", VOIDP), ("lpszMenuName", ctypes.c_wchar_p), ("lpszClassName", ctypes.c_wchar_p)]


MONITORENUMPROC = WINFUNCTYPE(BOOL, VOIDP, VOIDP, ctypes.POINTER(RECT), wt.LPARAM)

WH_KEYBOARD_LL, WH_MOUSE_LL, WM_QUIT = 13, 14, 0x0012
WM_MOUSEMOVE, WM_MOUSEWHEEL, WM_MOUSEHWHEEL = 0x0200, 0x020A, 0x020E
# message -> (nút, nhấn?)   1=trái 2=phải 3=giữa 4=X1 (5=X2)
BTN_MSG = {0x0201: (1, 1), 0x0202: (1, 0), 0x0204: (2, 1), 0x0205: (2, 0),
           0x0207: (3, 1), 0x0208: (3, 0), 0x020B: (4, 1), 0x020C: (4, 0)}
BTN_VK = {1: 0x01, 2: 0x02, 3: 0x04, 4: 0x05, 5: 0x06}
# nút -> (cờ nhấn, cờ nhả, mouseData) cho SendInput
BTN_FLAGS = {1: (0x0002, 0x0004, 0), 2: (0x0008, 0x0010, 0), 3: (0x0020, 0x0040, 0),
             4: (0x0080, 0x0100, 1), 5: (0x0080, 0x0100, 2)}
LLMHF_ANY_INJECTED = 0x01 | 0x02
LLKHF_EXTENDED, LLKHF_ANY_INJECTED, LLKHF_UP = 0x01, 0x10 | 0x02, 0x80
VK_SCROLL = 0x91
INPUT_MOUSE, INPUT_KEYBOARD = 0, 1
MOUSEEVENTF_MOVE, MOUSEEVENTF_WHEEL, MOUSEEVENTF_HWHEEL = 0x0001, 0x0800, 0x1000
KEYEVENTF_EXTENDEDKEY, KEYEVENTF_KEYUP = 0x0001, 0x0002
CF_DIB, CF_UNICODETEXT, CF_HDROP, GMEM_MOVEABLE = 8, 13, 15, 0x0002
KEY_NAME = {0x13: "Pause/Break", 0x7B: "F12", 0x91: "Scroll Lock"}.get(FILE_KEY, f"phím 0x{FILE_KEY:02X}")
HWND_MESSAGE, HWND_TOPMOST = VOIDP(-3), VOIDP(-1)
WM_SETCURSOR, HIDER = 0x0020, 16   # HIDER: cỡ cửa sổ che con trỏ (pixel)
INJECT_TAG = 0x4B564D  # "KVM"

user32 = kernel32 = None
if windll is not None:
    user32, kernel32 = windll.user32, windll.kernel32

    def _sig(fn, res, *args):
        fn.restype, fn.argtypes = res, list(args)

    _sig(user32.SetWindowsHookExW, VOIDP, ctypes.c_int, HOOKPROC, VOIDP, DWORD)
    _sig(user32.CallNextHookEx, LRESULT, VOIDP, ctypes.c_int, wt.WPARAM, wt.LPARAM)
    _sig(user32.UnhookWindowsHookEx, BOOL, VOIDP)
    _sig(user32.GetMessageW, BOOL, VOIDP, VOIDP, UINT, UINT)
    _sig(user32.PostThreadMessageW, BOOL, DWORD, UINT, wt.WPARAM, wt.LPARAM)
    _sig(user32.GetCursorPos, BOOL, ctypes.POINTER(POINT))
    _sig(user32.SetCursorPos, BOOL, ctypes.c_int, ctypes.c_int)
    _sig(user32.SendInput, UINT, UINT, ctypes.POINTER(INPUT), ctypes.c_int)
    _sig(user32.GetKeyState, ctypes.c_short, ctypes.c_int)
    _sig(user32.GetAsyncKeyState, ctypes.c_short, ctypes.c_int)
    _sig(user32.GetSystemMetrics, ctypes.c_int, ctypes.c_int)
    _sig(user32.EnumDisplayMonitors, BOOL, VOIDP, VOIDP, MONITORENUMPROC, wt.LPARAM)
    _sig(user32.OpenClipboard, BOOL, VOIDP)
    _sig(user32.CloseClipboard, BOOL)
    _sig(user32.EmptyClipboard, BOOL)
    _sig(user32.IsClipboardFormatAvailable, BOOL, UINT)
    _sig(user32.GetClipboardData, VOIDP, UINT)
    _sig(user32.SetClipboardData, VOIDP, UINT, VOIDP)
    _sig(user32.GetClipboardSequenceNumber, DWORD)
    _sig(user32.RegisterClipboardFormatW, UINT, ctypes.c_wchar_p)
    _sig(user32.CreateWindowExW, VOIDP, DWORD, ctypes.c_wchar_p, ctypes.c_wchar_p, DWORD,
         ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, VOIDP, VOIDP, VOIDP, VOIDP)
    _sig(user32.DestroyWindow, BOOL, VOIDP)
    _sig(user32.RegisterClassW, WORD, ctypes.POINTER(WNDCLASSW))
    _sig(user32.DefWindowProcW, LRESULT, VOIDP, UINT, wt.WPARAM, wt.LPARAM)
    _sig(user32.DispatchMessageW, LRESULT, VOIDP)
    _sig(user32.SetWindowPos, BOOL, VOIDP, VOIDP, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, UINT)
    _sig(user32.ShowWindowAsync, BOOL, VOIDP, ctypes.c_int)
    _sig(user32.SetLayeredWindowAttributes, BOOL, VOIDP, DWORD, ctypes.c_ubyte, DWORD)
    _sig(user32.CreateCursor, VOIDP, VOIDP, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, VOIDP, VOIDP)
    _sig(user32.SetCursor, VOIDP, VOIDP)
    _sig(user32.ShowCursor, ctypes.c_int, BOOL)
    _sig(kernel32.GlobalAlloc, VOIDP, UINT, ctypes.c_size_t)
    _sig(kernel32.GlobalLock, VOIDP, VOIDP)
    _sig(kernel32.GlobalUnlock, BOOL, VOIDP)
    _sig(kernel32.GlobalSize, ctypes.c_size_t, VOIDP)
    _sig(kernel32.GlobalFree, VOIDP, VOIDP)
    _sig(kernel32.GetModuleHandleW, VOIDP, ctypes.c_wchar_p)
    _sig(kernel32.GetCurrentThreadId, DWORD)
    _sig(kernel32.GetCurrentProcess, VOIDP)
    _sig(kernel32.SetPriorityClass, BOOL, VOIDP, DWORD)
    _sig(kernel32.GetStdHandle, VOIDP, DWORD)
    _sig(kernel32.GetConsoleMode, BOOL, VOIDP, ctypes.POINTER(DWORD))
    _sig(kernel32.SetConsoleMode, BOOL, VOIDP, DWORD)
    _sig(kernel32.SetConsoleTitleW, BOOL, ctypes.c_wchar_p)


def win_setup():
    """DPI-aware (tọa độ = pixel thật), ưu tiên CPU cao, tắt QuickEdit của console."""
    ok = 0
    try:
        user32.SetProcessDpiAwarenessContext.argtypes = [VOIDP]
        ok = user32.SetProcessDpiAwarenessContext(VOIDP(-4))  # PER_MONITOR_AWARE_V2
    except Exception:
        pass
    if not ok:
        try:
            windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                user32.SetProcessDPIAware()
            except Exception:
                pass
    try:  # HIGH_PRIORITY_CLASS: chuột không bị khựng khi máy đang bận
        kernel32.SetPriorityClass(kernel32.GetCurrentProcess(), 0x80)
    except Exception:
        pass
    try:  # QuickEdit: lỡ click vào cửa sổ console sẽ làm treo print -> tắt đi
        h, mode = kernel32.GetStdHandle(DWORD(-10).value), DWORD()
        if kernel32.GetConsoleMode(h, ctypes.byref(mode)):
            kernel32.SetConsoleMode(h, (mode.value & ~0x0040) | 0x0080)
    except Exception:
        pass
    sys.setswitchinterval(0.001)


def is_admin():
    try:
        return bool(windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def send_inputs(*items):
    n = len(items)
    user32.SendInput(n, (INPUT * n)(*items), ctypes.sizeof(INPUT))


def mouse_input(flags, data=0, dx=0, dy=0):
    i = INPUT(type=INPUT_MOUSE)
    i.u.mi = MOUSEINPUT(dx, dy, data & 0xFFFFFFFF, flags, 0, INJECT_TAG)
    return i


def key_input(vk, scan, flags):
    i = INPUT(type=INPUT_KEYBOARD)
    i.u.ki = KEYBDINPUT(vk, scan, flags, 0, INJECT_TAG)
    return i


def cursor_pos():
    p = POINT()
    user32.GetCursorPos(ctypes.byref(p))
    return p.x, p.y


# --------------------------------- Log ---------------------------------
# Mọi print đi qua 1 thread riêng: hook chuột/phím không bao giờ bị chặn vì console.
_logq = queue.SimpleQueue()


def log(msg):
    _logq.put(time.strftime("[%H:%M:%S] ") + msg)


def set_title(text):
    _logq.put((text,))


def _log_loop():
    while True:
        m = _logq.get()
        try:
            if isinstance(m, tuple):
                if kernel32 is not None:
                    kernel32.SetConsoleTitleW(m[0])
            else:
                print(m, flush=True)
        except Exception:
            pass


def start_logger():
    threading.Thread(target=_log_loop, name="log", daemon=True).start()


def size_str(n):
    return f"{n} B" if n < 1024 else (f"{n / 1024:.1f} KB" if n < 1 << 20 else f"{n / 1048576:.1f} MB")


# ------------------------------ Màn hình ------------------------------
LEFT, RIGHT, UP, DOWN = 0, 1, 2, 3
DIR_NAME = ("TRÁI", "PHẢI", "TRÊN", "DƯỚI")
OPP = (RIGHT, LEFT, DOWN, UP)
STEP = ((0, -1), (0, 1), (-1, 0), (1, 0))  # (dòng, cột) trong ipTable


class Screen:
    """Danh sách màn hình (hỗ trợ nhiều màn hình), tìm cạnh để chuyển máy."""

    def __init__(self):
        self.refresh()

    def refresh(self):
        rects = []

        def cb(hmon, hdc, prc, lp):
            r = prc.contents
            rects.append((r.left, r.top, r.right, r.bottom))
            return 1

        try:
            user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(cb), 0)
        except Exception:
            pass
        w, h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        if not rects:
            rects = [(0, 0, w, h)]
        self.park = (w // 2, h // 2)  # giữa màn hình chính: chỗ "đỗ" con trỏ master
        self.geo = (tuple(rects), min(r[0] for r in rects), min(r[1] for r in rects),
                    max(r[2] for r in rects), max(r[3] for r in rects))

    def contains(self, x, y):
        for l, t, r, b in self.geo[0]:
            if l <= x < r and t <= y < b:
                return True
        return False

    def edges_at(self, x, y):
        """Con trỏ (x,y) đang nằm sát những cạnh nào (phía bên kia không còn màn hình)."""
        for l, t, r, b in self.geo[0]:
            if l < x < r - 1 and t < y < b - 1:
                return ()
        c = self.contains
        return [d for d, ok in ((LEFT, c(x - 1, y)), (RIGHT, c(x + 1, y)),
                                (UP, c(x, y - 1)), (DOWN, c(x, y + 1))) if not ok]

    def exit_dirs(self, x, y, nx, ny):
        """Con trỏ ở (x,y) bị đẩy tới (nx,ny) nằm ngoài màn hình -> các hướng thoát."""
        c = self.contains
        out = []
        if nx < x and not c(nx, y):
            out.append(LEFT)
        if nx > x and not c(nx, y):
            out.append(RIGHT)
        if ny < y and not c(x, ny):
            out.append(UP)
        if ny > y and not c(x, ny):
            out.append(DOWN)
        if abs(ny - y) > abs(nx - x):
            out.sort(key=lambda d: d < UP)  # đẩy dọc nhiều hơn -> ưu tiên trên/dưới
        return out

    def frac(self, d, x, y):
        """Vị trí tương đối (0..1) dọc theo cạnh, để sang máy kia con trỏ ở đúng tầm."""
        _, vx, vy, vr, vb = self.geo
        if d in (LEFT, RIGHT):
            return (y - vy) / max(1, vb - vy - 1)
        return (x - vx) / max(1, vr - vx - 1)

    def entry(self, side, f):
        """Điểm xuất hiện khi con trỏ đi vào từ cạnh `side`."""
        _, vx, vy, vr, vb = self.geo
        f = min(max(f, 0.0), 1.0)
        x, y = vx + round(f * (vr - vx - 1)), vy + round(f * (vb - vy - 1))
        if side == LEFT:
            x = vx + 1
        elif side == RIGHT:
            x = vr - 2
        elif side == UP:
            y = vy + 1
        else:
            y = vb - 2
        return x, y


# ------------------------------ Clipboard ------------------------------
CLIP_FORMATS = (("text", CF_UNICODETEXT), ("html", "HTML Format"),
                ("rtf", "Rich Text Format"), ("image", CF_DIB))
MAX_CLIP = MAX_CLIP_MB * 1024 * 1024


def pack_clip(items):
    out = bytearray()
    for name, data in items:
        nb = name.encode()
        out += struct.pack("<B", len(nb)) + nb + struct.pack("<I", len(data)) + data
    return bytes(out)


def unpack_clip(blob):
    items, pos = [], 0
    while pos < len(blob):
        n = blob[pos]
        name = blob[pos + 1:pos + 1 + n].decode()
        (size,) = struct.unpack_from("<I", blob, pos + 1 + n)
        pos += 5 + n
        items.append((name, blob[pos:pos + size]))
        pos += size
    return items


def pack_hdrop(paths):
    """CF_HDROP = DROPFILES (20 byte, fWide=1) + các đường dẫn UTF-16, kết thúc bằng 2 số 0."""
    return struct.pack("<IiiII", 20, 0, 0, 0, 1) + ("".join(p + "\0" for p in paths) + "\0").encode("utf-16-le")


def parse_hdrop(raw):
    try:
        off, _, _, _, wide = struct.unpack_from("<IiiII", raw, 0)
        if wide:
            text = raw[off:].decode("utf-16-le", "ignore")
        else:
            try:
                text = raw[off:].decode("mbcs")
            except LookupError:
                text = raw[off:].decode("latin-1")
    except (struct.error, UnicodeDecodeError):
        return []
    return [p for p in text.split("\0\0", 1)[0].split("\0") if p]


def data_desc(data):
    return f"{len(data[1])} file/thư mục" if data[0] == "files" else clip_desc(data[1])


def clip_desc(blob):
    try:
        kinds = [n for n, _ in unpack_clip(blob)]
    except Exception:
        kinds = ["?"]
    return f"{'+'.join(kinds)}, {size_str(len(blob))}"


class Clipboard:
    """Đọc/ghi clipboard Windows: chữ, HTML, RTF, ảnh. Chỉ chạy trong 1 thread (Worker)."""

    def __init__(self):
        self.ids = {n: (f if isinstance(f, int) else user32.RegisterClipboardFormatW(f))
                    for n, f in CLIP_FORMATS}
        self.ids["drop"] = user32.RegisterClipboardFormatW("Preferred DropEffect")
        self.seq = user32.GetClipboardSequenceNumber()  # chỉ đồng bộ những gì copy SAU khi chạy

    def changed(self):
        return user32.GetClipboardSequenceNumber() != self.seq

    def _open(self):
        hwnd = user32.CreateWindowExW(0, "STATIC", None, 0, 0, 0, 0, 0, HWND_MESSAGE, None, None, None)
        for _ in range(25):
            if user32.OpenClipboard(hwnd):
                return True, hwnd
            time.sleep(0.02)
        if hwnd:
            user32.DestroyWindow(hwnd)
        return False, None

    def _close(self, hwnd):
        user32.CloseClipboard()
        if hwnd:
            user32.DestroyWindow(hwnd)
        self.seq = user32.GetClipboardSequenceNumber()

    def _get(self, fid, limit):
        h = user32.GetClipboardData(fid)
        p = kernel32.GlobalLock(h) if h else None
        if not p:
            return None
        try:
            size = kernel32.GlobalSize(h)
            return ctypes.string_at(p, size) if size <= limit else None
        finally:
            kernel32.GlobalUnlock(h)

    def read(self, files=False):
        """-> ("files", [đường dẫn]) | ("blob", bytes) | None"""
        ok, hwnd = self._open()
        if not ok:
            return None
        items, total, paths = [], 0, None
        try:
            if user32.IsClipboardFormatAvailable(CF_HDROP):
                raw = self._get(CF_HDROP, MAX_CLIP)
                paths = parse_hdrop(raw) if raw else None
            if not (paths and files):
                for name, _ in CLIP_FORMATS:
                    fid = self.ids[name]
                    if not fid or not user32.IsClipboardFormatAvailable(fid):
                        continue
                    data = self._get(fid, MAX_CLIP - total)
                    if data is None:
                        continue
                    if name == "text":
                        data = (data.decode("utf-16-le", "ignore").split("\0", 1)[0] + "\0").encode("utf-16-le")
                    total += len(data)
                    items.append((name, data))
        finally:
            self._close(hwnd)
        if paths and files:
            return ("files", paths)
        if paths and not items:
            log(f"[COPY FILE] đang TẮT nên không chuyển file (bấm {KEY_NAME} ở master để bật)")
        return ("blob", pack_clip(items)) if items else None

    def write(self, blob):
        self._set([(self.ids.get(n), d) for n, d in unpack_clip(blob)])

    def write_files(self, paths):   # dán trong Explorer = copy (DropEffect 1), không bao giờ "cắt"
        self._set([(CF_HDROP, pack_hdrop(paths)), (self.ids["drop"], struct.pack("<I", 1))])

    def _set(self, items):
        ok, hwnd = self._open()
        if not ok:
            log("[CLIPBOARD] Không mở được clipboard (ứng dụng khác đang giữ)")
            return
        try:
            user32.EmptyClipboard()
            for fid, data in items:
                h = kernel32.GlobalAlloc(GMEM_MOVEABLE, max(1, len(data))) if fid else None
                if not h:
                    continue
                p = kernel32.GlobalLock(h)
                ctypes.memmove(p, data, len(data))
                kernel32.GlobalUnlock(h)
                if not user32.SetClipboardData(fid, h):
                    kernel32.GlobalFree(h)
        finally:
            self._close(hwnd)

class Worker:
    """1 thread làm việc chậm (clipboard) để không bao giờ làm khựng chuột."""

    def __init__(self):
        self.q = queue.SimpleQueue()
        threading.Thread(target=self._run, name="worker", daemon=True).start()

    def submit(self, fn, *args):
        self.q.put((fn, args))

    def _run(self):
        while True:
            fn, args = self.q.get()
            try:
                fn(*args)
            except Exception:
                log("[LỖI] " + traceback.format_exc())


# ------------------------------ Giao thức ------------------------------
# Mỗi gói: [kiểu 1 byte][độ dài 4 byte][nội dung]. TCP_NODELAY để không bị trễ.
(T_WAKE, T_MOVE, T_BTN, T_WHEEL, T_KEY, T_ENTER, T_LEAVE, T_PING, T_PONG, T_EDGE, T_CLIP,
 T_OPT, T_FBEGIN, T_FENTRY, T_FDATA, T_FEND, T_FABORT, T_FILES) = range(18)
FILE_T = (T_FBEGIN, T_FENTRY, T_FDATA, T_FEND, T_FABORT)
HDR = struct.Struct("<BI")
FMT = {T_MOVE: struct.Struct("<ii"), T_BTN: struct.Struct("<BB"), T_WHEEL: struct.Struct("<hB"),
       T_KEY: struct.Struct("<HHB"), T_ENTER: struct.Struct("<Bf"), T_EDGE: struct.Struct("<Bf"),
       T_OPT: struct.Struct("<B")}
CHUNK = 64 * 1024     # clipboard lớn được cắt nhỏ, chen giữa các sự kiện chuột
TIMEOUT = 5.0         # không nhận được gì trong 5s -> coi như mất kết nối
PING_EVERY = 1.0      # master ping mỗi 1s (kể cả khi đang di chuột), client trả lời PONG


def encode(item):
    s = FMT.get(item[0])
    body = s.pack(*item[1:]) if s else b""
    return HDR.pack(item[0], len(body)) + body


PING_BYTES = encode((T_PING,))


class Link:
    """1 kết nối TCP: thread gửi (gộp các bước di chuột) + thread nhận."""

    def __init__(self, sock, name, on_msg, on_close, ping=False):
        self.sock, self.name, self.on_msg, self.on_close, self.ping = sock, name, on_msg, on_close, ping
        self.q = queue.SimpleQueue()
        self.stream, self.ftid = None, None   # luồng gửi chậm (clipboard/file), chen giữa sự kiện chuột
        self.recv = FileRecv()
        self.alive = True
        self._lock = threading.Lock()
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.settimeout(TIMEOUT)

    def start(self):
        threading.Thread(target=self._reader, name="rx-" + self.name, daemon=True).start()
        threading.Thread(target=self._writer, name="tx-" + self.name, daemon=True).start()
        return self

    def send(self, item):
        if self.alive:
            self.q.put(item)

    def send_clip(self, blob):
        n = max(1, (len(blob) + CHUNK - 1) // CHUNK)
        self._stream(iter([frame(T_CLIP, bytes([(1 if i == 0 else 0) | (2 if i == n - 1 else 0)])
                                 + blob[i * CHUNK:(i + 1) * CHUNK]) for i in range(n)]))

    def send_files(self, entries, total):
        tid = next(_tids)
        self._stream(file_frames(tid, entries, total), tid)

    def cancel_files(self):
        if self.ftid is not None:
            self._stream(iter([frame(T_FABORT, struct.pack("<I", self.ftid))]))

    def _stream(self, it, ftid=None):
        self.stream, self.ftid = it, ftid   # thay luôn luồng cũ nếu đang gửi dở
        self.send((T_WAKE,))

    def close(self):
        with self._lock:
            if not self.alive:
                return
            self.alive = False
        for fn in (lambda: self.sock.shutdown(socket.SHUT_RDWR), self.sock.close):
            try:
                fn()
            except OSError:
                pass
        self.q.put((T_WAKE,))
        try:
            self.on_close(self)
        except Exception:
            log("[LỖI] " + traceback.format_exc())

    def _writer(self):
        q, next_ping = self.q, 0.0
        try:
            while self.alive:
                try:
                    item = q.get_nowait() if self.stream is not None else q.get(timeout=PING_EVERY)
                except queue.Empty:
                    item = None
                buf, mx, my, mv, n = bytearray(), 0, 0, False, 0
                while item is not None:
                    t = item[0]
                    if t == T_MOVE:          # gộp nhiều bước di chuột thành 1 gói
                        mx += item[1]
                        my += item[2]
                        mv = True
                    elif t != T_WAKE:
                        if mv:
                            buf += encode((T_MOVE, mx, my))
                            mx = my = 0
                            mv = False
                        buf += encode(item)
                    n += 1
                    if n >= 500:
                        break
                    try:
                        item = q.get_nowait()
                    except queue.Empty:
                        item = None
                if mv:
                    buf += encode((T_MOVE, mx, my))
                st = self.stream
                if st is not None and q.empty():
                    try:
                        buf += next(st)
                    except StopIteration:
                        if self.stream is st:
                            self.stream, self.ftid = None, None
                    except Exception:
                        log("[LỖI gửi] " + traceback.format_exc())
                        self.stream, self.ftid = None, None
                if self.ping:   # ping theo đồng hồ, KHÔNG chờ rảnh (lỗi cũ: di chuột liên tục 5s -> mất kết nối)
                    now = time.monotonic()
                    if now >= next_ping:
                        buf += PING_BYTES
                        next_ping = now + PING_EVERY
                if buf and self.alive:
                    self.sock.sendall(buf)
        except OSError:
            pass
        finally:
            self.close()

    def _reader(self):
        buf, clip = bytearray(), None
        try:
            while self.alive:
                data = self.sock.recv(1 << 18)
                if not data:
                    break
                buf += data
                pos, end_all = 0, len(buf)
                while end_all - pos >= 5:
                    t, n = HDR.unpack_from(buf, pos)
                    if n > CHUNK + 4096:
                        raise ValueError("gói tin hỏng")
                    end = pos + 5 + n
                    if end > end_all:
                        break
                    body = bytes(buf[pos + 5:end])
                    pos = end
                    if t == T_CLIP:
                        flags = body[0] if body else 0
                        if flags & 1:
                            clip = bytearray()
                            self.recv.abort()   # có clipboard mới -> bỏ file đang nhận dở
                        if clip is not None:
                            clip += body[1:]
                            if len(clip) > MAX_CLIP:
                                clip = None
                            elif flags & 2:
                                blob, clip = bytes(clip), None
                                self._dispatch(T_CLIP, blob)
                    elif t in FILE_T:
                        paths = self.recv.handle(t, body)
                        if paths:
                            self._dispatch(T_FILES, paths)
                    else:
                        s = FMT.get(t)
                        self._dispatch(t, s.unpack(body) if s else ())
                if pos:
                    del buf[:pos]
        except (OSError, ValueError, struct.error):
            pass
        finally:
            self.recv.abort()
            self.close()

    def _dispatch(self, t, args):
        try:
            self.on_msg(self, t, args)
        except Exception:
            log("[LỖI] " + traceback.format_exc())


# ------------------------------ Copy file ------------------------------
TEMP_DIR = os.path.join(tempfile.gettempdir(), "MiniKVM")   # file nhận được nằm ở đây
MAX_FILE = MAX_FILE_MB * 1024 * 1024
_tids = itertools.count(int(time.time()) & 0xFFFF)


def frame(t, body):
    return HDR.pack(t, len(body)) + body


def scan_files(paths):
    """-> [(đường dẫn thật, tên tương đối, cỡ, là thư mục)], tổng dung lượng"""
    out = []
    for p in paths:
        p = os.path.abspath(p)
        base = os.path.dirname(p.rstrip("\\/")) or p
        try:
            if os.path.isdir(p):
                for root, _dirs, files in os.walk(p):
                    out.append((root, os.path.relpath(root, base), 0, True))
                    for fn in files:
                        fp = os.path.join(root, fn)
                        out.append((fp, os.path.relpath(fp, base), os.path.getsize(fp), False))
            elif os.path.isfile(p):
                out.append((p, os.path.basename(p), os.path.getsize(p), False))
        except OSError as e:
            log(f"[COPY FILE] Bỏ qua {p}: {e}")
    return out, sum(e[2] for e in out)


def file_frames(tid, entries, total):
    """Đọc file dần từng đoạn ngay lúc gửi -> file to mấy cũng không tốn RAM."""
    yield frame(T_FBEGIN, struct.pack("<IIQ", tid, len(entries), total))
    for path, rel, size, isdir in entries:
        yield frame(T_FENTRY, struct.pack("<IQB", tid, size, isdir) + rel.replace("\\", "/").encode())
        if isdir or not size:
            continue
        try:
            with open(path, "rb") as f:
                left = size
                while left > 0:
                    data = f.read(min(CHUNK - 8, left))
                    if not data:
                        break
                    left -= len(data)
                    yield frame(T_FDATA, struct.pack("<I", tid) + data)
        except OSError as e:
            log(f"[COPY FILE] Không đọc được {path}: {e}")
    yield frame(T_FEND, struct.pack("<I", tid))


def cleanup_temp(keep=2):
    """Xóa các lần nhận cũ trong thư mục tạm, giữ lại `keep` lần mới nhất."""
    try:
        names = sorted(os.listdir(TEMP_DIR))
    except OSError:
        return
    for n in names[:max(0, len(names) - keep)]:
        shutil.rmtree(os.path.join(TEMP_DIR, n), ignore_errors=True)


def _safe_parts(rel):
    parts = rel.split("/")
    if any(x in ("", ".", "..") or ":" in x or "\\" in x for x in parts):
        return None   # chặn tên kiểu ../../Windows hoặc C:\... (ghi ra ngoài thư mục tạm)
    return parts


class FileRecv:
    """Nhận file vào thư mục tạm (mỗi lần nhận 1 thư mục con riêng)."""

    def __init__(self):
        self.tid, self.f, self.dir = None, None, None

    def handle(self, t, body):
        (tid,) = struct.unpack_from("<I", body)
        if t == T_FBEGIN:
            self.abort()
            _, count, self.total = struct.unpack_from("<IIQ", body)
            self.dir = os.path.join(TEMP_DIR, f"{int(time.time() * 1000)}-{tid}")
            self.tid, self.top, self.t0 = tid, [], time.monotonic()
            try:
                os.makedirs(self.dir, exist_ok=True)
            except OSError as e:
                log(f"[COPY FILE] Không tạo được thư mục tạm: {e}")
                self.tid = None
                return None
            log(f"[COPY FILE] Đang nhận {count} mục ({size_str(self.total)})...")
            return None
        if tid != self.tid:
            return None
        try:
            if t == T_FDATA:
                if self.f:
                    self.f.write(memoryview(body)[4:])
            elif t == T_FENTRY:
                self._close_file()
                size, isdir = struct.unpack_from("<QB", body, 4)
                parts = _safe_parts(body[13:].decode("utf-8", "replace"))
                if parts is None:
                    raise ValueError("tên file không hợp lệ")
                path = os.path.join(self.dir, *parts)
                if parts[0] not in self.top:
                    self.top.append(parts[0])
                if isdir:
                    os.makedirs(path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    self.f = open(path, "wb")
            elif t == T_FEND:
                self._close_file()
                paths = [os.path.join(self.dir, n) for n in self.top]
                log(f"[COPY FILE] Nhận xong {size_str(self.total)} trong {time.monotonic() - self.t0:.1f}s")
                self.tid = None
                cleanup_temp()
                return paths
            elif t == T_FABORT:
                log("[COPY FILE] Bên gửi đã hủy")
                self.abort()
        except (OSError, ValueError) as e:
            log(f"[COPY FILE] Lỗi khi nhận: {e} -> hủy")
            self.abort()
        return None

    def _close_file(self):
        if self.f:
            try:
                self.f.close()
            except OSError:
                pass
            self.f = None

    def abort(self):
        self._close_file()
        if self.tid is not None:
            self.tid = None
            shutil.rmtree(self.dir, ignore_errors=True)


# =============================== MASTER ===============================
class Peer:
    def __init__(self, ip, cell, label):
        self.ip, self.cell, self.label = ip, cell, label
        self.link = None
        self.clip_ver = 0
        self.warn_t = 0.0


class Master:
    def __init__(self, table=None):
        self.table = table if table is not None else ipTable
        self.home, self.peers = None, {}
        for r, row in enumerate(self.table):
            for c, v in enumerate(row):
                if v == "MASTER":
                    self.home = (r, c)
        if self.home is None:
            raise SystemExit("ipTable phải có đúng 1 ô 'MASTER'")
        for r, row in enumerate(self.table):
            for c, v in enumerate(row):
                if v and v != "MASTER":
                    d = [i for i, s in enumerate(STEP) if (self.home[0] + s[0], self.home[1] + s[1]) == (r, c)]
                    self.peers[v] = Peer(v, (r, c), DIR_NAME[d[0]] if d else f"ô[{r}][{c}]")
        self.cell, self.active = self.home, None       # active = None nghĩa là đang ở MASTER
        self.lock = threading.RLock()
        self.screen = Screen()
        self.scroll = bool(user32.GetKeyState(VK_SCROLL) & 1)
        self.scroll_held = False
        self.buttons, self.local_down = set(), set()
        self.px, self.py = cursor_pos()
        self.clip, self.worker = Clipboard(), Worker()
        self.clip_data, self.clip_ver = None, 0       # ("blob", bytes) | ("files", [đường dẫn])
        self.file_mode, self.file_held = False, False  # copy file: mặc định TẮT
        cleanup_temp(0)
        self.running, self.hook_tid = True, 0
        self._hider = self._blank = None

    # ---------- chuyển máy ----------
    def neighbor(self, cell, d):
        r, c = cell[0] + STEP[d][0], cell[1] + STEP[d][1]
        if 0 <= r < len(self.table) and 0 <= c < len(self.table[r]):
            return self.table[r][c]
        return None

    def try_switch(self, d, frac, src=None):
        """Chuyển sang máy ở hướng d. src = máy client báo chạm cạnh (None = master)."""
        with self.lock:
            if self.scroll or self.buttons or src is not self.active:
                return False
            name = self.neighbor(self.cell, d)
            if not name:
                return False
            target = None
            if name != "MASTER":
                target = self.peers.get(name)
                if target is None or target.link is None:
                    now = time.monotonic()
                    if target is not None and now - target.warn_t > 3:
                        target.warn_t = now
                        log(f"[!] {name} chưa kết nối - không chuyển sang được")
                    return False
            self._switch(target, OPP[d], frac)
            return True

    def _switch(self, target, side, frac):
        old = self.active
        if old is not None and old.link:
            old.link.send((T_LEAVE,))
        self.active = target
        if target is None:
            self.cell = self.home
            x, y = self.screen.entry(side, frac)
            self._show_cursor()
            user32.SetCursorPos(x, y)
            self.px, self.py = x, y
            log("<< Về MASTER")
        else:
            self.cell = target.cell
            target.link.send((T_ENTER, side, frac))
            if old is None:  # rời master: đỗ + ẩn con trỏ giữa màn hình, lấy clipboard master nếu mới copy
                self._hide_cursor()
                self.worker.submit(self._grab_local_clip)
            self.worker.submit(self._push_clip, target)
            log(f">> Điều khiển {target.ip} ({target.label})")
        self._title()

    # ---------- ẩn con trỏ master (cách Deskflow làm) ----------
    def _make_hider(self):
        """Cửa sổ 16x16 gần như trong suốt, nằm ngay dưới chỗ đỗ con trỏ, dùng con trỏ rỗng.
        Con trỏ nằm trên cửa sổ này -> không thấy. Thoát chương trình là cửa sổ mất -> chuột hiện lại."""
        hinst = kernel32.GetModuleHandleW(None)
        self._blank = user32.CreateCursor(hinst, 0, 0, 32, 32, (ctypes.c_ubyte * 128)(*([0xFF] * 128)),
                                          (ctypes.c_ubyte * 128)())

        def wndproc(hwnd, msg, wp, lp):
            if msg == WM_SETCURSOR:
                user32.SetCursor(self._blank)
                return 1
            return user32.DefWindowProcW(hwnd, msg, wp, lp)

        self._wndproc = WNDPROC(wndproc)
        wc = WNDCLASSW(lpfnWndProc=self._wndproc, hInstance=hinst, hCursor=self._blank,
                       lpszClassName="MiniKVMHide")
        user32.RegisterClassW(ctypes.byref(wc))
        # TOPMOST | TOOLWINDOW (không hiện ở Alt+Tab) | LAYERED | NOACTIVATE (không cướp focus), kiểu POPUP
        self._hider = user32.CreateWindowExW(0x08080088, "MiniKVMHide", None, 0x80000000,
                                             0, 0, HIDER, HIDER, None, None, hinst, None)
        if self._hider:
            user32.SetLayeredWindowAttributes(self._hider, 0, 1, 2)   # độ đậm 1/255: mắt không thấy
            user32.ShowCursor(False)
        else:
            log("[!] Không tạo được cửa sổ ẩn chuột - chuột master sẽ hiện giữa màn hình")

    def _hide_cursor(self):
        x, y = self.screen.park
        if self._hider:   # hiện cửa sổ che TRƯỚC, rồi mới đưa con trỏ vào -> Windows đổi sang con trỏ rỗng
            user32.SetWindowPos(self._hider, HWND_TOPMOST, x - HIDER // 2, y - HIDER // 2, HIDER, HIDER,
                                0x0010 | 0x0040 | 0x4000)   # NOACTIVATE | SHOWWINDOW | ASYNC
        user32.SetCursorPos(x, y)

    def _show_cursor(self):
        if self._hider:
            user32.ShowWindowAsync(self._hider, 0)   # SW_HIDE, không chặn thread nào

    def _title(self):
        where = self.active.ip if self.active else "MASTER"
        set_title(f"MiniKVM MASTER | Scroll Lock: {'BẬT (khóa)' if self.scroll else 'TẮT'} | "
                  f"Copy file: {'BẬT' if self.file_mode else 'TẮT'} | Đang ở: {where}")

    def _log_scroll(self):
        if self.scroll:
            where = self.active.ip if self.active else "MASTER"
            log(f"[SCROLL LOCK] BẬT  -> khóa chuột tại {where}, KHÔNG chuyển máy")
        else:
            log("[SCROLL LOCK] TẮT  -> có thể di chuyển chuột qua các PC")
        self._title()

    def set_file_mode(self, on):
        self.file_mode = on
        self._log_file()
        for p in list(self.peers.values()):
            link = p.link
            if link:
                link.send((T_OPT, on))
                if not on:
                    link.cancel_files()   # tắt giữa chừng -> hủy luôn file đang gửi
        self._title()

    def _log_file(self):
        if self.file_mode:
            log(f"[COPY FILE] BẬT  -> Ctrl+C file/thư mục ở 1 máy, sang máy khác Ctrl+V (bấm {KEY_NAME} để tắt)")
        else:
            log(f"[COPY FILE] TẮT  -> chỉ copy chữ/ảnh (bấm {KEY_NAME} để bật copy file)")

    # ---------- hook chuột ----------
    def _mouse_proc(self, code, wp, lp):
        if code == 0:
            try:
                if self._on_mouse(wp, MSLLHOOKSTRUCT.from_address(lp)):
                    return 1   # nuốt sự kiện (đang điều khiển máy khác)
            except Exception:
                log("[LỖI hook chuột] " + traceback.format_exc())
        return user32.CallNextHookEx(None, code, wp, lp)

    def _on_mouse(self, msg, m):
        if m.flags & LLMHF_ANY_INJECTED:
            return False
        act = self.active
        link = act.link if act is not None else None
        if msg == WM_MOUSEMOVE:
            x, y = m.pt.x, m.pt.y
            if act is None:
                if not self.scroll:
                    if self.buttons:  # bỏ nút "kẹt" (lỡ mất sự kiện nhả)
                        self.buttons = {b for b in self.buttons if user32.GetAsyncKeyState(BTN_VK[b]) & 0x8000}
                    dirs = () if self.buttons else self.screen.edges_at(x, y)
                    if len(dirs) > 1 and abs(y - self.py) > abs(x - self.px):
                        dirs = sorted(dirs, key=lambda d: d < UP)
                    for d in dirs:
                        if self.try_switch(d, self.screen.frac(d, x, y)):
                            return True
                self.px, self.py = x, y
                return False
            cx, cy = cursor_pos()           # con trỏ master đứng yên -> độ lệch = bước di chuột
            if link and (x != cx or y != cy):
                link.send((T_MOVE, x - cx, y - cy))
            return True
        if msg in BTN_MSG:
            b, down = BTN_MSG[msg]
            if b == 4 and (m.mouseData >> 16) == 2:
                b = 5
            if down:
                self.buttons.add(b)
            else:
                self.buttons.discard(b)
            if act is None:
                return False
            if link:
                link.send((T_BTN, b, down))
            return True
        if msg in (WM_MOUSEWHEEL, WM_MOUSEHWHEEL):
            if act is None:
                return False
            delta = (m.mouseData >> 16) & 0xFFFF
            if link:
                link.send((T_WHEEL, delta - 0x10000 if delta >= 0x8000 else delta, msg == WM_MOUSEHWHEEL))
            return True
        return act is not None

    # ---------- hook bàn phím ----------
    def _kbd_proc(self, code, wp, lp):
        if code == 0:
            try:
                if self._on_key(KBDLLHOOKSTRUCT.from_address(lp)):
                    return 1
            except Exception:
                log("[LỖI hook phím] " + traceback.format_exc())
        return user32.CallNextHookEx(None, code, wp, lp)

    def _on_key(self, k):
        if k.flags & LLKHF_ANY_INJECTED:
            return False
        vk, up = k.vkCode, bool(k.flags & LLKHF_UP)
        if vk == FILE_KEY:    # phím bật/tắt copy file: nuốt luôn, không gửi cho ứng dụng/máy nào
            if not up and not self.file_held:
                self.set_file_mode(not self.file_mode)
            self.file_held = not up
            return True
        if vk == VK_SCROLL:   # luôn để Windows xử lý để đèn Scroll Lock đổi theo
            if not up and not self.scroll_held:
                self.scroll = not self.scroll
                self._log_scroll()
            self.scroll_held = not up
            return False
        act = self.active
        if act is None:
            if up:
                self.local_down.discard(vk)
            else:
                self.local_down.add(vk)
            return False
        if up and vk in self.local_down:   # phím nhấn lúc còn ở master -> nhả ở master, tránh kẹt phím
            self.local_down.discard(vk)
            return False
        link = act.link
        if link:
            link.send((T_KEY, vk, k.scanCode & 0xFFFF,
                       (1 if up else 0) | (2 if k.flags & LLKHF_EXTENDED else 0)))
        return True

    def _hook_loop(self):
        self.hook_tid = kernel32.GetCurrentThreadId()
        if HIDE_MASTER_CURSOR:
            self._make_hider()   # cửa sổ phải thuộc thread có vòng lặp message (thread này)
        self._mproc, self._kproc = HOOKPROC(self._mouse_proc), HOOKPROC(self._kbd_proc)
        hmod = kernel32.GetModuleHandleW(None)
        hm = user32.SetWindowsHookExW(WH_MOUSE_LL, self._mproc, hmod, 0)
        hk = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._kproc, hmod, 0)
        if not hm or not hk:
            log("[LỖI] Không cài được hook chuột/bàn phím")
            return
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.DispatchMessageW(ctypes.byref(msg))
        user32.UnhookWindowsHookEx(hm)
        user32.UnhookWindowsHookEx(hk)

    # ---------- clipboard ----------
    def _grab_local_clip(self):
        if not self.clip.changed():
            return
        data = self.clip.read(files=self.file_mode)
        if not data:
            return
        with self.lock:
            self.clip_ver += 1
            self.clip_data, act = data, self.active
        log(f"[CLIPBOARD] MASTER vừa copy ({data_desc(data)})")
        if act is not None:
            self._push_clip(act)

    def _push_clip(self, peer):
        with self.lock:
            data, ver, link = self.clip_data, self.clip_ver, peer.link
            if data is None or link is None or peer.clip_ver == ver:
                return
            if data[0] == "files" and not self.file_mode:
                return
            peer.clip_ver = ver
        if data[0] == "blob":
            link.send_clip(data[1])
            log(f"[CLIPBOARD] -> {peer.ip} ({clip_desc(data[1])})")
            return
        entries, total = scan_files(data[1])
        if total > MAX_FILE:
            log(f"[COPY FILE] {size_str(total)} vượt giới hạn {MAX_FILE_MB} MB -> không gửi (dùng thư mục chia sẻ)")
        elif entries:
            link.send_files(entries, total)
            log(f"[COPY FILE] Gửi {len(entries)} mục ({size_str(total)}) -> {peer.ip}")

    def _recv_clip(self, peer, blob):
        self._got(peer, ("blob", blob), self.clip.write, blob)

    def _recv_files(self, peer, paths):
        if self.file_mode:
            self._got(peer, ("files", paths), self.clip.write_files, paths)

    def _got(self, peer, data, write, arg):
        with self.lock:
            self.clip_ver += 1
            self.clip_data, peer.clip_ver, act = data, self.clip_ver, self.active
        log(f"[CLIPBOARD] {peer.ip} vừa copy ({data_desc(data)}) -> MASTER")
        self.worker.submit(write, arg)
        if act is not None and act is not peer:
            self.worker.submit(self._push_clip, act)

    # ---------- mạng ----------
    def _on_peer_msg(self, link, t, a):
        peer = link.peer
        if peer.link is not link:
            return
        if t == T_EDGE:
            d, f = a
            if 0 <= d <= 3:
                self.try_switch(d, f, src=peer)
        elif t == T_CLIP:
            self._recv_clip(peer, a)
        elif t == T_FILES:
            self._recv_files(peer, a)

    def _peer_lost(self, peer):
        with self.lock:
            peer.link = None
            if self.active is peer:
                self.active, self.cell = None, self.home
                self._show_cursor()
                user32.SetCursorPos(*self.screen.park)
                self.px, self.py = self.screen.park
                log(f"<< Mất kết nối {peer.ip} -> quay về MASTER")
                self._title()

    def _peer_loop(self, peer):
        fails = 0
        while self.running:
            try:
                s = socket.create_connection((peer.ip, PORT), timeout=2.0)
            except OSError:
                fails += 1
                if fails == 3:
                    log(f"[..] Chưa kết nối được {peer.ip} - client đã chạy chưa? firewall mở cổng {PORT} chưa?")
                time.sleep(2.0)
                continue
            fails = 0
            done = threading.Event()
            link = Link(s, peer.ip, self._on_peer_msg, lambda _l: done.set(), ping=True)
            link.peer = peer
            with self.lock:
                peer.clip_ver, peer.link = 0, link
            link.start()
            link.send((T_OPT, self.file_mode))
            log(f"[OK] Đã kết nối {peer.ip} ({peer.label})")
            done.wait()
            self._peer_lost(peer)
            log(f"[X] Mất kết nối {peer.ip} - đang thử kết nối lại...")
            time.sleep(1.0)

    def run(self):
        log("=== MiniKVM MASTER ===")
        for p in self.peers.values():
            log(f"    {p.label:>6}: {p.ip}")
        self._log_scroll()
        self._log_file()
        threading.Thread(target=self._hook_loop, name="hook", daemon=True).start()
        for p in self.peers.values():
            threading.Thread(target=self._peer_loop, args=(p,), name="peer-" + p.ip, daemon=True).start()
        try:
            while self.running:
                time.sleep(3.0)
                self.screen.refresh()   # cắm/rút màn hình, đổi độ phân giải
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            if self.hook_tid:
                user32.PostThreadMessageW(self.hook_tid, WM_QUIT, 0, 0)
            log("Đã thoát.")
            time.sleep(0.3)


# =============================== CLIENT ===============================
class Client:
    def __init__(self, bind_ip=""):
        self.bind_ip = bind_ip
        self.link = None
        self.screen = Screen()
        self.keys, self.btns = set(), set()   # phím/nút đang giữ (để nhả hết khi rời máy)
        self.clip, self.worker = Clipboard(), Worker()
        self.edge_t = 0.0
        self.file_mode = False   # master bật/tắt bằng phím (mặc định TẮT)
        cleanup_temp(0)

    def move(self, link, dx, dy):
        x, y = cursor_pos()
        nx, ny = x + dx, y + dy
        if not self.screen.contains(nx, ny):
            now = time.monotonic()
            if now - self.edge_t > 0.03:
                self.edge_t = now
                for d in self.screen.exit_dirs(x, y, nx, ny):
                    link.send((T_EDGE, d, self.screen.frac(d, x, y)))
        user32.SetCursorPos(nx, ny)             # đặt đúng pixel, không bị tăng tốc 2 lần
        send_inputs(mouse_input(MOUSEEVENTF_MOVE))  # báo Windows có thao tác (không tắt màn hình)

    def button(self, b, down):
        f = BTN_FLAGS.get(b)
        if f:
            send_inputs(mouse_input(f[0] if down else f[1], f[2]))
            (self.btns.add if down else self.btns.discard)(b)

    def key(self, vk, scan, fl):
        up, ext = fl & 1, fl & 2
        send_inputs(key_input(vk, scan, (KEYEVENTF_KEYUP if up else 0) | (KEYEVENTF_EXTENDEDKEY if ext else 0)))
        (self.keys.discard if up else self.keys.add)((vk, scan, ext))

    def release_all(self):
        items = [key_input(vk, scan, KEYEVENTF_KEYUP | (KEYEVENTF_EXTENDEDKEY if ext else 0))
                 for vk, scan, ext in list(self.keys)]
        items += [mouse_input(BTN_FLAGS[b][1], BTN_FLAGS[b][2]) for b in list(self.btns)]
        self.keys.clear()
        self.btns.clear()
        if items:
            send_inputs(*items)

    def _on_msg(self, link, t, a):
        if link is not self.link:
            return
        if t == T_MOVE:
            self.move(link, *a)
        elif t == T_KEY:
            self.key(*a)
        elif t == T_BTN:
            self.button(*a)
        elif t == T_WHEEL:
            send_inputs(mouse_input(MOUSEEVENTF_HWHEEL if a[1] else MOUSEEVENTF_WHEEL, a[0]))
        elif t == T_PING:
            link.send((T_PONG,))
        elif t == T_ENTER:
            self.edge_t = 0.0
            self.screen.refresh()
            user32.SetCursorPos(*self.screen.entry(*a))
            send_inputs(mouse_input(MOUSEEVENTF_MOVE))
            log(">> Chuột/bàn phím đang điều khiển máy này")
        elif t == T_LEAVE:
            self.release_all()
            self.worker.submit(self._send_clip, link)
            log("<< Chuột đã rời máy này")
        elif t == T_CLIP:
            self.worker.submit(self._recv_clip, a)
        elif t == T_FILES:
            if self.file_mode:
                self.worker.submit(self._recv_files, a)
        elif t == T_OPT:
            on = bool(a[0])
            if not on:
                link.cancel_files()
            if on != self.file_mode:
                self.file_mode = on
                log(f"[COPY FILE] Master đã {'BẬT' if on else 'TẮT'} copy file")

    def _send_clip(self, link):
        if not self.clip.changed():
            return
        data = self.clip.read(files=self.file_mode)
        if not data or not link.alive:
            return
        if data[0] == "blob":
            link.send_clip(data[1])
            log(f"[CLIPBOARD] gửi về master ({clip_desc(data[1])})")
            return
        entries, total = scan_files(data[1])
        if total > MAX_FILE:
            log(f"[COPY FILE] {size_str(total)} vượt giới hạn {MAX_FILE_MB} MB -> không gửi")
        elif entries:
            link.send_files(entries, total)
            log(f"[COPY FILE] Gửi {len(entries)} mục ({size_str(total)}) về master")

    def _recv_files(self, paths):
        self.clip.write_files(paths)
        log("[COPY FILE] Xong - vào thư mục bất kỳ bấm Ctrl+V để dán")

    def _recv_clip(self, blob):
        self.clip.write(blob)
        log(f"[CLIPBOARD] nhận từ master ({clip_desc(blob)}) - Ctrl+V được rồi")

    def _on_close(self, link):
        if link is self.link:
            self.link = None
            self.release_all()
            log("[X] Mất kết nối master - đang chờ kết nối lại...")
            set_title("MiniKVM CLIENT | chưa kết nối")

    def run(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            srv.bind((self.bind_ip, PORT))
        except OSError as e:
            log(f"[LỖI] Không mở được cổng {PORT}: {e} (đang chạy 2 lần?)")
            return
        srv.listen(4)
        srv.settimeout(1.0)
        log(f"=== MiniKVM CLIENT === đang chờ master kết nối (cổng {PORT})")
        set_title("MiniKVM CLIENT | chưa kết nối")
        try:
            while True:
                try:
                    s, addr = srv.accept()
                except socket.timeout:
                    continue
                if MASTER_IP and addr[0] != MASTER_IP:
                    log(f"[!] Từ chối kết nối lạ từ {addr[0]}")
                    s.close()
                    continue
                old = self.link
                if old:
                    old.close()
                link = Link(s, addr[0], self._on_msg, self._on_close)
                self.link = link
                link.start()
                log(f"[OK] Master {addr[0]} đã kết nối")
                set_title(f"MiniKVM CLIENT | master {addr[0]}")
        except KeyboardInterrupt:
            pass
        finally:
            if self.link:
                self.link.close()
            srv.close()
            log("Đã thoát.")
            time.sleep(0.3)


# ================================ MAIN ================================
def local_ips(probe):
    ips = set()
    try:
        ips.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((probe, 9))   # UDP connect không gửi gói nào, chỉ để biết IP LAN của máy này
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    return ips


def main():
    if windll is None:
        print("MiniKVM chỉ chạy trên Windows.")
        return
    start_logger()
    win_setup()
    clients = [v for row in ipTable for v in row if v and v != "MASTER"]
    role = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    if role not in ("master", "client"):
        mine = local_ips(clients[0] if clients else "8.8.8.8")
        role = "client" if mine & set(clients) else "master"
    if not is_admin():
        log("[!] Chưa chạy bằng Administrator: sẽ không điều khiển được cửa sổ chạy quyền admin")
    if role == "master":
        Master().run()
    else:
        Client().run()


if __name__ == "__main__":
    main()