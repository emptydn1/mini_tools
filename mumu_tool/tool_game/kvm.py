# -*- coding: utf-8 -*-
"""
MiniKVM 2 trong 1 - 1 chuột + 1 bàn phím dùng cho nhiều PC Windows qua mạng LAN.
Gộp 2 script cũ (MiniKVM chuyển máy + đồng bộ chuột/bàn phím). Đổi chế độ bằng Scroll Lock ở master:

  Scroll Lock BẬT (đèn sáng) = ĐỒNG BỘ: thao tác trên master (di chuột, click, cuộn, gõ phím) được làm
                               y hệt trên TẤT CẢ các máy cùng lúc. Vị trí chuột tính theo tỉ lệ màn hình
                               nên máy khác độ phân giải vẫn click đúng chỗ.
  Scroll Lock TẮT            = CHUYỂN MÁY: đưa chuột ra cạnh màn hình để sang máy bên cạnh và điều khiển
                               riêng máy đó (clipboard + copy file dùng chung như MiniKVM cũ).

Nhẹ: không mã hóa, không cần cài thư viện (chỉ Python 3.8+ và Win32 API qua ctypes).
TẮT HẾT 2 script cũ trước khi chạy file này (chạy song song sẽ bị gửi chuột/phím 2 lần).

Cấu hình (ipTable, MASTER_IP, SYNC_IPS, PORT) sửa trong file Desktop\\kvm_config.txt của từng máy.
Lần đầu chạy chưa có file thì kvm.py tự tạo file mẫu trên Desktop. Sửa xong tắt kvm.py rồi chạy lại.

Copy CÙNG MỘT file này sang mọi máy rồi chạy:
    python kvm.py            -> tự nhận vai trò (IP có trong ipTable/SYNC_IPS = client, còn lại = master)
    python kvm.py master     -> ép chạy master
    python kvm.py client     -> ép chạy client
Nên chạy bằng quyền Administrator (để điều khiển được cả cửa sổ/game đang chạy quyền admin).

Phím ở master:
    Scroll Lock   BẬT = đồng bộ tất cả máy | TẮT = chuyển máy bằng cạnh màn hình
                  (đang điều khiển máy khác mà bấm BẬT -> chuột tự về master, hiện giữa màn hình, rồi đồng bộ)
    Pause/Break   bật/tắt copy file giữa các máy (đổi ở FILE_KEY)
    LOCK_KEY      (tùy chọn, mặc định không dùng) khóa chuột ở máy đang dùng: chạm cạnh không chuyển máy

Clipboard: lúc vừa BẬT đồng bộ, chữ/ảnh copy gần nhất được chép sang mọi máy (Ctrl+V ở đâu cũng dán cùng
nội dung). Trong lúc đồng bộ, Ctrl+C ở máy nào thì máy đó giữ nội dung của chính nó.
"""

# =============================== CẤU HÌNH ===============================
ipTable = [
    [None, "192.168.1.102", None],
    ["192.168.1.23", "MASTER", "192.168.1.106"],
    [None, "192.168.1.108", None],
]
SYNC_IPS = None       # máy làm theo khi ĐỒNG BỘ. None = mọi máy trong ipTable. Hoặc liệt kê, vd
                      # ["192.168.1.102", "192.168.1.50"] (IP không có trong ipTable vẫn được: máy đó chỉ đồng bộ)
PORT = 24900          # cổng TCP: client lắng nghe, master kết nối tới (mở firewall trên client)
MASTER_IP = None      # vd "192.168.1.10": client chỉ nhận kết nối từ máy này (None = nhận mọi máy)
MAX_CLIP_MB = 50      # giới hạn dung lượng clipboard mỗi lần chuyển (ảnh chụp màn hình...)
FILE_KEY = 0x13       # phím BẬT/TẮT copy file ở master: 0x13 = Pause/Break (muốn dùng F12 thì đặt 0x7B)
LOCK_KEY = None       # phím khóa chuột ở máy đang dùng (chạm cạnh không chuyển máy), vd 0x7B = F12. None = không dùng
MAX_FILE_MB = 2048    # giới hạn tổng dung lượng mỗi lần copy file/thư mục
HIDE_MASTER_CURSOR = True   # ẩn con trỏ của master khi đang điều khiển máy khác
CLICK_SETTLE = 0.008  # ĐỒNG BỘ: client chờ (giây) trước khi click nếu chuột vừa đổi chỗ.
                      # Rê nhanh rồi click mà máy khác click hụt thì tăng lên 0.012 - 0.02
RAW_MOUSE = True      # CHUYỂN MÁY: gửi chuyển động GỐC của chuột, máy kia tự tính tốc độ như chuột cắm thẳng vào nó
                      # (không bị rề khi khác độ phân giải / scale / tốc độ chuột). False = cách cũ
MOUSE_LIKE_MASTER = True   # CHUYỂN MÁY: lúc đang điều khiển, máy kia dùng TẠM tốc độ chuột + "Enhance pointer
                           # precision" của master (chuột đi y như ở master), rời máy thì trả lại cài đặt của nó
# ========================================================================

import collections
import ctypes
import itertools
import json
import math
import os
import queue
import shutil
import socket
import struct
import sys
import tempfile
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


# --- Raw Input: chuyển động gốc của chuột (chưa qua tốc độ/gia tốc của Windows) ---
class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [("usUsagePage", WORD), ("usUsage", WORD), ("dwFlags", DWORD), ("hwndTarget", VOIDP)]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [("dwType", DWORD), ("dwSize", DWORD), ("hDevice", VOIDP), ("wParam", ULONG_PTR)]


class _RAWBTN(ctypes.Structure):
    _fields_ = [("usButtonFlags", WORD), ("usButtonData", WORD)]


class _RAWBTNU(ctypes.Union):
    _fields_ = [("ulButtons", DWORD), ("b", _RAWBTN)]


class RAWMOUSE(ctypes.Structure):
    _fields_ = [("usFlags", WORD), ("u", _RAWBTNU), ("ulRawButtons", DWORD),
                ("lLastX", LONG), ("lLastY", LONG), ("ulExtraInformation", DWORD)]


class _RAWDATA(ctypes.Union):
    _fields_ = [("mouse", RAWMOUSE), ("pad", ctypes.c_ubyte * 64)]


class RAWINPUT(ctypes.Structure):
    _fields_ = [("header", RAWINPUTHEADER), ("data", _RAWDATA)]


WM_INPUT, RID_INPUT, RIM_TYPEMOUSE, RIDEV_INPUTSINK, PM_REMOVE = 0x00FF, 0x10000003, 0, 0x00000100, 0x0001
MOUSE_MOVE_ABSOLUTE = 0x01

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
VK_SCROLL, VK_PACKET, SM_SWAPBUTTON = 0x91, 0xE7, 23
INPUT_MOUSE, INPUT_KEYBOARD = 0, 1
MOUSEEVENTF_MOVE, MOUSEEVENTF_WHEEL, MOUSEEVENTF_HWHEEL = 0x0001, 0x0800, 0x1000
KEYEVENTF_EXTENDEDKEY, KEYEVENTF_KEYUP = 0x0001, 0x0002
CF_DIB, CF_UNICODETEXT, CF_HDROP, GMEM_MOVEABLE = 8, 13, 15, 0x0002
HWND_MESSAGE, HWND_TOPMOST = VOIDP(-3), VOIDP(-1)
WM_SETCURSOR, HIDER = 0x0020, 16   # HIDER: cỡ cửa sổ che con trỏ (pixel)
INJECT_TAG = 0x4B564D  # "KVM"


def key_name(vk):
    return {0x13: "Pause/Break", 0x7B: "F12", 0x91: "Scroll Lock", 0x2D: "Insert"}.get(vk, f"phím 0x{vk:02X}")


KEY_NAME = key_name(FILE_KEY)

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
    _sig(user32.MapVirtualKeyW, UINT, UINT, UINT)
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
    _sig(user32.PeekMessageW, BOOL, VOIDP, VOIDP, UINT, UINT, UINT)
    _sig(user32.RegisterRawInputDevices, BOOL, ctypes.POINTER(RAWINPUTDEVICE), UINT, UINT)
    _sig(user32.GetRawInputData, UINT, VOIDP, UINT, VOIDP, ctypes.POINTER(UINT), UINT)
    _sig(user32.SystemParametersInfoW, BOOL, UINT, UINT, VOIDP, UINT)
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
    """DPI-aware (tọa độ = pixel thật), ưu tiên CPU cao, tắt QuickEdit của console, sleep chính xác 1ms."""
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
    try:  # time.sleep vài ms cho chính xác (mặc định Windows làm tròn ~15ms) - dùng cho CLICK_SETTLE
        windll.winmm.timeBeginPeriod(1)
    except Exception:
        pass
    try:  # Windows 10/11: cửa sổ kvm nằm dưới nền / bị thu nhỏ thì Windows hay cho chạy "tiết kiệm điện" (EcoQoS,
        # nhân E) và bỏ qua timeBeginPeriod -> tắt cả 2 cho tiến trình này
        st = POWER_THROTTLING(1, 0x1 | 0x4, 0)   # EXECUTION_SPEED | IGNORE_TIMER_RESOLUTION, StateMask 0 = không tiết kiệm
        f = kernel32.SetProcessInformation
        f.restype, f.argtypes = BOOL, [VOIDP, ctypes.c_int, ctypes.POINTER(POWER_THROTTLING), DWORD]
        f(kernel32.GetCurrentProcess(), 4, ctypes.byref(st), ctypes.sizeof(st))   # 4 = ProcessPowerThrottling
    except Exception:
        pass
    sys.setswitchinterval(0.001)


class POWER_THROTTLING(ctypes.Structure):
    _fields_ = [("Version", DWORD), ("ControlMask", DWORD), ("StateMask", DWORD)]


def boost_thread():
    """Luồng xử lý chuột/phím: ưu tiên TIME_CRITICAL. Máy chạy nhiều giả lập (CPU 100%) thì luồng này vẫn được
    chạy ngay, không phải xếp hàng sau giả lập."""
    try:
        f = kernel32.SetThreadPriority
        f.restype, f.argtypes = BOOL, [VOIDP, ctypes.c_int]
        kernel32.GetCurrentThread.restype = VOIDP
        f(kernel32.GetCurrentThread(), 15)   # THREAD_PRIORITY_TIME_CRITICAL
    except Exception:
        pass


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


def led_on():
    """Đèn Scroll Lock đang sáng?"""
    return bool(user32.GetKeyState(VK_SCROLL) & 1)


def btn_down(b):
    """Nút chuột b (logic) có đang được giữ? GetAsyncKeyState đọc nút VẬT LÝ nên phải tính
    trường hợp đã đổi nút trái/phải (chuột cho người thuận tay trái)."""
    if b in (1, 2) and user32.GetSystemMetrics(SM_SWAPBUTTON):
        b = 3 - b
    return bool(user32.GetAsyncKeyState(BTN_VK[b]) & 0x8000)


# ---------- cài đặt chuột của Windows: tốc độ con trỏ (1-20) + "Enhance pointer precision" ----------
SPI_GETMOUSE, SPI_SETMOUSE, SPI_GETMOUSESPEED, SPI_SETMOUSESPEED = 0x0003, 0x0004, 0x0070, 0x0071
MOUSE_SAVE = os.path.join(tempfile.gettempdir(), "MiniKVM_mouse.txt")   # cài đặt gốc của client (phòng tắt ngang)
EXIT_HOOKS = []   # việc phải làm trước khi thoát (trả lại cài đặt chuột của client)


def get_mouse():
    """-> (tốc độ 1-20, ngưỡng 1, ngưỡng 2, gia tốc). "Enhance pointer precision" bật = gia tốc 1."""
    sp, arr = ctypes.c_int(10), (ctypes.c_int * 3)(6, 10, 1)
    user32.SystemParametersInfoW(SPI_GETMOUSESPEED, 0, ctypes.byref(sp), 0)
    user32.SystemParametersInfoW(SPI_GETMOUSE, 0, arr, 0)
    return (sp.value, arr[0], arr[1], arr[2])


def set_mouse(m):
    """Đặt TẠM (không lưu vào registry, khởi động lại máy là về như cũ)."""
    speed, t1, t2, acc = m
    if not (1 <= speed <= 20 and 0 <= acc <= 2):
        return
    user32.SystemParametersInfoW(SPI_SETMOUSE, 0, (ctypes.c_int * 3)(t1, t2, acc), 0)
    user32.SystemParametersInfoW(SPI_SETMOUSESPEED, 0, VOIDP(speed), 0)   # SETMOUSESPEED: giá trị nằm ngay trong tham số


def run_exit_hooks():
    for fn in list(EXIT_HOOKS):
        try:
            fn()
        except Exception:
            pass


# --------------------------------- Log ---------------------------------
# Mọi print đi qua 1 thread riêng: hook chuột/phím không bao giờ bị chặn vì console.
_logq = queue.SimpleQueue()
GUI = False   # True khi chạy từ kvm_gui.py (tham số --gui): in thêm dòng trạng thái "@@KVM {json}" cho giao diện


def log(msg):
    _logq.put(time.strftime("[%H:%M:%S] ") + msg)


def set_title(text):
    _logq.put((text,))


def gui_event(d):
    """Gửi trạng thái cho giao diện (chỉ khi chạy với --gui). Đi chung hàng đợi log nên đúng thứ tự."""
    if GUI:
        _logq.put(("ev", json.dumps(d)))


def _log_loop():
    while True:
        m = _logq.get()
        try:
            if isinstance(m, tuple):
                if len(m) == 2:
                    print("@@KVM " + m[1], flush=True)
                elif kernel32 is not None and not GUI:
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
    """Danh sách màn hình (hỗ trợ nhiều màn hình), tìm cạnh để chuyển máy, quy đổi tọa độ khi đồng bộ."""

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
        self.prim = (max(1, w), max(1, h))   # màn hình chính: gốc quy đổi tọa độ khi ĐỒNG BỘ
        self.park = (w // 2, h // 2)  # giữa màn hình chính: chỗ "đỗ" con trỏ master
        self.geo = (tuple(rects), min(r[0] for r in rects), min(r[1] for r in rects),
                    max(r[2] for r in rects), max(r[3] for r in rects))

    def contains(self, x, y):
        for l, t, r, b in self.geo[0]:
            if l <= x < r and t <= y < b:
                return True
        return False

    def clamp(self, x, y):
        """Điểm trên màn hình gần (x,y) nhất (tọa độ từ hook có thể vượt ra ngoài khi đẩy chuột sát mép)."""
        best, bd = (x, y), -1
        for l, t, r, b in self.geo[0]:
            cx, cy = min(max(x, l), r - 1), min(max(y, t), b - 1)
            d = (cx - x) * (cx - x) + (cy - y) * (cy - y)
            if bd < 0 or d < bd:
                best, bd = (cx, cy), d
                if not d:
                    break
        return best

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

    def norm(self, x, y):
        """ĐỒNG BỘ: pixel -> tỉ lệ theo màn hình chính (lấy TÂM pixel). Trả thêm pixel đã kẹp vào màn hình."""
        x, y = self.clamp(x, y)
        w, h = self.prim
        return (x + 0.5) / w, (y + 0.5) / h, (x, y)

    def denorm(self, rx, ry):
        """ĐỒNG BỘ: tỉ lệ -> pixel trên màn hình máy này."""
        w, h = self.prim
        return math.floor(rx * w), math.floor(ry * h)


# ------------------------------ Clipboard ------------------------------
CLIP_FORMATS = (("text", CF_UNICODETEXT), ("html", "HTML Format"),
                ("rtf", "Rich Text Format"), ("image", CF_DIB))
MAX_CLIP = MAX_CLIP_MB * 1024 * 1024


def pack_clip(items):
    parts = []   # ghép 1 lần (ảnh chụp màn hình vài chục MB: bớt copy -> bớt khựng chuột lúc chuyển máy)
    for name, data in items:
        nb = name.encode()
        parts += (struct.pack("<B", len(nb)), nb, struct.pack("<I", len(data)), data)
    return b"".join(parts)


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

    def mark(self):
        """Coi nội dung clipboard hiện tại là 'đã biết' (không gửi đi) - dùng khi tắt đồng bộ."""
        self.seq = user32.GetClipboardSequenceNumber()

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
 T_OPT, T_FBEGIN, T_FENTRY, T_FDATA, T_FEND, T_FABORT, T_FILES,
 T_SYNC, T_SPOS, T_SBTN, T_HELLO, T_RMOVE, T_MFEEL) = range(24)
FILE_T = (T_FBEGIN, T_FENTRY, T_FDATA, T_FEND, T_FABORT)
INPUT_T = (T_MOVE, T_BTN, T_WHEEL, T_KEY, T_SPOS, T_SBTN, T_RMOVE)   # gói phím/chuột
SYNC_T = (T_SPOS, T_SBTN)                                    # chỉ dùng lúc ĐỒNG BỘ
MOVE_T = (T_MOVE, T_RMOVE, T_SPOS)   # các kiểu di chuột: dồn nhiều gói thì gộp lại
SUM_T = (T_MOVE, T_RMOVE)            # di chuột tương đối: gộp = cộng dồn (T_SPOS: lấy vị trí mới nhất)
HDR = struct.Struct("<BI")
FMT = {T_MOVE: struct.Struct("<ii"), T_BTN: struct.Struct("<BB"), T_WHEEL: struct.Struct("<hB"),
       T_KEY: struct.Struct("<HHB"), T_ENTER: struct.Struct("<Bf"), T_EDGE: struct.Struct("<Bf"),
       T_OPT: struct.Struct("<B"),
       T_SYNC: struct.Struct("<B"),       # ĐỒNG BỘ bật/tắt
       T_SPOS: struct.Struct("<ff"),      # ĐỒNG BỘ: vị trí chuột (tỉ lệ màn hình chính)
       T_SBTN: struct.Struct("<BBff"),    # ĐỒNG BỘ: nút chuột + vị trí của chính lần click đó
       T_HELLO: struct.Struct("<H"),      # client báo phiên bản khi vừa kết nối
       T_RMOVE: struct.Struct("<ii"),     # CHUYỂN MÁY: chuyển động gốc của chuột (raw), client tự tính tốc độ
       T_MFEEL: struct.Struct("<Biii")}   # CHUYỂN MÁY: cài đặt chuột của master (tốc độ, ngưỡng 1, ngưỡng 2, gia tốc)
VERSION = 4           # 2 = đồng bộ, 3 = chuyển động chuột gốc, 4 = chuột đi y như master. Client cũ hơn vẫn dùng được
CHUNK = 64 * 1024     # clipboard lớn được cắt nhỏ, chen giữa các sự kiện chuột
TIMEOUT = 5.0         # không nhận được gì trong 5s -> coi như mất kết nối
PING_EVERY = 1.0      # master ping mỗi 1s (kể cả khi đang di chuột), client trả lời PONG
STUCK_AGE = 0.3       # ĐỒNG BỘ: phím/nút giữ quá lâu mà thực tế đã nhả -> tự gửi lệnh nhả
SLOW_MS = 30          # độ trễ đi-về master <-> client từ mức này trở lên thì báo "phản hồi chậm"


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
        self.pings = collections.deque(maxlen=8)   # lúc gửi từng PING -> PONG về thì tính độ trễ đi-về
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
        # cắt từng đoạn NGAY LÚC GỬI (không cắt hết 1 lần): ảnh lớn không làm khựng chuột lúc vừa chuyển máy
        self._stream(frame(T_CLIP, bytes([(1 if i == 0 else 0) | (2 if i == n - 1 else 0)])
                           + blob[i * CHUNK:(i + 1) * CHUNK]) for i in range(n))

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
        boost_thread()
        q, next_ping = self.q, 0.0
        try:
            while self.alive:
                try:
                    item = q.get_nowait() if self.stream is not None else q.get(timeout=PING_EVERY)
                except queue.Empty:
                    item = None
                buf, pend, n = bytearray(), None, 0   # pend: bước di chuột đang gộp (T_MOVE / T_RMOVE / T_SPOS)
                while item is not None:
                    t = item[0]
                    if t in SUM_T and pend is not None and pend[0] == t:
                        pend = (t, pend[1] + item[1], pend[2] + item[2])   # cộng dồn bước tương đối
                    elif t in MOVE_T:   # T_SPOS (đồng bộ): chỉ cần vị trí mới nhất
                        if pend is not None and pend[0] != t:
                            buf += encode(pend)
                        pend = item
                    elif t != T_WAKE:
                        if pend is not None:   # giữ đúng thứ tự: di chuột tới nơi rồi mới click/gõ phím
                            buf += encode(pend)
                            pend = None
                        buf += encode(item)
                    n += 1
                    if n >= 500:
                        break
                    try:
                        item = q.get_nowait()
                    except queue.Empty:
                        item = None
                if pend is not None:
                    buf += encode(pend)
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
                if self.ping:   # ping theo đồng hồ, KHÔNG chờ rảnh (di chuột liên tục cũng không mất kết nối)
                    now = time.monotonic()
                    if now >= next_ping:
                        buf += PING_BYTES
                        next_ping = now + PING_EVERY
                        self.pings.append(now)
                if buf and self.alive:
                    self.sock.sendall(buf)
        except OSError:
            pass
        finally:
            self.close()

    def _reader(self):
        boost_thread()
        buf, clip = bytearray(), None
        try:
            while self.alive:
                data = self.sock.recv(1 << 18)
                if not data:
                    break
                buf += data
                pos, end_all, mv = 0, len(buf), None
                while end_all - pos >= 5:
                    t, n = HDR.unpack_from(buf, pos)
                    if n > CHUNK + 4096:
                        raise ValueError("gói tin hỏng")
                    end = pos + 5 + n
                    if end > end_all:
                        break
                    body = bytes(buf[pos + 5:end])
                    pos = end
                    if t in MOVE_T:
                        # nhiều bước di chuột đến dồn (máy đang bận) -> gộp, xử lý 1 lần: chuột nhảy thẳng tới chỗ
                        # mới nhất thay vì chạy lại từng bước rồi trễ dần
                        a = FMT[t].unpack(body)
                        if mv is not None and mv[0] == t:
                            if t in SUM_T:
                                a = (mv[1][0] + a[0], mv[1][1] + a[1])
                        elif mv is not None:
                            self._dispatch(*mv)
                        mv = (t, a)
                        continue
                    if mv is not None:   # giữ đúng thứ tự: di chuột tới nơi rồi mới click/gõ phím
                        self._dispatch(*mv)
                        mv = None
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
                if mv is not None:
                    self._dispatch(*mv)
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
    def __init__(self, ip, cell, label, sync):
        self.ip, self.cell, self.label, self.sync = ip, cell, label, sync   # sync: làm theo khi ĐỒNG BỘ
        self.link = None
        self.ok = self.checked = False   # ok = client đủ mới để ĐỒNG BỘ (đã gửi T_HELLO, bản >= 2)
        self.ver = 0                     # phiên bản kvm.py trên client (0 = bản rất cũ, không gửi HELLO)
        self.clip_ver = 0
        self.warn_t = self.slow_t = 0.0
        self.rtt = None                  # độ trễ đi-về gần nhất (ms): master -> client -> master
        self.rtts = collections.deque(maxlen=10)   # 10 lần đo gần nhất (~10 giây)


class Master:
    def __init__(self, table=None, sync_ips=SYNC_IPS):
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
                    self.peers[v] = Peer(v, (r, c), DIR_NAME[d[0]] if d else f"ô[{r}][{c}]",
                                         sync_ips is None or v in sync_ips)
        for ip in sync_ips or ():
            if ip and ip != "MASTER" and ip not in self.peers:
                self.peers[ip] = Peer(ip, None, "chỉ đồng bộ", True)
        self.peer_list = tuple(self.peers.values())
        self.sync_peers = tuple(p for p in self.peer_list if p.sync)
        self.cell, self.active = self.home, None       # active = None nghĩa là đang ở MASTER
        self.lock = threading.RLock()
        self.screen = Screen()
        self.sync = led_on()                           # đèn Scroll Lock sáng = ĐỒNG BỘ
        self.scroll_held = False
        self.sync_keys, self.sync_btns = {}, {}        # phím/nút đã gửi "nhấn" cho các máy lúc đồng bộ
        self.spos, self.move_t = None, 0.0             # pixel vừa gửi lúc đồng bộ / lúc hook thấy chuột di
        self.locked = self.lock_held = False           # LOCK_KEY: khóa chuột ở máy đang dùng
        self.buttons, self.local_down = set(), set()
        self.px, self.py = cursor_pos()
        self.clip, self.worker = Clipboard(), Worker()
        self.clip_data, self.clip_ver = None, 0       # ("blob", bytes) | ("files", [đường dẫn])
        self.file_mode, self.file_held = False, False  # copy file: mặc định TẮT
        cleanup_temp(0)
        self.running, self.hook_tid = True, 0
        self._hider = self._blank = None
        # chuyển động chuột gốc (raw): None = chưa biết (thử), True = đang dùng, False = dùng cách cũ
        self.raw = None if RAW_MOUSE else False
        self.raw_wait = [0, 0, 0]   # bước di chuột hook thấy mà chưa có raw tương ứng: dx, dy, số lần
        self.raw_skip = False       # vừa từ master sang client: bỏ WM_INPUT của chính bước chạm mép (thuộc master)
        self._raw_hwnd, self._raw_buf = None, RAWINPUT()

    # ---------- chuyển động chuột gốc (raw input) ----------
    def _make_raw(self):
        """Cửa sổ ẩn nhận WM_INPUT (chuyển động gốc của chuột, kể cả khi kvm nằm dưới nền).
        Phải tạo trong thread có vòng lặp message (thread hook)."""
        hinst = kernel32.GetModuleHandleW(None)

        def wndproc(hwnd, msg, wp, lp):
            if msg == WM_INPUT:
                try:
                    self._on_raw(lp)
                except Exception:
                    log("[LỖI raw] " + traceback.format_exc())
            return user32.DefWindowProcW(hwnd, msg, wp, lp)

        self._rawproc = WNDPROC(wndproc)
        wc = WNDCLASSW(lpfnWndProc=self._rawproc, hInstance=hinst, lpszClassName="MiniKVMRaw")
        user32.RegisterClassW(ctypes.byref(wc))
        hwnd = user32.CreateWindowExW(0, "MiniKVMRaw", None, 0, 0, 0, 0, 0, HWND_MESSAGE, None, hinst, None)
        rid = RAWINPUTDEVICE(1, 2, RIDEV_INPUTSINK, hwnd)   # usage page 1 / usage 2 = chuột
        if hwnd and user32.RegisterRawInputDevices(ctypes.byref(rid), 1, ctypes.sizeof(rid)):
            self._raw_hwnd = hwnd
        else:
            self.raw = False
            log("[CHUỘT] Không đăng ký được chuyển động chuột gốc -> chuyển máy dùng cách cũ")

    def _use_raw(self, act):
        """Gửi chuyển động gốc cho máy này? (client bản >= 3 mới hiểu)"""
        return self.raw is not False and act.ver >= 3

    def _on_raw(self, lp):
        act = self.active
        if act is None or self.raw_skip or not self._use_raw(act):
            return
        ri = self._raw_buf
        sz = UINT(ctypes.sizeof(ri))
        n = user32.GetRawInputData(lp, RID_INPUT, ctypes.byref(ri), ctypes.byref(sz), ctypes.sizeof(RAWINPUTHEADER))
        if n == 0xFFFFFFFF or n < ctypes.sizeof(RAWINPUTHEADER) or ri.header.dwType != RIM_TYPEMOUSE:
            return
        m = ri.data.mouse
        if m.usFlags & MOUSE_MOVE_ABSOLUTE:
            self._raw_off("chuột báo tọa độ tuyệt đối (bút vẽ, máy ảo, Remote Desktop...)")
            return
        self.raw_wait = [0, 0, 0]
        if self.raw is None:
            self.raw = True
            log("[CHUỘT] Dùng chuyển động chuột gốc: máy kia tự tính tốc độ như chuột cắm thẳng vào nó")
        if (m.lLastX or m.lLastY) and act.link:
            act.link.send((T_RMOVE, m.lLastX, m.lLastY))

    def _wait_raw(self, dx, dy):
        """Hook thấy chuột di; chuyển động gốc (WM_INPUT) sẽ tới ngay sau. Không tới -> raw không dùng được."""
        self.raw_skip = False
        w = self.raw_wait
        w[0] += dx
        w[1] += dy
        w[2] += 1
        if w[2] >= (300 if self.raw else 30):
            self._raw_off("không nhận được chuyển động chuột gốc")

    def _raw_off(self, why):
        self.raw = False
        log(f"[CHUỘT] {why} -> chuyển máy dùng cách cũ")
        act, w = self.active, self.raw_wait
        if act is not None and act.link and (w[0] or w[1]):
            act.link.send((T_MOVE, w[0], w[1]))   # phần đã di mà chưa gửi -> gửi bù, không mất bước nào
        self.raw_wait = [0, 0, 0]

    def _flush_raw(self):
        """Trước khi gửi click/cuộn: lấy nốt các WM_INPUT còn trong hàng đợi gửi trước -> click đúng chỗ."""
        if not self._raw_hwnd:
            return
        msg = wt.MSG()
        for _ in range(256):
            if not user32.PeekMessageW(ctypes.byref(msg), self._raw_hwnd, WM_INPUT, WM_INPUT, PM_REMOVE):
                break
            self._on_raw(msg.lParam)
            user32.DefWindowProcW(msg.hWnd, msg.message, msg.wParam, msg.lParam)

    # ---------- chuyển máy ----------
    def neighbor(self, cell, d):
        r, c = cell[0] + STEP[d][0], cell[1] + STEP[d][1]
        if 0 <= r < len(self.table) and 0 <= c < len(self.table[r]):
            return self.table[r][c]
        return None

    def try_switch(self, d, frac, src=None):
        """Chuyển sang máy ở hướng d. src = máy client báo chạm cạnh (None = master)."""
        with self.lock:
            if self.sync or self.locked or self.buttons or src is not self.active:
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
        """side = None: về master, con trỏ hiện ở giữa màn hình chính."""
        old = self.active
        if old is not None and old.link:
            old.link.send((T_LEAVE,))
        if target is not None:   # gửi ENTER TRƯỚC khi đổi active -> máy mới không nhận phím/chuột trước ENTER
            target.link.send((T_ENTER, side, frac))
            if MOUSE_LIKE_MASTER and target.ver >= 4 and self._use_raw(target):
                try:   # máy kia dùng tạm tốc độ chuột của master -> chuột đi y như ở master
                    target.link.send((T_MFEEL,) + get_mouse())
                except Exception:
                    log("[LỖI] " + traceback.format_exc())
        self.active = target
        self.raw_wait = [0, 0, 0]
        self.raw_skip = old is None and target is not None
        if target is None:
            self.cell = self.home
            x, y = self.screen.park if side is None else self.screen.entry(side, frac)
            self._show_cursor()
            user32.SetCursorPos(x, y)
            self.px, self.py = x, y
            log("<< Về MASTER")
        else:
            self.cell = target.cell
            if old is None:  # rời master: đỗ + ẩn con trỏ giữa màn hình, lấy clipboard master nếu mới copy
                self._hide_cursor()
                self.worker.submit(self._grab_local_clip)
            self.worker.submit(self._push_clip, target)
            rt = list(target.rtts)
            log(f">> Điều khiển {target.ip} ({target.label})" + (
                f" | độ trễ {rt[-1]:.0f} ms, 10 giây qua cao nhất {max(rt):.0f} ms (dây LAN thường 1-3 ms)"
                if rt else ""))
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

    # ---------- trạng thái / log ----------
    def _title(self):
        where = self.active.ip if self.active else "MASTER"
        mode = "ĐỒNG BỘ tất cả máy" if self.sync else ("chuyển máy (đang KHÓA)" if self.locked else "chuyển máy")
        set_title(f"MiniKVM MASTER | Scroll Lock {'BẬT' if self.sync else 'TẮT'}: {mode} | "
                  f"Copy file: {'BẬT' if self.file_mode else 'TẮT'} | Đang ở: {where}")
        if GUI:   # ảnh chụp trạng thái cho giao diện: chế độ, máy đang điều khiển, từng máy đã kết nối chưa
            act = self.active
            gui_event({"ev": "master", "sync": self.sync, "file": self.file_mode, "locked": self.locked,
                       "active": act.ip if act else None,
                       "peers": [{"ip": p.ip, "sync": p.sync,
                                  "st": "off" if p.link is None else "ok" if p.ok else "old" if p.checked else "wait",
                                  "rtt": None if p.link is None or p.rtt is None else round(p.rtt)}
                                 for p in self.peer_list]})

    def _log_mode(self, why=""):
        why = f" ({why})" if why else ""
        if self.sync:
            n = sum(1 for p in self.sync_peers if p.link and p.ok)
            who = f"master + {n} máy" if n else "master (chưa có máy nào kết nối)"
            log(f"[SCROLL LOCK] BẬT  -> ĐỒNG BỘ: chuột + bàn phím điều khiển {who} cùng lúc{why}")
        else:
            log(f"[SCROLL LOCK] TẮT  -> CHUYỂN MÁY: đưa chuột ra cạnh màn hình để sang máy bên cạnh{why}")
        self._title()

    def _log_lock(self):
        if self.locked:
            log(f"[KHÓA] BẬT -> chuột ở yên máy hiện tại, chạm cạnh không chuyển máy "
                f"(bấm {key_name(LOCK_KEY)} để mở)")
        else:
            log("[KHÓA] TẮT -> chạm cạnh màn hình để chuyển máy")
        self._title()

    def _log_file(self):
        if self.file_mode:
            log(f"[COPY FILE] BẬT  -> Ctrl+C file/thư mục ở 1 máy, sang máy khác Ctrl+V (bấm {KEY_NAME} để tắt)")
        else:
            log(f"[COPY FILE] TẮT  -> chỉ copy chữ/ảnh (bấm {KEY_NAME} để bật copy file)")

    def set_sync(self, on, why=""):
        """Scroll Lock BẬT -> ĐỒNG BỘ mọi máy theo master; TẮT -> CHUYỂN MÁY bằng cạnh màn hình."""
        with self.lock:
            if on == self.sync:
                return
            self.sync = on
            self.sync_keys.clear()
            self.sync_btns.clear()
            if on:
                if self.active is not None:   # đồng bộ lấy master làm gốc -> rời máy đang điều khiển
                    self._switch(None, None, 0.0)
                self._bcast((T_SYNC, 1))
                self.spos = None
                self._sync_pos(*cursor_pos())   # các máy nhảy ngay tới vị trí chuột master
            else:
                self._bcast((T_SYNC, 0))        # các máy tự nhả hết phím/nút đang giữ
                for p in self.sync_peers:       # copy lúc đồng bộ: máy nào giữ nội dung của máy đó
                    p.clip_ver = self.clip_ver
                self.px, self.py = cursor_pos()
        self.worker.submit(self._sync_clip if on else self.clip.mark)
        self._log_mode(why)

    def set_file_mode(self, on):
        self.file_mode = on
        self._log_file()
        for p in self.peer_list:
            link = p.link
            if link:
                link.send((T_OPT, on))
                if not on:
                    link.cancel_files()   # tắt giữa chừng -> hủy luôn file đang gửi
        self._title()

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
        if act is None and self.sync:   # ĐỒNG BỘ: master vẫn dùng bình thường, gửi thêm cho mọi máy
            self._sync_mouse(msg, m)
            return False
        link = act.link if act is not None else None
        if msg == WM_MOUSEMOVE:
            rx, ry = m.pt.x, m.pt.y
            if act is None:
                x, y = self.screen.clamp(rx, ry)
                if not self.locked:
                    if self.buttons:  # bỏ nút "kẹt" (lỡ mất sự kiện nhả)
                        self.buttons = {b for b in self.buttons if btn_down(b)}
                    dirs = () if self.buttons else self.screen.edges_at(x, y)
                    if len(dirs) > 1 and abs(ry - self.py) > abs(rx - self.px):
                        dirs = sorted(dirs, key=lambda d: d < UP)
                    for d in dirs:
                        if self.try_switch(d, self.screen.frac(d, x, y)):
                            return True
                self.px, self.py = x, y
                return False
            cx, cy = cursor_pos()           # con trỏ master đứng yên -> độ lệch = bước di chuột
            dx, dy = rx - cx, ry - cy
            if self._use_raw(act):          # chuyển động gốc đi qua WM_INPUT (_on_raw); ở đây chỉ canh raw có tới
                self._wait_raw(dx, dy)
            elif link and (dx or dy):
                link.send((T_MOVE, dx, dy))
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
                if self._use_raw(act):
                    self._flush_raw()       # bước di chuột gốc còn chờ -> gửi trước, click mới đúng chỗ
                link.send((T_BTN, b, down))
            return True
        if msg in (WM_MOUSEWHEEL, WM_MOUSEHWHEEL):
            if act is None:
                return False
            delta = (m.mouseData >> 16) & 0xFFFF
            if link:
                if self._use_raw(act):
                    self._flush_raw()
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
        if LOCK_KEY and vk == LOCK_KEY:   # phím khóa chuột (tùy chọn): nuốt luôn
            if not up and not self.lock_held:
                self.locked = not self.locked
                self._log_lock()
            self.lock_held = not up
            return True
        if vk == VK_SCROLL:   # đổi chế độ; luôn để Windows xử lý để đèn Scroll Lock đổi theo
            if not up and not self.scroll_held:
                self.set_sync(not self.sync)
            self.scroll_held = not up
            return False
        ext = bool(k.flags & LLKHF_EXTENDED)
        act = self.active
        if act is None:
            if up:
                self.local_down.discard(vk)
            else:
                self.local_down.add(vk)
            if self.sync:     # ĐỒNG BỘ: master vẫn nhận phím bình thường, gửi thêm cho mọi máy
                self._sync_key(vk, k.scanCode & 0xFFFF, ext, up)
            return False
        if up and vk in self.local_down:   # phím nhấn lúc còn ở master -> nhả ở master, tránh kẹt phím
            self.local_down.discard(vk)
            return False
        link = act.link
        if link:
            link.send((T_KEY, vk, k.scanCode & 0xFFFF, (1 if up else 0) | (2 if ext else 0)))
        return True

    def _hook_loop(self):
        boost_thread()   # hook chậm = chuột của CẢ máy master bị chậm theo
        self.hook_tid = kernel32.GetCurrentThreadId()
        if HIDE_MASTER_CURSOR:
            self._make_hider()   # cửa sổ phải thuộc thread có vòng lặp message (thread này)
        if self.raw is not False:
            self._make_raw()
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

    # ---------- ĐỒNG BỘ ----------
    def _bcast(self, item):
        """Gửi cho mọi máy đồng bộ đã kết nối (và chạy đúng bản)."""
        for p in self.sync_peers:
            link = p.link
            if link and p.ok:
                link.send(item)

    def _sync_pos(self, x, y):
        rx, ry, pix = self.screen.norm(x, y)
        if pix != self.spos:
            self.spos = pix
            self._bcast((T_SPOS, rx, ry))

    def _sync_mouse(self, msg, m):
        if msg == WM_MOUSEMOVE:
            self.move_t = time.monotonic()
            self._sync_pos(m.pt.x, m.pt.y)
            return
        if msg in BTN_MSG:
            b, down = BTN_MSG[msg]
            if b == 4 and (m.mouseData >> 16) == 2:
                b = 5
            if down:
                self.buttons.add(b)
            else:
                self.buttons.discard(b)
            with self.lock:
                if not self.sync:
                    return
                if down:
                    self.sync_btns[b] = time.monotonic()
                elif self.sync_btns.pop(b, None) is None:
                    return   # nhấn từ lúc chưa bật đồng bộ -> các máy chưa nhận "nhấn", không gửi "nhả"
                rx, ry, self.spos = self.screen.norm(m.pt.x, m.pt.y)
                self._bcast((T_SBTN, b, down, rx, ry))   # click mang theo tọa độ của chính nó
            return
        if msg in (WM_MOUSEWHEEL, WM_MOUSEHWHEEL):
            delta = (m.mouseData >> 16) & 0xFFFF
            if delta >= 0x8000:
                delta -= 0x10000
            with self.lock:
                if delta and self.sync:
                    self._bcast((T_WHEEL, delta, msg == WM_MOUSEHWHEEL))

    def _sync_key(self, vk, scan, ext, up):
        if vk == VK_PACKET:
            return
        with self.lock:
            if not self.sync:   # vừa tắt đồng bộ (luồng khác) -> không gửi nữa
                return
            if up:
                if self.sync_keys.pop(vk, None) is None:
                    return   # nhấn từ lúc chưa bật đồng bộ -> không gửi "nhả"
            elif vk not in self.sync_keys:   # giữ phím: Windows tự lặp "nhấn" -> vẫn gửi, máy khác cũng lặp
                self.sync_keys[vk] = (scan, ext, time.monotonic())
            self._bcast((T_KEY, vk, scan, (1 if up else 0) | (2 if ext else 0)))

    def _release_stuck(self, now):
        """Phím/nút thật ra đã nhả nhưng hook không thấy sự kiện nhả (Ctrl+Alt+Del, Win+L, cửa sổ UAC...)
        -> tự gửi lệnh nhả cho các máy, tránh kẹt phím."""
        with self.lock:
            if not self.sync:
                return
            for vk, (scan, ext, t) in list(self.sync_keys.items()):
                if now - t >= STUCK_AGE and not (user32.GetAsyncKeyState(vk) & 0x8000):
                    del self.sync_keys[vk]
                    self._bcast((T_KEY, vk, scan, 1 | (2 if ext else 0)))
            for b, t in list(self.sync_btns.items()):
                if now - t >= STUCK_AGE and not btn_down(b):
                    del self.sync_btns[b]
                    rx, ry, _ = self.screen.norm(*cursor_pos())
                    self._bcast((T_SBTN, b, 0, rx, ry))

    def _watch_loop(self):
        """Luồng phụ, 20 lần/giây:
        - ĐỒNG BỘ: con trỏ bị phần mềm/game tự dời (hook không thấy) -> gửi vị trí mới; tự nhả phím/nút kẹt.
        - Đèn Scroll Lock là chuẩn: chế độ lệch đèn quá 1 giây thì theo đèn (bấm Scroll Lock lúc đang ở màn hình
          UAC, Ctrl+Alt+Del, màn hình khóa, cửa sổ quyền admin... thì hook không thấy). Chỉ làm khi đã thấy đèn
          đổi ít nhất 1 lần (chứng tỏ đọc được đèn thật), để không bao giờ "bấm xong 1 giây tự đổi lại"."""
        led_seen, live, bad_t, stuck_t = led_on(), False, None, 0.0
        while self.running:
            time.sleep(0.05)
            try:
                now = time.monotonic()
                led = led_on()
                if led != led_seen:
                    led_seen, live = led, True
                if live and led != self.sync:
                    if bad_t is None:
                        bad_t = now
                    elif now - bad_t >= 1.0:
                        bad_t = None
                        self.set_sync(led, "khớp theo đèn Scroll Lock")
                else:
                    bad_t = None
                if not self.sync or self.active is not None:
                    continue
                if now - self.move_t > 0.05:
                    self._sync_pos(*cursor_pos())
                if now - stuck_t >= 0.1:
                    stuck_t = now
                    self._release_stuck(now)
            except Exception:
                log("[LỖI] " + traceback.format_exc())
                time.sleep(1.0)

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

    def _push_clip(self, peer, blob_only=False):
        with self.lock:
            data, ver, link = self.clip_data, self.clip_ver, peer.link
            if data is None or link is None or peer.clip_ver == ver:
                return
            if data[0] == "files" and (blob_only or not self.file_mode):
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

    def _sync_clip(self):
        """(Worker) Vừa bật đồng bộ: chép clipboard chung (chữ/ảnh, không gửi file) sang mọi máy đồng bộ
        -> Ctrl+V lúc đồng bộ thì máy nào cũng dán cùng nội dung."""
        self._grab_local_clip()
        for p in self.sync_peers:
            if not self.sync:
                return
            self._push_clip(p, blob_only=True)

    def _recv_clip(self, peer, blob):
        self._got(peer, ("blob", blob), self.clip.write, blob)

    def _recv_files(self, peer, paths):
        if self.file_mode:
            self._got(peer, ("files", paths), self.clip.write_files, paths)

    def _got(self, peer, data, write, arg):
        with self.lock:
            self.clip_ver += 1
            self.clip_data, act, sync = data, self.active, self.sync
            if not (sync and peer.sync):
                peer.clip_ver = self.clip_ver
        log(f"[CLIPBOARD] {peer.ip} vừa copy ({data_desc(data)}) -> MASTER")
        self.worker.submit(write, arg)
        if act is not None and act is not peer:
            self.worker.submit(self._push_clip, act)
        elif sync:   # (lúc vừa bật đồng bộ) clipboard của máy vừa rời -> chép sang MỌI máy đồng bộ, kể cả máy
            for p in self.sync_peers:   # đó (clipboard của nó có thể vừa bị bản cũ hơn của master ghi đè)
                self.worker.submit(self._push_clip, p, True)

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
        elif t == T_HELLO:
            with self.lock:
                peer.ver = a[0]
                peer.ok = peer.ver >= 2   # bản 2 trở lên đều hiểu lệnh ĐỒNG BỘ
                if peer.ver < VERSION:
                    log(f"[!] {peer.ip} chạy kvm.py bản cũ ({peer.ver}) -> vẫn dùng được, nhưng chép file mới sang "
                        "máy đó để chuột mượt hơn")
                if peer.ok and peer.sync and self.sync:   # đang đồng bộ -> máy mới vào làm theo luôn
                    rx, ry, _ = self.screen.norm(*cursor_pos())
                    link.send((T_SYNC, 1))
                    link.send((T_SPOS, rx, ry))
                    self.worker.submit(self._push_clip, peer, True)   # + clipboard chung
            self._title()
        elif t == T_PONG:
            if link.pings:
                self._rtt(peer, (time.monotonic() - link.pings.popleft()) * 1000)
            if not peer.checked:
                peer.checked = True
                if not peer.ok:
                    log(f"[!] {peer.ip} đang chạy bản MiniKVM KHÁC bản này -> chỉ chuyển máy được, KHÔNG đồng bộ. "
                        "Chép file này sang máy đó rồi chạy lại")
                    self._title()

    def _rtt(self, peer, ms):
        """Đo độ trễ mỗi giây (PING -> PONG). Chậm thì báo: biết ngay máy nào quá tải / mạng chậm."""
        peer.rtt = ms
        peer.rtts.append(ms)
        now = time.monotonic()
        if ms >= SLOW_MS and now - peer.slow_t >= 10:
            peer.slow_t = now
            log(f"[!] {peer.ip} phản hồi chậm {ms:.0f} ms (bình thường dưới 5 ms) -> máy đó đang quá tải "
                "(CPU/RAM) hoặc mạng chậm (Wi-Fi)")
            self._title()

    def _peer_lost(self, peer):
        with self.lock:
            peer.link, peer.ok, peer.rtt = None, False, None
            peer.rtts.clear()
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
                peer.ok = peer.checked = False
                peer.ver = 0
            link.start()
            link.send((T_OPT, self.file_mode))
            log(f"[OK] Đã kết nối {peer.ip} ({peer.label})")
            self._title()
            done.wait()
            self._peer_lost(peer)
            log(f"[X] Mất kết nối {peer.ip} - đang thử kết nối lại...")
            time.sleep(1.0)

    def run(self):
        log(f"=== MiniKVM MASTER (bản {VERSION}) ===")
        for p in self.peer_list:
            log(f"    {p.label:>11}: {p.ip}" + ("" if p.sync else "   (không đồng bộ)"))
        self._log_mode()
        self._log_file()
        if LOCK_KEY:
            log(f"[KHÓA] bấm {key_name(LOCK_KEY)} để khóa/mở khóa chuột ở máy đang dùng")
        threading.Thread(target=self._hook_loop, name="hook", daemon=True).start()
        threading.Thread(target=self._watch_loop, name="watch", daemon=True).start()
        for p in self.peer_list:
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
        self.keys, self.btns = set(), set()   # phím/nút đang giữ (để nhả hết khi rời máy / tắt đồng bộ)
        self.clip, self.worker = Clipboard(), Worker()
        self.edge_t = self.move_t = self.slow_t = 0.0
        self.file_mode = False   # master bật/tắt bằng phím (mặc định TẮT)
        self.sync = False        # master đang ĐỒNG BỘ (Scroll Lock BẬT) -> máy này làm theo
        self.entered = False     # CHUYỂN MÁY: chuột đang ở máy này (giữa ENTER và LEAVE)
        self.poke_ev = threading.Event()
        threading.Thread(target=self._poke_loop, name="poke", daemon=True).start()
        self.my_mouse, self.mlock, self.mfeel_logged = None, threading.Lock(), False   # cài đặt chuột gốc của máy này
        EXIT_HOOKS.append(self.mouse_restore)
        self._recover_mouse()
        cleanup_temp(0)

    # ---------- chuột đi y như master: dùng tạm cài đặt chuột của master lúc đang điều khiển máy này ----------
    def mouse_like(self, m):
        if not self.entered:
            return
        with self.mlock:
            try:
                cur = get_mouse()
                if self.my_mouse is None:   # lưu cài đặt của máy này (cả ra file, phòng kvm bị tắt ngang)
                    self.my_mouse = cur
                    try:
                        with open(MOUSE_SAVE, "w") as f:
                            f.write(" ".join(map(str, cur)))
                    except OSError:
                        pass
                if cur != tuple(m):
                    set_mouse(m)
                    if not self.mfeel_logged:
                        self.mfeel_logged = True
                        log(f"[CHUỘT] Lúc điều khiển máy này: dùng tạm tốc độ chuột của master ({m[0]}/20, Enhance "
                            f"pointer precision {'BẬT' if m[3] else 'TẮT'}). Chuột rời đi là trả lại cài đặt của máy "
                            f"này ({cur[0]}/20, {'BẬT' if cur[3] else 'TẮT'})")
            except Exception:
                log("[LỖI] " + traceback.format_exc())

    def mouse_restore(self):
        """Trả lại cài đặt chuột của máy này (chuột rời đi / tắt đồng bộ / mất kết nối / thoát)."""
        with self.mlock:
            if self.my_mouse is None:
                return
            m, self.my_mouse = self.my_mouse, None
            try:
                if get_mouse() != m:
                    set_mouse(m)
            except Exception:
                pass
            try:
                os.remove(MOUSE_SAVE)
            except OSError:
                pass

    def _recover_mouse(self):
        """Lần trước kvm bị tắt ngang lúc đang dùng tạm cài đặt của master -> trả lại cài đặt của máy này."""
        if not os.path.exists(MOUSE_SAVE):
            return
        try:
            with open(MOUSE_SAVE) as f:
                m = tuple(int(v) for v in f.read().split())
            if len(m) == 4:
                set_mouse(m)
                log("[CHUỘT] Lần trước kvm bị tắt ngang -> đã trả lại tốc độ chuột của máy này")
        except (OSError, ValueError):
            pass
        try:
            os.remove(MOUSE_SAVE)
        except OSError:
            pass

    def _poke_loop(self):
        """Luồng riêng báo Windows "có thao tác chuột": không tắt màn hình, hiện lại con trỏ bị ẩn lúc gõ phím.
        Tối đa 4 lần/giây. Để riêng vì lệnh này phải đi qua hook của mọi phần mềm khác trên máy (MuMu, phần mềm
        chuột, anti-cheat...): máy nhiều giả lập có thể mất vài chục ms/lần -> không bắt luồng nhận chuột phải chờ."""
        while True:
            self.poke_ev.wait()
            self.poke_ev.clear()
            send_inputs(mouse_input(MOUSEEVENTF_MOVE))
            time.sleep(0.25)

    def _check_slow(self, t0, what):
        """Windows trên máy này xử lý chuột/phím quá chậm (máy quá tải) -> báo ra cửa sổ, 10 giây tối đa 1 lần."""
        ms = (time.perf_counter() - t0) * 1000
        if ms >= SLOW_MS:
            now = time.monotonic()
            if now - self.slow_t >= 10:
                self.slow_t = now
                log(f"[!] Windows máy này {what} chậm: {ms:.0f} ms/lần (bình thường dưới 1 ms) -> máy đang quá tải "
                    "(CPU/RAM/card màn hình)")

    # ---------- CHUYỂN MÁY: bước di chuột tương đối, chạm cạnh thì báo master ----------
    def move(self, link, dx, dy):
        t0 = time.perf_counter()
        x, y = cursor_pos()
        nx, ny = x + dx, y + dy
        if not self.screen.contains(nx, ny):
            now = time.monotonic()
            if now - self.edge_t > 0.03:
                self.edge_t = now
                for d in self.screen.exit_dirs(x, y, nx, ny):
                    link.send((T_EDGE, d, self.screen.frac(d, x, y)))
        user32.SetCursorPos(nx, ny)             # đặt đúng pixel, không bị tăng tốc 2 lần
        self.poke_ev.set()
        self._check_slow(t0, "di chuột")

    def rmove(self, link, dx, dy):
        """CHUYỂN MÁY, chuyển động gốc (raw) của chuột master: đưa vào Windows máy này như chuột cắm thẳng vào nó
        -> Windows tự áp tốc độ chuột, gia tốc, scale màn hình của máy này: mượt y như chuột thật."""
        t0 = time.perf_counter()
        x, y = cursor_pos()
        c = self.screen.contains   # đang nằm sát mép mà vẫn đẩy ra ngoài -> báo master chuyển máy
        out = [d for d, push in ((LEFT, dx < 0 and not c(x - 1, y)), (RIGHT, dx > 0 and not c(x + 1, y)),
                                 (UP, dy < 0 and not c(x, y - 1)), (DOWN, dy > 0 and not c(x, y + 1))) if push]
        if out:
            now = time.monotonic()
            if now - self.edge_t > 0.03:
                self.edge_t = now
                if abs(dy) > abs(dx):
                    out.sort(key=lambda d: d < UP)   # đẩy dọc nhiều hơn -> ưu tiên trên/dưới
                for d in out:
                    link.send((T_EDGE, d, self.screen.frac(d, x, y)))
        send_inputs(mouse_input(MOUSEEVENTF_MOVE, 0, dx, dy))
        self._check_slow(t0, "di chuột")

    # ---------- ĐỒNG BỘ: vị trí tuyệt đối theo tỉ lệ màn hình master ----------
    def move_to(self, pos):
        t0 = time.perf_counter()
        user32.SetCursorPos(*pos)
        self.poke_ev.set()
        self.move_t = time.perf_counter()
        self._check_slow(t0, "di chuột")

    def sync_button(self, b, down, rx, ry):
        """Lệnh click mang theo tọa độ của chính nó -> đặt chuột đúng chỗ rồi mới click."""
        pos = self.screen.denorm(rx, ry)
        if cursor_pos() != pos:
            self.move_to(pos)
        if down:   # chuột vừa đổi chỗ -> chờ ứng dụng/game kịp nhận vị trí mới rồi mới nhấn
            wait = CLICK_SETTLE - (time.perf_counter() - self.move_t)
            if wait > 0:
                time.sleep(wait)
        self.button(b, down)

    def set_sync(self, on):
        self.release_all()
        self.entered = False
        self.mouse_restore()
        if on == self.sync:
            return
        self.sync = on
        if on:
            self.screen.refresh()
            log("[ĐỒNG BỘ] BẬT -> máy này làm theo chuột + bàn phím của master")
        else:
            self.worker.submit(self.clip.mark)   # copy lúc đồng bộ thì máy nào giữ nội dung của máy đó
            log("[ĐỒNG BỘ] TẮT")
        self._title()

    # ---------- dùng chung ----------
    def button(self, b, down):
        f = BTN_FLAGS.get(b)
        if f:
            t0 = time.perf_counter()
            send_inputs(mouse_input(f[0] if down else f[1], f[2]))
            (self.btns.add if down else self.btns.discard)(b)
            self._check_slow(t0, "bấm chuột")

    def key(self, vk, scan, fl):
        up, ext = fl & 1, fl & 2
        if not scan:   # vài phím không có scan code -> tự tra (game đọc scan code mới nhận đúng phím)
            scan = user32.MapVirtualKeyW(vk, 0) & 0xFFFF
        t0 = time.perf_counter()
        send_inputs(key_input(vk, scan, (KEYEVENTF_KEYUP if up else 0) | (KEYEVENTF_EXTENDEDKEY if ext else 0)))
        (self.keys.discard if up else self.keys.add)((vk, scan, ext))
        self._check_slow(t0, "gõ phím")

    def release_all(self):
        items = [key_input(vk, scan, KEYEVENTF_KEYUP | (KEYEVENTF_EXTENDEDKEY if ext else 0))
                 for vk, scan, ext in list(self.keys)]
        items += [mouse_input(BTN_FLAGS[b][1], BTN_FLAGS[b][2]) for b in list(self.btns)]
        self.keys.clear()
        self.btns.clear()
        if items:
            send_inputs(*items)

    def _title(self):
        link = self.link
        set_title("MiniKVM CLIENT | " + (f"master {link.name}" if link else "chưa kết nối")
                  + (" | ĐỒNG BỘ: đang làm theo master" if link and self.sync else ""))
        gui_event({"ev": "client", "master": link.name if link else None, "sync": bool(link and self.sync),
                   "entered": bool(link and self.entered), "file": self.file_mode})

    def _on_msg(self, link, t, a):
        if link is not self.link:
            return
        if t in INPUT_T:   # phím/chuột chỉ nhận khi chuột đang ở máy này hoặc đang ĐỒNG BỘ
            if t in SYNC_T and not self.sync or not (self.entered or self.sync):
                return     # (gói đến trễ sau LEAVE / sau khi tắt đồng bộ -> bỏ, tránh kẹt phím)
            if t == T_RMOVE:
                self.rmove(link, *a)
            elif t == T_MOVE:
                self.move(link, *a)
            elif t == T_SPOS:
                self.move_to(self.screen.denorm(*a))
            elif t == T_KEY:
                self.key(*a)
            elif t == T_BTN:
                self.button(*a)
            elif t == T_SBTN:
                self.sync_button(*a)
            else:
                send_inputs(mouse_input(MOUSEEVENTF_HWHEEL if a[1] else MOUSEEVENTF_WHEEL, a[0]))
        elif t == T_PING:
            link.send((T_PONG,))
        elif t == T_SYNC:
            self.set_sync(bool(a[0]))
        elif t == T_ENTER:
            self.entered, self.edge_t = True, 0.0
            self.screen.refresh()
            user32.SetCursorPos(*self.screen.entry(*a))
            self.poke_ev.set()
            log(">> Chuột/bàn phím đang điều khiển máy này")
            self._title()
        elif t == T_MFEEL:
            self.mouse_like(a)
        elif t == T_LEAVE:
            self.entered = False
            self.release_all()
            self.mouse_restore()
            self.worker.submit(self._send_clip, link)
            log("<< Chuột đã rời máy này")
            self._title()
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
                self._title()

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
            self.sync = self.entered = False
            self.release_all()
            self.mouse_restore()
            log("[X] Mất kết nối master - đang chờ kết nối lại...")
            self._title()

    def run(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            srv.bind((self.bind_ip, PORT))
        except OSError as e:
            log(f"[LỖI] Không mở được cổng {PORT}: {e} (đang chạy 2 lần?)")
            gui_event({"ev": "error", "msg": f"Cổng {PORT} đang bị chiếm - có thể kvm.py đang chạy ở cửa sổ khác"})
            time.sleep(0.3)
            return
        srv.listen(4)
        srv.settimeout(1.0)
        log(f"=== MiniKVM CLIENT (bản {VERSION}) === đang chờ master kết nối (cổng {PORT})")
        self._title()
        try:
            while True:
                try:
                    s, addr = srv.accept()
                except socket.timeout:
                    if self.sync:
                        self.screen.refresh()   # đổi độ phân giải lúc đang đồng bộ
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
                link.send((T_HELLO, VERSION))   # báo phiên bản cho master
                link.start()
                log(f"[OK] Master {addr[0]} đã kết nối")
                self._title()
        except KeyboardInterrupt:
            pass
        finally:
            if self.link:
                self.link.close()
            srv.close()
            self.mouse_restore()
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


CONFIG_NAME = "kvm_config.txt"   # nằm trên Desktop của user đang chạy kvm.py
CONFIG_FILE = CONFIG_NAME
CONFIG_KEYS = ("ipTable", "MASTER_IP", "SYNC_IPS", "PORT", "FILE_KEY", "LOCK_KEY", "CLICK_SETTLE", "HIDE_MASTER_CURSOR",
               "RAW_MOUSE", "MOUSE_LIKE_MASTER")
CONFIG_TEMPLATE = '''# Cấu hình MiniKVM - sửa file này, KHÔNG cần sửa kvm.py. Dòng bắt đầu bằng # là ghi chú.
# Sửa xong thì tắt kvm.py rồi chạy lại.

# Vị trí các máy: "MASTER" là máy master, None là ô trống. Mọi máy nên dùng CÙNG ipTable.
ipTable = [
    [None, "192.168.1.102", None],
    ["192.168.1.23", "MASTER", "192.168.1.106"],
    [None, "192.168.1.108", None],
]

# Chỉ dùng ở CLIENT: IP máy master, vd MASTER_IP = "192.168.1.10" -> chỉ nhận đúng máy đó.
# None = nhận mọi máy (trong mạng LAN có 2 master thì nên điền).
MASTER_IP = None

# Máy làm theo khi ĐỒNG BỘ (Scroll Lock BẬT). None = mọi máy trong ipTable.
SYNC_IPS = None

# Cổng TCP (mọi máy phải giống nhau)
PORT = 24900

# Phím bật/tắt copy file ở master (mã phím Windows): 0x13 = Pause/Break, 0x7B = F12
FILE_KEY = 0x13

# Phím khóa chuột ở máy đang dùng (chạm cạnh không chuyển máy). None = không dùng, vd 0x7A = F11
LOCK_KEY = None

# ĐỒNG BỘ: client chờ (giây) trước khi click nếu chuột vừa đổi chỗ. Click hụt thì tăng lên 0.012 - 0.02
CLICK_SETTLE = 0.008

# Ẩn con trỏ của master khi đang điều khiển máy khác (True / False)
HIDE_MASTER_CURSOR = True

# CHUYỂN MÁY: gửi chuyển động GỐC của chuột -> máy kia tự tính tốc độ như chuột cắm thẳng vào nó (mượt, đúng tốc độ).
# Chuột sang máy khác bị lỗi lạ (đi sai, không đi) thì đặt False để dùng cách cũ. Chỉ cần sửa ở máy MASTER.
RAW_MOUSE = True

# CHUYỂN MÁY: lúc đang điều khiển, máy kia dùng TẠM tốc độ chuột + "Enhance pointer precision" của master -> chuột đi
# y như ở master. Chuột rời máy đó là trả lại cài đặt của nó. False = mỗi máy dùng cài đặt chuột riêng. Sửa ở MASTER.
MOUSE_LIKE_MASTER = True
'''


def desktop_dir():
    """Thư mục Desktop thật của user (kể cả khi Desktop đã bị OneDrive chuyển sang OneDrive\\Desktop)."""
    try:
        buf = ctypes.create_unicode_buffer(260)
        if windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, buf) == 0 and buf.value:   # CSIDL_DESKTOPDIRECTORY
            return buf.value
    except Exception:
        pass
    return os.path.join(os.environ.get("USERPROFILE") or os.path.expanduser("~"), "Desktop")


def load_config():
    """Đọc %USERPROFILE%\\Desktop\\kvm_config.txt (chưa có thì tạo file mẫu). Chỉ đọc giá trị, không chạy code trong file."""
    import ast
    global CONFIG_FILE
    CONFIG_FILE = os.path.join(desktop_dir(), CONFIG_NAME)
    g = globals()
    status = "ok"
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(CONFIG_TEMPLATE)
            log(f"[CẤU HÌNH] Chưa có file -> đã tạo {CONFIG_FILE}, mở ra sửa rồi chạy lại")
            status = "created"
        except OSError as e:
            log(f"[CẤU HÌNH] Không tạo được {CONFIG_FILE}: {e} -> dùng cấu hình trong kvm.py")
            gui_event({"ev": "config", "path": CONFIG_FILE, "st": "error", "msg": str(e)})
            return
    try:
        with open(CONFIG_FILE, encoding="utf-8-sig") as f:
            tree = ast.parse(f.read(), CONFIG_FILE)
        vals = {}
        for node in tree.body:
            if (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id in CONFIG_KEYS):
                vals[node.targets[0].id] = ast.literal_eval(node.value)
        t = vals.get("ipTable", g["ipTable"])
        if not (isinstance(t, list) and all(isinstance(r, list) for r in t)
                and all(v is None or isinstance(v, str) for r in t for v in r)
                and sum(v == "MASTER" for r in t for v in r) == 1):
            raise ValueError('ipTable phải là danh sách các dòng [..], có đúng 1 ô "MASTER"')
        if not (vals.get("MASTER_IP") is None or isinstance(vals.get("MASTER_IP"), str)):
            raise ValueError('MASTER_IP phải là None hoặc "IP"')
        s = vals.get("SYNC_IPS")
        if not (s is None or isinstance(s, list) and all(isinstance(v, str) for v in s)):
            raise ValueError('SYNC_IPS phải là None hoặc ["IP", ...]')
        p = vals.get("PORT", 24900)
        if type(p) is not int or not 1 <= p <= 65535:
            raise ValueError("PORT phải là số từ 1 đến 65535")
        fk = vals.get("FILE_KEY", g["FILE_KEY"])
        if type(fk) is not int or not 0 < fk < 255 or fk == VK_SCROLL:
            raise ValueError("FILE_KEY phải là mã phím, vd 0x13 (không được là Scroll Lock)")
        lk = vals.get("LOCK_KEY", g["LOCK_KEY"])
        if not (lk is None or type(lk) is int and 0 < lk < 255 and lk not in (VK_SCROLL, fk)):
            raise ValueError("LOCK_KEY phải là None hoặc mã phím khác FILE_KEY và Scroll Lock")
        cs = vals.get("CLICK_SETTLE", 0.008)
        if type(cs) not in (int, float) or not 0 <= cs <= 0.1:
            raise ValueError("CLICK_SETTLE phải từ 0 đến 0.1 (giây)")
        if type(vals.get("HIDE_MASTER_CURSOR", True)) is not bool:
            raise ValueError("HIDE_MASTER_CURSOR phải là True hoặc False")
        if type(vals.get("RAW_MOUSE", True)) is not bool:
            raise ValueError("RAW_MOUSE phải là True hoặc False")
        if type(vals.get("MOUSE_LIKE_MASTER", True)) is not bool:
            raise ValueError("MOUSE_LIKE_MASTER phải là True hoặc False")
    except (OSError, SyntaxError, ValueError) as e:
        log(f"[CẤU HÌNH] LỖI trong {CONFIG_FILE}: {e}")
        log("[CẤU HÌNH] Sửa file rồi chạy lại. Tạm dùng cấu hình trong kvm.py")
        gui_event({"ev": "config", "path": CONFIG_FILE, "st": "error", "msg": str(e)})
        return
    g.update(vals)
    g["KEY_NAME"] = key_name(g["FILE_KEY"])
    log(f"[CẤU HÌNH] Đọc {CONFIG_FILE}" + (f" | MASTER_IP = {MASTER_IP}" if MASTER_IP else ""))
    gui_event({"ev": "config", "path": CONFIG_FILE, "st": status})


def _gui_stdin():
    """(--gui) Giao diện gửi "quit" qua stdin để dừng; giao diện bị tắt ngang (stdin đóng) cũng tự thoát,
    không bỏ lại kvm.py chạy ngầm. Thoát tiến trình là Windows tự gỡ hook, client tự nhả phím."""
    try:
        for line in sys.stdin:
            if line.strip().lower() in ("quit", "exit", "stop"):
                break
    except Exception:
        pass
    run_exit_hooks()   # client: trả lại cài đặt chuột của máy này trước khi thoát
    log("Đã thoát (giao diện yêu cầu dừng).")
    time.sleep(0.3)
    os._exit(0)


def main():
    global GUI
    args = [a.lower() for a in sys.argv[1:]]
    GUI = "--gui" in args
    if windll is None:
        print("MiniKVM chỉ chạy trên Windows.")
        return
    if GUI:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        threading.Thread(target=_gui_stdin, name="gui-stdin", daemon=True).start()
    start_logger()
    win_setup()
    load_config()
    clients = [v for row in ipTable for v in row if v and v != "MASTER"] + [v for v in (SYNC_IPS or ()) if v]
    role = next((a for a in args if not a.startswith("--")), "")
    if role not in ("master", "client"):
        mine = local_ips(clients[0] if clients else "8.8.8.8")
        role = "client" if mine & set(clients) else "master"
    admin = is_admin()
    gui_event({"ev": "start", "role": role, "version": VERSION, "admin": admin, "port": PORT,
               "ips": sorted(local_ips(clients[0] if clients else "8.8.8.8"))})
    if not admin:
        log("[!] Chưa chạy bằng Administrator: sẽ không điều khiển được cửa sổ chạy quyền admin")
    if role == "master":
        Master(sync_ips=SYNC_IPS).run()   # truyền rõ: SYNC_IPS có thể vừa được đọc từ file cấu hình
    else:
        Client().run()


if __name__ == "__main__":
    main()