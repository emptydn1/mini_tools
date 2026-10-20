#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KeyClick - Bấm phím thay cho click chuột (dùng được cho mọi tựa game)
=====================================================================

  1. Bấm "＋ Thêm nút": một nút tròn hiện giữa màn hình, có dấu nháy nhấp nháy.
  2. Nhấn 1 phím (ví dụ A) để gán phím đó cho nút tròn.
  3. Kéo nút tròn tới chỗ cần click trong game.
  4. Nhấn F8 (hoặc tick "Bật phím tắt"). Từ giờ nhấn A = click chuột tại tâm nút tròn.

  - Bấm vào nút tròn: gán lại phím (Esc: huỷ).
  - Kéo giữa nút: di chuyển. Kéo MÉP nút hoặc lăn chuột: phóng to / thu nhỏ.
  - Ctrl + kéo nút, hoặc chuột phải > "Nhân bản": tạo bản sao rồi gõ phím mới cho nó.
  - Chuột phải vào nút: click trái/phải/giữa, chế độ click / giữ / turbo, đổi cỡ, xoá.
  - Thanh trượt "Độ đậm nền nút": nền nút trong hơn / đậm hơn (chữ luôn rõ).
  - Khi đang BẬT phím tắt, các nút bị khoá và chuột đi xuyên qua (không cản game).
    Muốn chỉnh nút thì nhấn F8 để tắt trước.
  - "＋ Nút vuốt": nhấn phím = vuốt từ nút tới chấm vàng (kéo chấm vàng để chọn hướng);
    giữ phím = vuốt rồi giữ ở chấm vàng tới khi thả phím.
  - Tab "Script": nhiều combo, chạy CÙNG LÚC được, ví dụ Q ▸ U – 100 ms – I – 200 ms – O.
    F9 chạy cùng lúc mọi combo có tick "Chạy khi nhấn F9"; phím chạy riêng (không bắt
    buộc) chạy / dừng riêng từng combo; Esc dừng hết. Phím của nút tròn luôn để click.
    Ô "Khoá phím các nút trong combo khi đang chạy" (mặc định tick): lúc combo chạy, bấm
    tay A, S… của combo đó không click.
  - Đang BẬT thì phím đã gán luôn click, dù cửa sổ nào đang ở trước (kể cả chính
    KeyClick); chỉ tạm dừng khi đang gõ trong ô Tên (ô số thì chỉ phím số dùng để gõ).
  - Game chạy quyền Admin: KeyClick báo ngay và có ô "Luôn chạy bằng quyền Admin".

Chạy trên Windows 10/11 với Python 3.8 trở lên (bản cài từ python.org đã có tkinter).
Không cần cài thêm thư viện nào. Muốn có file .exe thì chạy build_exe.bat.

Cấu trúc code:
  WinAPI        - gọi Windows API bằng ctypes: hook bàn phím toàn hệ thống, giả lập chuột
  ClickEngine   - nhận phím từ hook, quyết định "nuốt" phím nào, giao việc click cho luồng riêng
  Circle        - một nút tròn trên màn hình (2 lớp cửa sổ: nền mờ + chữ rõ, luôn nằm trên cùng)
  App           - cửa sổ điều khiển (3 ô tick, thêm nút, lưu/mở bộ phím...)
"""

import ctypes
import itertools
import json
import math
import os
import queue
import re
import sys
import threading
import time
import traceback
from collections import namedtuple

import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

APP_NAME = "KeyClick"
APP_VERSION = "1.7"
WINDOW_TITLE = "KeyClick – Bấm phím thay chuột"
IS_WINDOWS = sys.platform == "win32"

# ---------------------------------------------------------------------------
# Cấu hình mặc định - lưu tự động ở %APPDATA%\KeyClick\config.json
# ---------------------------------------------------------------------------
DEFAULT_CFG = {
    "return_cursor": True,      # Trả chuột về vị trí cũ sau khi click
    "show_buttons": True,       # Hiện các nút trên màn hình
    "toggle_key": 0x77,         # F8: bật/tắt nhanh (mã phím ảo Windows)
    "click_hold_ms": 40,        # thời gian giữ chuột trong 1 cú click
    "move_settle_ms": 10,       # chờ sau khi đưa chuột tới, để game kịp nhận "hover"
    "return_delay_ms": 10,      # chờ trước khi trả chuột về chỗ cũ
    "turbo_interval_ms": 100,   # chế độ turbo: 100 ms/lần = 10 click/giây
    "bg_alpha": 0.4,            # độ đậm NỀN của nút (0.05..1) - chữ trên nút luôn rõ
    "play_dim": 0.85,           # khi đang chơi, nút mờ thêm: nhân độ đậm với số này
    "button_size": 0,           # cỡ nút mới (pixel); 0 = tự chọn theo độ phân giải
    "script_key": 0x78,         # F9: chạy / dừng script đang chọn (Esc cũng dừng)
    "run_as_admin": False,      # Luôn chạy bằng quyền Admin (mở lên là tự xin quyền)
}
RELAUNCH_ARG = "--relaunched"   # đánh dấu bản vừa được mở lại bằng quyền Admin
DEFAULT_DELAY_MS = 500          # (file cũ) thời gian chờ mặc định sau mỗi nút
DEFAULT_STEP_DELAY_MS = 200     # thời gian chờ mặc định khi thêm bước mới vào script
LIST_H = 160                    # khung danh sách bước của script cao cố định (pixel ở 100%)
MAX_DELAY_MS = 3600000
CFG_LIMITS = {
    "toggle_key": (1, 254),
    "script_key": (1, 254),
    "click_hold_ms": (5, 1000),
    "move_settle_ms": (0, 500),
    "return_delay_ms": (0, 500),
    "turbo_interval_ms": (30, 5000),
    "bg_alpha": (0.05, 1.0),
    "play_dim": (0.1, 1.0),
    "button_size": (0, 320),
}
TIMING_KEYS = ("click_hold_ms", "move_settle_ms", "return_delay_ms", "turbo_interval_ms")

MOUSE_BUTTONS = ("left", "right", "middle")
MODES = ("click", "hold", "turbo", "swipe")
DEFAULT_SWIPE_MS = 200          # thời gian vuốt mặc định (từ nút tới điểm đích)
SWIPE_MS_RANGE = (30, 3000)

# ---------------------------------------------------------------------------
# Mã phím ảo (Virtual-Key) của Windows và tên hiển thị trên nút tròn
# ---------------------------------------------------------------------------
VK_ESCAPE = 0x1B
VK_F8 = 0x77
VK_F9 = 0x78
VK_PACKET = 0xE7   # ký tự Unicode do bộ gõ (Unikey...) gửi vào - bỏ qua
# Đang sửa 1 ô SỐ của KeyClick (ms, Loop): chỉ các phím này để gõ, phím khác (A, S…) vẫn click.
NUMBER_EDIT_KEYS = frozenset(list(range(0x30, 0x3A)) + list(range(0x60, 0x6A)) +
                             [0x08, 0x09, 0x0D, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2E])

_VK_NAMES = {
    0x03: "Break", 0x08: "Bksp", 0x09: "Tab", 0x0C: "Clear", 0x0D: "Enter",
    0x10: "Shift", 0x11: "Ctrl", 0x12: "Alt", 0x13: "Pause", 0x14: "Caps",
    0x1B: "Esc", 0x20: "Space", 0x21: "PgUp", 0x22: "PgDn", 0x23: "End",
    0x24: "Home", 0x25: "←", 0x26: "↑", 0x27: "→", 0x28: "↓",
    0x2C: "PrtSc", 0x2D: "Ins", 0x2E: "Del",
    0x5B: "Win", 0x5C: "RWin", 0x5D: "Menu",
    0x6A: "Num*", 0x6B: "Num+", 0x6C: "Num,", 0x6D: "Num-", 0x6E: "Num.", 0x6F: "Num/",
    0x90: "NumLk", 0x91: "ScrLk",
    0xA0: "Shift", 0xA1: "RShift", 0xA2: "Ctrl", 0xA3: "RCtrl", 0xA4: "Alt", 0xA5: "RAlt",
    0xAD: "Mute", 0xAE: "Vol-", 0xAF: "Vol+", 0xB0: "Next", 0xB1: "Prev", 0xB2: "Stop",
    0xB3: "Play",
    0xBA: ";", 0xBB: "=", 0xBC: ",", 0xBD: "-", 0xBE: ".", 0xBF: "/", 0xC0: "`",
    0xDB: "[", 0xDC: "\\", 0xDD: "]", 0xDE: "'", 0xE2: "\\",
}
for _i in range(10):
    _VK_NAMES[0x30 + _i] = str(_i)
    _VK_NAMES[0x60 + _i] = "Num" + str(_i)
for _i in range(26):
    _VK_NAMES[0x41 + _i] = chr(0x41 + _i)
for _i in range(24):
    _VK_NAMES[0x70 + _i] = "F%d" % (_i + 1)


def vk_label(vk, api=None):
    """Tên ngắn của phím để hiện trên nút tròn, ví dụ 0x41 -> 'A'."""
    if vk is None:
        return ""
    name = _VK_NAMES.get(vk)
    if name:
        return name
    if api is not None:
        try:
            n = api.key_name(vk)
            if n:
                return n[:6]
        except Exception:
            pass
    return "#%02X" % vk


# ---------------------------------------------------------------------------
# Cấu trúc dữ liệu của Windows (dùng kiểu cố định độ rộng cho đúng trên x64/x86)
# ---------------------------------------------------------------------------
_DWORD = ctypes.c_uint32
_LONG = ctypes.c_int32
_WORD = ctypes.c_uint16
_ULONG_PTR = ctypes.c_size_t


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", _DWORD), ("scanCode", _DWORD), ("flags", _DWORD),
                ("time", _DWORD), ("dwExtraInfo", _ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", _LONG), ("dy", _LONG), ("mouseData", _DWORD),
                ("dwFlags", _DWORD), ("time", _DWORD), ("dwExtraInfo", _ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", _WORD), ("wScan", _WORD), ("dwFlags", _DWORD),
                ("time", _DWORD), ("dwExtraInfo", _ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", _DWORD), ("wParamL", _WORD), ("wParamH", _WORD)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", _DWORD), ("u", _INPUTUNION)]


class POINT(ctypes.Structure):
    _fields_ = [("x", _LONG), ("y", _LONG)]


def to_absolute(x, y, vx, vy, vw, vh):
    """Đổi toạ độ pixel trên màn hình ảo sang toạ độ chuẩn hoá 0..65535 cho SendInput."""
    def conv(p, origin, size):
        rel = min(max(p - origin, 0), size - 1)
        return max(0, min(65535, (rel * 65536) // size + 1))
    return conv(x, vx, vw), conv(y, vy, vh)


# ---------------------------------------------------------------------------
# Ghi log lỗi (pythonw không có cửa sổ console)
# ---------------------------------------------------------------------------
_LOG_PATH = None
_LOG_LOCK = threading.Lock()


def log(msg):
    if not _LOG_PATH:
        return
    try:
        with _LOG_LOCK:
            if os.path.exists(_LOG_PATH) and os.path.getsize(_LOG_PATH) > 256 * 1024:
                os.replace(_LOG_PATH, _LOG_PATH + ".old")
            with open(_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg.rstrip() + "\n")
    except Exception:
        pass


def log_exc(where=""):
    log("LỖI %s\n%s" % (where, traceback.format_exc()))


def _last_error():
    fn = getattr(ctypes, "get_last_error", None)
    return fn() if fn else 0


_FUNCTYPE = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)


# ---------------------------------------------------------------------------
# Lớp gọi Windows API
# ---------------------------------------------------------------------------
class WinAPI(object):
    """Hook bàn phím toàn hệ thống, giả lập chuột, chỉnh kiểu cửa sổ - tất cả bằng ctypes."""

    is_windows = True

    WH_KEYBOARD_LL = 13
    WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP = 0x0100, 0x0101, 0x0104, 0x0105
    WM_QUIT = 0x0012
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_VIRTUALDESK = 0x4000
    MOUSEEVENTF_ABSOLUTE = 0x8000
    BUTTON_FLAGS = {
        "left": (0x0002, 0x0004),
        "right": (0x0008, 0x0010),
        "middle": (0x0020, 0x0040),
    }
    GWL_EXSTYLE = -20
    GWLP_HWNDPARENT = -8
    WS_EX_TRANSPARENT = 0x00000020   # chuột đi xuyên qua cửa sổ
    WS_EX_TOOLWINDOW = 0x00000080    # không hiện trên thanh taskbar / Alt+Tab
    WS_EX_NOACTIVATE = 0x08000000    # bấm vào không cướp focus của game
    SWP_NOSIZE, SWP_NOMOVE, SWP_NOZORDER = 0x0001, 0x0002, 0x0004
    SWP_NOACTIVATE, SWP_FRAMECHANGED = 0x0010, 0x0020
    SM_SWAPBUTTON = 23
    EXTRA_INFO = 0x4B43              # "KC": đánh dấu sự kiện chuột do KeyClick tạo
    MUTEX_NAME = "Local\\KeyClick.SingleInstance"

    def __init__(self, user32=None, kernel32=None, shell32=None, advapi32=None, set_dpi=True):
        from ctypes import wintypes
        self.wt = wintypes
        if user32 is None:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
        if kernel32 is None:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        if shell32 is None:
            shell32 = ctypes.WinDLL("shell32", use_last_error=True)
        if advapi32 is None:
            advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
        self.u, self.k, self.s, self.a = user32, kernel32, shell32, advapi32
        self._mutex = None
        self._declare()
        if set_dpi:
            self._set_dpi_awareness()

    # -- khai báo kiểu tham số cho các hàm Windows (bắt buộc trên Windows 64-bit) --
    def _declare(self):
        w, u, k, s = self.wt, self.u, self.k, self.s
        LRESULT = ctypes.c_ssize_t
        self.HOOKPROC = _FUNCTYPE(LRESULT, ctypes.c_int, w.WPARAM, w.LPARAM)

        def sig(fn, res, *args):
            fn.restype = res
            fn.argtypes = args

        sig(u.SetWindowsHookExW, w.HHOOK, ctypes.c_int, self.HOOKPROC, w.HINSTANCE, w.DWORD)
        sig(u.CallNextHookEx, LRESULT, w.HHOOK, ctypes.c_int, w.WPARAM, w.LPARAM)
        sig(u.UnhookWindowsHookEx, w.BOOL, w.HHOOK)
        sig(u.GetMessageW, w.BOOL, ctypes.POINTER(w.MSG), w.HWND, w.UINT, w.UINT)
        sig(u.TranslateMessage, w.BOOL, ctypes.POINTER(w.MSG))
        sig(u.DispatchMessageW, LRESULT, ctypes.POINTER(w.MSG))
        sig(u.PostThreadMessageW, w.BOOL, w.DWORD, w.UINT, w.WPARAM, w.LPARAM)
        sig(u.SendInput, w.UINT, w.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
        sig(u.GetCursorPos, w.BOOL, ctypes.POINTER(POINT))
        sig(u.GetSystemMetrics, ctypes.c_int, ctypes.c_int)
        sig(u.GetAsyncKeyState, ctypes.c_short, ctypes.c_int)
        sig(u.GetAncestor, w.HWND, w.HWND, w.UINT)
        sig(u.SetWindowPos, w.BOOL, w.HWND, w.HWND, ctypes.c_int, ctypes.c_int,
            ctypes.c_int, ctypes.c_int, w.UINT)
        sig(u.SetForegroundWindow, w.BOOL, w.HWND)
        sig(u.ShowWindow, w.BOOL, w.HWND, ctypes.c_int)
        sig(u.FindWindowW, w.HWND, w.LPCWSTR, w.LPCWSTR)
        sig(u.GetForegroundWindow, w.HWND)
        sig(u.GetWindowThreadProcessId, w.DWORD, w.HWND, ctypes.POINTER(w.DWORD))
        sig(u.SetTimer, ctypes.c_size_t, w.HWND, ctypes.c_size_t, w.UINT, ctypes.c_void_p)
        sig(u.KillTimer, w.BOOL, w.HWND, ctypes.c_size_t)
        sig(u.MapVirtualKeyW, w.UINT, w.UINT, w.UINT)
        sig(u.GetKeyNameTextW, ctypes.c_int, w.LONG, w.LPWSTR, ctypes.c_int)
        # Windows 32-bit không có *WindowLongPtrW -> dùng bản thường
        get_wl = getattr(u, "GetWindowLongPtrW", None) or u.GetWindowLongW
        set_wl = getattr(u, "SetWindowLongPtrW", None) or u.SetWindowLongW
        sig(get_wl, ctypes.c_ssize_t, w.HWND, ctypes.c_int)
        sig(set_wl, ctypes.c_ssize_t, w.HWND, ctypes.c_int, ctypes.c_ssize_t)
        self._get_wl, self._set_wl = get_wl, set_wl
        sig(k.GetModuleHandleW, w.HMODULE, w.LPCWSTR)
        sig(k.GetCurrentThreadId, w.DWORD)
        sig(k.CreateMutexW, w.HANDLE, ctypes.c_void_p, w.BOOL, w.LPCWSTR)
        sig(k.CloseHandle, w.BOOL, w.HANDLE)
        sig(k.OpenProcess, w.HANDLE, w.DWORD, w.BOOL, w.DWORD)
        sig(s.ShellExecuteW, ctypes.c_void_p, w.HWND, w.LPCWSTR, w.LPCWSTR, w.LPCWSTR,
            w.LPCWSTR, ctypes.c_int)
        sig(s.IsUserAnAdmin, w.BOOL)
        a = self.a
        sig(a.OpenProcessToken, w.BOOL, w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE))
        sig(a.GetTokenInformation, w.BOOL, w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD,
            ctypes.POINTER(w.DWORD))

    def _set_dpi_awareness(self):
        """Báo cho Windows biết app tự lo DPI -> mọi toạ độ là pixel thật (click chính xác
        cả khi màn hình đặt Scale 125%/150% hoặc dùng nhiều màn hình)."""
        try:
            fn = self.u.SetProcessDpiAwarenessContext
            fn.restype = self.wt.BOOL
            fn.argtypes = (ctypes.c_void_p,)
            if fn(ctypes.c_void_p(-4)):  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
                return
        except Exception:
            pass
        try:
            if ctypes.WinDLL("shcore").SetProcessDpiAwareness(2) == 0:
                return
        except Exception:
            pass
        try:
            self.u.SetProcessDPIAware()
        except Exception:
            pass

    # -- bàn phím --
    def start_keyboard_hook(self, handler):
        hook = _KeyboardHookThread(self, handler)
        hook.start()
        hook.ready.wait(3.0)
        return hook

    def async_down(self, vk):
        return bool(self.u.GetAsyncKeyState(vk) & 0x8000)

    def key_name(self, vk):
        sc = self.u.MapVirtualKeyW(vk, 0)  # MAPVK_VK_TO_VSC
        if not sc:
            return None
        buf = ctypes.create_unicode_buffer(64)
        n = self.u.GetKeyNameTextW(sc << 16, buf, 64)
        return buf.value if n > 0 else None

    # -- chuột --
    def virtual_screen(self):
        g = self.u.GetSystemMetrics
        return g(76), g(77), max(1, g(78)), max(1, g(79))

    def _mouse_input(self, flags, dx=0, dy=0):
        inp = INPUT()
        inp.type = 0  # INPUT_MOUSE
        inp.mi.dx = dx
        inp.mi.dy = dy
        inp.mi.dwFlags = flags
        inp.mi.dwExtraInfo = self.EXTRA_INFO
        return inp

    def _move_input(self, x, y):
        vx, vy, vw, vh = self.virtual_screen()
        nx, ny = to_absolute(x, y, vx, vy, vw, vh)
        flags = self.MOUSEEVENTF_MOVE | self.MOUSEEVENTF_ABSOLUTE | self.MOUSEEVENTF_VIRTUALDESK
        return self._mouse_input(flags, nx, ny)

    def _send(self, inputs):
        n = len(inputs)
        arr = (INPUT * n)(*inputs)
        return self.u.SendInput(n, arr, ctypes.sizeof(INPUT))

    def move(self, x, y):
        self._send([self._move_input(x, y)])

    def button(self, button, down, at=None):
        """Nhấn/thả chuột. Nếu có `at`, di chuột tới đó NGAY TRONG CÙNG 1 lệnh SendInput
        (không bị chuột thật chen vào giữa)."""
        if button in ("left", "right") and self.u.GetSystemMetrics(self.SM_SWAPBUTTON):
            button = "right" if button == "left" else "left"   # người dùng đổi nút chuột
        flag = self.BUTTON_FLAGS.get(button, self.BUTTON_FLAGS["left"])[0 if down else 1]
        events = []
        if at is not None:
            events.append(self._move_input(at[0], at[1]))
        events.append(self._mouse_input(flag))
        self._send(events)

    def get_cursor(self):
        p = POINT()
        if self.u.GetCursorPos(ctypes.byref(p)):
            return (p.x, p.y)
        return None

    # -- cửa sổ --
    def toplevel_hwnd(self, tkwin):
        tkwin.update_idletasks()
        try:
            h = int(tkwin.wm_frame(), 16)
        except Exception:
            h = tkwin.winfo_id()
        try:
            root = self.u.GetAncestor(h, 2)  # GA_ROOT
            if root:
                return root
        except Exception:
            pass
        return h

    def set_window_style(self, hwnd, click_through):
        if not hwnd:
            return
        old = self._get_wl(hwnd, self.GWL_EXSTYLE)
        new = old | self.WS_EX_NOACTIVATE | self.WS_EX_TOOLWINDOW
        if click_through:
            new |= self.WS_EX_TRANSPARENT
        else:
            new &= ~self.WS_EX_TRANSPARENT
        if new != old:
            self._set_wl(hwnd, self.GWL_EXSTYLE, new)
            self.u.SetWindowPos(hwnd, None, 0, 0, 0, 0,
                                self.SWP_NOMOVE | self.SWP_NOSIZE | self.SWP_NOZORDER
                                | self.SWP_NOACTIVATE | self.SWP_FRAMECHANGED)

    def set_topmost(self, hwnd):
        if hwnd:
            self.u.SetWindowPos(hwnd, ctypes.c_void_p(-1), 0, 0, 0, 0,  # HWND_TOPMOST
                                self.SWP_NOMOVE | self.SWP_NOSIZE | self.SWP_NOACTIVATE)

    def set_owner(self, hwnd, owner):
        """Cho hwnd "thuộc về" owner: Windows luôn giữ hwnd nằm ngay trên owner."""
        if hwnd and owner:
            self._set_wl(hwnd, self.GWLP_HWNDPARENT, owner)

    def force_foreground(self, hwnd):
        if hwnd:
            self.u.SetForegroundWindow(hwnd)

    # -- quyền Admin, chỉ chạy 1 bản --
    def is_admin(self):
        try:
            return bool(self.s.IsUserAnAdmin())
        except Exception:
            return True

    def relaunch_as_admin(self):
        """Mở lại KeyClick bằng quyền Admin (Windows hỏi UAC). True = đã mở được."""
        if getattr(sys, "frozen", False):          # đang chạy file .exe
            exe, params = sys.executable, RELAUNCH_ARG
            here = os.path.dirname(os.path.abspath(sys.executable))
        else:                                      # đang chạy file .pyw
            exe = sys.executable
            pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
            if os.path.exists(pyw):
                exe = pyw
            script = os.path.abspath(sys.argv[0])
            params = '"%s" %s' % (script, RELAUNCH_ARG)
            here = os.path.dirname(script)
        r = self.s.ShellExecuteW(None, "runas", exe, params, here, 1)
        return (r or 0) > 32

    def acquire_single_instance(self):
        h = self.k.CreateMutexW(None, False, self.MUTEX_NAME)
        err = _last_error()
        if h and err != 183:            # 183 = ERROR_ALREADY_EXISTS
            self._mutex = h
            return True
        if h:
            self.k.CloseHandle(h)
            return False
        return err != 5                 # 5 = bản đang chạy là bản Admin

    def release_single_instance(self):
        if self._mutex:
            self.k.CloseHandle(self._mutex)
            self._mutex = None

    def bring_existing_to_front(self, title):
        hwnd = self.u.FindWindowW(None, title)
        if not hwnd:
            return False
        self.u.ShowWindow(hwnd, 9)  # SW_RESTORE
        self.u.SetForegroundWindow(hwnd)
        return True

    def foreground_window(self):
        """(hwnd, pid) của cửa sổ đang được chọn."""
        hwnd = self.u.GetForegroundWindow()
        if not hwnd:
            return None, 0
        pid = self.wt.DWORD()
        self.u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return hwnd, pid.value

    def foreground_is_mine(self):
        """Cửa sổ đang được chọn có phải của KeyClick không (đang gõ tên, số ms...)."""
        hwnd, pid = self.foreground_window()
        return bool(hwnd) and pid == os.getpid()

    def process_elevated(self, pid):
        """True nếu tiến trình đang chạy quyền Admin (hoặc được bảo vệ, không xem được).
        Khi đó Windows chặn KeyClick (chưa chạy Admin) nhận phím / click vào cửa sổ đó."""
        if not pid or pid == os.getpid():
            return False
        h = self.k.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return _last_error() == 5                 # bị từ chối
        try:
            tok = self.wt.HANDLE()
            if not self.a.OpenProcessToken(h, 0x0008, ctypes.byref(tok)):   # TOKEN_QUERY
                return _last_error() == 5
            try:
                elev, size = self.wt.DWORD(), self.wt.DWORD()
                if self.a.GetTokenInformation(tok, 20, ctypes.byref(elev), 4,  # TokenElevation
                                              ctypes.byref(size)):
                    return bool(elev.value)
                return False
            finally:
                self.k.CloseHandle(tok)
        finally:
            self.k.CloseHandle(h)


class _KeyboardHookThread(threading.Thread):
    """Luồng riêng: cài WH_KEYBOARD_LL và chạy vòng lặp message của Windows.
    Để riêng một luồng giúp phím không bị khựng khi giao diện đang bận.

    Tự hồi phục: Windows có thể âm thầm gỡ hook khi máy bận (vd lúc phóng to game nặng),
    và app khác cài hook sau sẽ được nhận phím trước KeyClick. Vì vậy cứ mỗi lần đổi
    cửa sổ đang chọn, và định kỳ vài giây, hook được cài lại (cài mới trước, gỡ cũ sau)."""

    WM_TIMER = 0x0113
    TICK_MS = 500
    REHOOK_TICKS = 10        # cài lại định kỳ: 10 x 500 ms = 5 giây

    def __init__(self, api, handler):
        threading.Thread.__init__(self, name="KeyClick-hook")
        self.daemon = True
        self.api = api
        self.handler = handler
        self.ready = threading.Event()
        self.error = None
        self.thread_id = None
        self.rehooks = 0
        self._proc = None

    def run(self):
        api = self.api
        u, k = api.u, api.k
        handler = self.handler
        from_address = KBDLLHOOKSTRUCT.from_address
        downs = (api.WM_KEYDOWN, api.WM_SYSKEYDOWN)
        ups = (api.WM_KEYUP, api.WM_SYSKEYUP)

        def proc(n_code, w_param, l_param):
            if n_code == 0:  # HC_ACTION
                try:
                    if w_param in downs:
                        kb = from_address(l_param)
                        if handler(kb.vkCode, True, kb.flags):
                            return 1   # "nuốt" phím: game không nhận được
                    elif w_param in ups:
                        kb = from_address(l_param)
                        if handler(kb.vkCode, False, kb.flags):
                            return 1
                except Exception:
                    log_exc("hook")
            return u.CallNextHookEx(None, n_code, w_param, l_param)

        self._proc = api.HOOKPROC(proc)  # giữ tham chiếu, tránh bị dọn rác

        def install():
            return u.SetWindowsHookExW(api.WH_KEYBOARD_LL, self._proc, k.GetModuleHandleW(None), 0)

        hook = None
        try:
            self.thread_id = k.GetCurrentThreadId()
            hook = install()
        except Exception as e:
            self.error = str(e)
        if not hook:
            self.error = self.error or ("SetWindowsHookEx lỗi %d" % _last_error())
            self.ready.set()
            return
        self.ready.set()
        timer = 0
        try:
            timer = u.SetTimer(None, 0, self.TICK_MS, None)   # WM_TIMER gửi về luồng này
        except Exception:
            log_exc("SetTimer")
        last_fg, ticks = None, 0
        msg = api.wt.MSG()
        try:
            while True:
                r = u.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if r == 0 or r == -1:
                    break
                if msg.message == self.WM_TIMER and not msg.hWnd:
                    ticks += 1
                    try:
                        fg = u.GetForegroundWindow()
                    except Exception:
                        fg = last_fg
                    if fg != last_fg or ticks >= self.REHOOK_TICKS:
                        last_fg, ticks = fg, 0
                        try:
                            new = install()               # cài hook mới (đứng đầu hàng)
                        except Exception:
                            new = None
                        if new:
                            u.UnhookWindowsHookEx(hook)   # rồi mới gỡ hook cũ
                            hook = new
                            self.rehooks += 1
                    continue
                u.TranslateMessage(ctypes.byref(msg))
                u.DispatchMessageW(ctypes.byref(msg))
        finally:
            if timer:
                try:
                    u.KillTimer(None, timer)
                except Exception:
                    pass
            u.UnhookWindowsHookEx(hook)

    def stop(self):
        if self.thread_id:
            try:
                self.api.u.PostThreadMessageW(self.thread_id, self.api.WM_QUIT, 0, 0)
            except Exception:
                pass


class _NullHook(object):
    error = None

    def stop(self):
        pass


class FakeAPI(object):
    """Dùng khi KHÔNG chạy trên Windows (để thử giao diện / kiểm thử):
    không click thật, chỉ ghi lại các thao tác chuột."""

    is_windows = False

    def __init__(self):
        self.events = []
        self.cursor = (10, 10)
        self.styles = {}
        self.owners = {}
        self.handler = None
        self.fg_mine = False             # giả lập: cửa sổ KeyClick đang được chọn
        self.fg_pid = 0                  # giả lập: tiến trình của cửa sổ đang chọn
        self.elevated_pids = set()       # giả lập: tiến trình chạy quyền Admin
        self._lock = threading.Lock()

    def start_keyboard_hook(self, handler):
        self.handler = handler
        return _NullHook()

    def async_down(self, vk):
        return True

    def foreground_is_mine(self):
        return self.fg_mine

    def foreground_window(self):
        return (1, self.fg_pid) if self.fg_pid else (None, 0)

    def process_elevated(self, pid):
        return pid in self.elevated_pids

    def key_name(self, vk):
        return None

    def virtual_screen(self):
        return None

    def move(self, x, y):
        with self._lock:
            self.events.append(("move", x, y))
            self.cursor = (x, y)

    def button(self, button, down, at=None):
        with self._lock:
            if at is not None:
                self.events.append(("move", at[0], at[1]))
                self.cursor = (at[0], at[1])
            self.events.append(("down" if down else "up", button))

    def get_cursor(self):
        return self.cursor

    def toplevel_hwnd(self, tkwin):
        return id(tkwin)

    def set_window_style(self, hwnd, click_through):
        self.styles[hwnd] = click_through

    def set_topmost(self, hwnd):
        pass

    def set_owner(self, hwnd, owner):
        self.owners[hwnd] = owner

    def force_foreground(self, hwnd):
        pass

    def is_admin(self):
        return True

    def relaunch_as_admin(self):
        return False

    def acquire_single_instance(self):
        return True

    def release_single_instance(self):
        pass

    def bring_existing_to_front(self, title):
        return False


# ---------------------------------------------------------------------------
# Bộ não: phím -> click
# ---------------------------------------------------------------------------
# x2, y2, dur: chỉ dùng cho nút vuốt (điểm đích + thời gian vuốt ms)
Target = namedtuple("Target", "cid x y button mode x2 y2 dur", defaults=(None, None, 0))


class ClickEngine(object):
    """on_key() chạy trong luồng hook: phải trả lời thật nhanh (nuốt phím hay không).
    Việc click (có chờ vài ms) được đẩy sang luồng worker để bàn phím không bị lag."""

    def __init__(self, api, ui_queue, cfg=None):
        self.api = api
        self.ui_queue = ui_queue
        cfg = cfg or DEFAULT_CFG
        self.enabled = False
        self.return_cursor = bool(cfg.get("return_cursor", True))
        self.toggle_vk = int(cfg.get("toggle_key", VK_F8))
        self.script_vk = int(cfg.get("script_key", VK_F9))
        self.script_running = False     # luồng hook đọc cờ này để Esc dừng script
        self.typing = None              # đang gõ trong KeyClick: "text" (ô Tên), "number" (ô số)
        self.capture_id = None          # đang chờ gán phím cho: ("circle", id) / ("script", id)
        self.timing = dict((k, int(cfg.get(k, DEFAULT_CFG[k]))) for k in TIMING_KEYS)
        self._map = {}                  # vk -> Target
        self._script_keys = {}          # vk -> (id script, các bước, số vòng)
        self._held = {}                 # vk -> lý do đã nuốt phím (chỉ luồng hook dùng)
        self._down = set()              # phím đang được giữ (để nhận ra phím tự lặp)
        self._q = queue.Queue()
        self._active = None             # ("hold"|"turbo", vk, Target) đang chạy
        self._origin = None             # vị trí chuột trước khi click
        self._next_tick = 0.0
        self._scripts = {}              # id -> trạng thái các script đang chạy (luồng worker)
        self._script_hold = None        # (id script, Target) đang được script giữ chuột
        self._locked = frozenset()      # phím bị khoá (không bấm tay) khi combo đang chạy
        self._worker = threading.Thread(target=self._run, name="KeyClick-worker")
        self._worker.daemon = True
        self._worker.start()

    # ---- gọi từ giao diện ----
    def set_mappings(self, mapping):
        self._map = dict(mapping)       # thay nguyên dict -> an toàn giữa các luồng

    def set_script_keys(self, mapping):
        """mapping: {phím: (id script, [(Target, chờ ms), ...], số vòng hoặc None,
        các phím khoá khi chạy)}"""
        self._script_keys = dict(mapping)

    def set_script_lock(self, sid, keys):
        """Đổi ô "khoá phím" lúc script sid đang chạy (luồng worker tự kiểm tra sid)."""
        self._q.put(("lock", sid, frozenset(keys)))

    def set_timing(self, **kw):
        t = dict(self.timing)
        t.update(kw)
        self.timing = t

    def release_all(self):
        self._q.put(("release",))

    def start_script(self, sid, steps, loops, lock=frozenset()):
        """Chạy thêm 1 script (các script khác đang chạy vẫn chạy tiếp).
        steps: [(Target, thời gian chờ ms), ...]; loops: số vòng, None = lặp vĩnh viễn;
        lock: các phím không cho bấm tay trong lúc script này chạy."""
        self.script_running = True       # để Esc dừng được ngay
        self._q.put(("script_start", sid, list(steps), loops, frozenset(lock)))

    def stop_script(self, sid=None):
        """Dừng 1 script (sid) hoặc tất cả (None)."""
        self._q.put(("script_stop", sid))

    def stop(self):
        self._q.put(("stop",))
        self._worker.join(1.0)

    # ---- gọi từ luồng hook bàn phím: trả về True = nuốt phím ----
    def on_key(self, vk, down, flags=0):
        if vk <= 0 or vk >= 0xFF or vk == VK_PACKET:
            return False
        if not down:
            self._down.discard(vk)
            kind = self._held.pop(vk, None)
            if kind == "action":
                self._q.put(("up", vk))
            return kind is not None      # chỉ nuốt phím-thả nếu đã nuốt phím-nhấn

        if vk in self._held:             # phím tự lặp khi giữ, trước đó đã nuốt
            return True
        repeat = vk in self._down and self.api.async_down(vk)
        self._down.add(vk)
        if repeat:                       # phím tự lặp của phím không nuốt -> cho qua
            return False

        if vk == self.toggle_vk:         # F8: bật/tắt nhanh
            self._held[vk] = "toggle"
            self.ui_queue.put(("toggle",))
            return True

        if vk == self.script_vk:         # F9: chạy / dừng script
            self._held[vk] = "script"
            self.ui_queue.put(("script_toggle",))
            return True

        if vk == VK_ESCAPE and self.script_running:   # Esc: dừng script đang chạy
            self._held[vk] = "script"
            self._q.put(("script_stop",))
            return True

        cid = self.capture_id
        if cid is not None:              # đang có nút tròn chờ gán phím
            self.capture_id = None
            self._held[vk] = "capture"
            self.ui_queue.put(("captured", cid, vk))
            return True

        if self.enabled:
            # Chỉ để phím đi qua khi đang GÕ trong 1 ô nhập của KeyClick: ô Tên = mọi phím,
            # ô số (ms, Loop) = chỉ phím số. Còn lại — cửa sổ KeyClick ở trước (vừa đổi tab,
            # bấm nút…) hay game/ứng dụng khác đang mở to phía trước — phím vẫn click.
            typing = self.typing
            if (typing and (typing == "text" or vk in NUMBER_EDIT_KEYS)
                    and self.api.foreground_is_mine()):
                return False
            t = self._map.get(vk)
            if t is not None:
                if vk in self._locked and self.script_running:   # combo đang chạy: khoá
                    self._held[vk] = "locked"                   # nuốt luôn, không click
                    self.ui_queue.put(("locked", t.cid))
                    return True
                self._held[vk] = "action"
                self._q.put(("down", vk, t))
                self.ui_queue.put(("flash", t.cid))
                return True
            sk = self._script_keys.get(vk)
            if sk is not None:               # phím chạy script / combo
                self._held[vk] = "script"
                self.script_running = True   # để Esc dừng được ngay
                self._q.put(("script_key",) + tuple(sk))
                return True
        return False

    # ---- luồng worker: thực hiện click (phím bấm tay + script) ----
    def _run(self):
        while True:
            try:
                ev = self._q.get(timeout=self._time_to_next())
            except queue.Empty:
                ev = None
            try:
                if ev is not None:
                    kind = ev[0]
                    if kind == "down":
                        self._on_down(ev[1], ev[2])
                    elif kind == "up":
                        self._on_up(ev[1])
                    elif kind == "release":
                        self._finish_active(restore=True)
                    elif kind == "script_start":
                        self._script_begin(*ev[1:])
                    elif kind == "script_key":
                        self._on_script_key(*ev[1:])
                    elif kind == "script_stop":
                        self._script_finish("stopped", ev[1] if len(ev) > 1 else None)
                    elif kind == "lock":
                        s = self._scripts.get(ev[1])
                        if s is not None:
                            s["lock"] = ev[2]
                            self._update_running()
                    elif kind == "stop":
                        self._script_finish("stopped")
                        self._finish_active(restore=True)
                        self._q.task_done()
                        return
                self._run_due()
            except Exception:
                log_exc("worker")
                self._reset_after_error()
            if ev is not None:
                self._q.task_done()

    def _time_to_next(self):
        """Còn bao lâu tới việc hẹn giờ kế tiếp (turbo / bước script). None = không có."""
        t = None
        if self._active is not None and self._active[0] == "turbo":
            t = self._next_tick
        if self._scripts and self._active is None:      # đang giữ phím tay: script đợi
            nxt = min(sc["next"] for sc in self._scripts.values())
            t = nxt if t is None else min(t, nxt)
        return None if t is None else max(0.0, t - time.perf_counter())

    def _run_due(self):
        if (self._active is not None and self._active[0] == "turbo"
                and time.perf_counter() >= self._next_tick):
            self._turbo_tick()
        # Các script đang chạy cùng lúc: tới lượt script nào thì chạy bước của script đó
        # (chỉ 1 con chuột nên các cú click được xếp lần lượt).
        for sc in sorted(self._scripts.values(), key=lambda x: x["next"]):
            if self._active is not None:
                break
            if self._scripts.get(sc["sid"]) is sc and time.perf_counter() >= sc["next"]:
                self._script_tick(sc)

    def _reset_after_error(self):
        """Lỗi bất ngờ: nhả chuột, huỷ script để không bị lặp lỗi liên tục."""
        held = self._script_hold[1] if self._script_hold else None
        for t in (held, self._active[2] if self._active else None):
            if t is not None:
                try:
                    self.api.button(t.button, False)
                except Exception:
                    pass
        self._active = None
        self._script_hold = None
        had = bool(self._scripts) or self.script_running
        self._scripts = {}
        self._update_running()
        if had:
            self.ui_queue.put(("script_done", None, "error", 0))

    @staticmethod
    def _sleep_ms(ms):
        if ms > 0:
            time.sleep(ms / 1000.0)

    def _press(self, t):
        settle = self.timing["move_settle_ms"]
        if settle > 0:
            self.api.move(t.x, t.y)
            self._sleep_ms(settle)
        self.api.button(t.button, True, (t.x, t.y))

    def _click(self, t, hold_ms=None):
        self._press(t)
        self._sleep_ms(self.timing["click_hold_ms"] if hold_ms is None else hold_ms)
        self.api.button(t.button, False, (t.x, t.y))

    def _restore(self):
        origin, self._origin = self._origin, None
        if origin is not None and self.return_cursor:
            self._sleep_ms(self.timing["return_delay_ms"])
            self.api.move(origin[0], origin[1])

    def _on_down(self, vk, t):
        self._release_script_hold()       # script đang giữ chuột -> nhả ra trước
        if self._active is not None:     # đang giữ/turbo nút khác -> nhả nút đó trước
            self._finish_active(restore=False)
        if self._origin is None:
            self._origin = self.api.get_cursor()
        if t.mode == "hold":             # giữ phím = giữ chuột (kéo, ngắm skill...)
            self._press(t)
            self._active = ("hold", vk, t)
        elif t.mode == "turbo":          # giữ phím = click liên tục
            self._active = ("turbo", vk, t)
            self._next_tick = time.perf_counter()
            self._turbo_tick()
        elif t.mode == "swipe":          # vuốt từ nút tới điểm đích B
            self._swipe(t)
            if self._held.get(vk) == "action":   # phím vẫn đang giữ -> giữ chuột ở B
                self._active = ("swipe", vk, t)
            else:                                # nhấp nhanh -> thả luôn ở B
                self.api.button(t.button, False, (t.x2, t.y2))
                self._restore()
        else:                            # nhấn phím = click 1 lần
            self._click(t)
            self._restore()

    def _on_up(self, vk):
        if self._active is not None and self._active[1] == vk:
            self._finish_active(restore=True)

    def _finish_active(self, restore):
        active, self._active = self._active, None
        if active is not None and active[0] in ("hold", "swipe"):
            self.api.button(active[2].button, False)
        if restore:
            self._restore()

    def _swipe(self, t):
        """Nhấn chuột ở nút (A) rồi kéo mượt tới điểm đích B trong t.dur ms (chưa thả)."""
        self._press(t)
        if t.x2 is None or t.y2 is None:
            return
        dur = max(SWIPE_MS_RANGE[0], min(SWIPE_MS_RANGE[1], t.dur or DEFAULT_SWIPE_MS))
        steps = max(4, int(dur / 10))            # ~100 lần di chuột mỗi giây
        t0 = time.perf_counter()
        for i in range(1, steps + 1):
            f = i / float(steps)
            self.api.move(int(round(t.x + (t.x2 - t.x) * f)), int(round(t.y + (t.y2 - t.y) * f)))
            left = t0 + dur / 1000.0 * f - time.perf_counter()
            if left > 0:
                time.sleep(left)

    def _turbo_tick(self):
        a = self._active
        if a is None or a[0] != "turbo":
            return
        interval = max(30, self.timing["turbo_interval_ms"])
        self._click(a[2], hold_ms=min(self.timing["click_hold_ms"], interval // 2))
        self._next_tick = max(self._next_tick + interval / 1000.0, time.perf_counter() + 0.005)

    # ---- script: chạy lần lượt các nút, chờ giữa các nút, lặp N lần / vĩnh viễn ----
    #  Mỗi bước: nút "click" -> click 1 lần rồi chờ; nút "giữ" -> giữ chuột suốt thời gian
    #  chờ; nút "turbo" -> click liên tục suốt thời gian chờ. Thời gian chờ tính từ lúc
    #  bắt đầu bước, nên nhịp chạy đều (vd chờ 500 ms = mỗi 0,5 giây 1 nút).
    #  Nhiều script chạy CÙNG LÚC được (vd 2–4 combo): mỗi script có lịch riêng, các cú
    #  click được xếp lần lượt vì chỉ có 1 con chuột. Bước cuối của lần chạy cuối không chờ.
    def _on_script_key(self, sid, steps, loops, lock=frozenset()):
        """Nhấn phím chạy của 1 script (khi đang BẬT phím tắt). Script khác vẫn chạy tiếp."""
        sc = self._scripts.get(sid)
        if sc is not None:
            if sc["loops"] != 1:               # script có lặp: nhấn lại = dừng
                self._script_finish("stopped", sid)
            else:                               # combo 1 lần: cứ để chạy hết
                self._update_running()
            return
        self._script_begin(sid, steps, loops, lock)

    def _script_begin(self, sid, steps, loops, lock=frozenset()):
        if sid in self._scripts:
            self._script_finish("stopped", sid)
        if not steps:
            self._update_running()
            self.ui_queue.put(("script_done", sid, "empty", 0))
            return
        self._scripts[sid] = {"sid": sid, "steps": steps, "loops": loops, "i": 0, "done": 0,
                              "phase": "start", "next": time.perf_counter(), "end": 0.0,
                              "lock": frozenset(lock)}
        self._update_running()
        self.ui_queue.put(("script_started", sid, loops))
        self.ui_queue.put(("script_progress", sid, 1, loops))

    def _update_running(self):
        """Báo cho luồng hook: còn script nào chạy không, phím nào đang bị khoá."""
        locked = frozenset()
        for sc in self._scripts.values():
            locked = locked | sc["lock"]
        self._locked = locked
        self.script_running = bool(self._scripts)

    def _release_script_hold(self, keep_sid=None):
        """Nhả chuột mà 1 script đang giữ (vì phím tay / script khác cần click chỗ khác)."""
        h = self._script_hold
        if h is None or h[0] == keep_sid:
            return
        self.api.button(h[1].button, False)
        self._script_hold = None
        sc = self._scripts.get(h[0])
        if sc is not None and sc["phase"] == "hold":
            sc["phase"] = "wait"                # vẫn đợi hết thời gian của bước đó

    @staticmethod
    def _script_is_last_step(sc):
        return (sc["i"] == len(sc["steps"]) - 1 and sc["loops"] is not None
                and sc["done"] + 1 >= sc["loops"])

    def _script_release(self, sc):
        """Script dừng: nhả chuột nếu nó đang giữ, rồi trả chuột về chỗ cũ."""
        h = self._script_hold
        if h is not None and h[0] == sc["sid"]:
            self.api.button(h[1].button, False)
            self._script_hold = None
            self._restore()
        elif sc["phase"] == "turbo":
            self._restore()

    def _script_finish(self, reason, sid=None):
        """Dừng script sid, hoặc tất cả script đang chạy (sid=None)."""
        sids = list(self._scripts) if sid is None else [sid]
        stopped = 0
        for x in sids:
            sc = self._scripts.pop(x, None)
            if sc is None:
                continue
            stopped += 1
            self._script_release(sc)
            self.ui_queue.put(("script_done", x, reason, sc["done"]))
        was_running = self.script_running
        self._update_running()
        if sid is None and not stopped and was_running:   # bị dừng trước khi kịp bắt đầu
            self.ui_queue.put(("script_done", None, reason, 0))

    def _script_tick(self, sc):
        t, delay = sc["steps"][sc["i"]]
        now = time.perf_counter()
        wait = max(0, delay) / 1000.0
        phase = sc["phase"]
        if phase == "start":                     # bắt đầu 1 bước
            self._release_script_hold()          # script khác đang giữ chuột -> nhả ra
            self.ui_queue.put(("flash", t.cid))
            if self._origin is None:
                self._origin = self.api.get_cursor()
            if t.mode == "hold":                 # giữ chuột suốt thời gian chờ
                self._press(t)
                self._script_hold = (sc["sid"], t)
                sc["phase"], sc["next"] = "hold", now + wait
            elif t.mode == "turbo":              # click liên tục suốt thời gian chờ
                sc["phase"], sc["end"] = "turbo", now + wait
                self._script_turbo_click(sc, t)
            elif t.mode == "swipe":              # vuốt A -> B rồi thả, sau đó chờ
                self._swipe(t)
                self.api.button(t.button, False, (t.x2, t.y2) if t.x2 is not None else None)
                self._restore()
                sc["phase"] = "wait"
                sc["next"] = now if self._script_is_last_step(sc) else now + wait
            else:                                # click 1 lần rồi chờ
                self._click(t)
                self._restore()
                sc["phase"] = "wait"
                sc["next"] = now if self._script_is_last_step(sc) else now + wait
        elif phase == "hold":
            h = self._script_hold
            if h is not None and h[0] == sc["sid"]:
                self.api.button(h[1].button, False)
                self._script_hold = None
                self._restore()
            self._script_next_step(sc)
        elif phase == "turbo":
            if now >= sc["end"]:
                self._restore()
                self._script_next_step(sc)
            else:
                self._script_turbo_click(sc, t)
        else:                                    # "wait": hết giờ chờ -> sang nút tiếp theo
            self._script_next_step(sc)

    def _script_turbo_click(self, sc, t):
        self._release_script_hold()
        interval = max(30, self.timing["turbo_interval_ms"])
        self._click(t, hold_ms=min(self.timing["click_hold_ms"], interval // 2))
        sc["next"] = min(time.perf_counter() + interval / 1000.0, sc["end"])

    def _script_next_step(self, sc):
        sc["i"] += 1
        if sc["i"] >= len(sc["steps"]):          # xong 1 vòng
            sc["i"] = 0
            sc["done"] += 1
            if sc["loops"] is not None and sc["done"] >= sc["loops"]:
                self._script_finish("done", sc["sid"])
                return
            self.ui_queue.put(("script_progress", sc["sid"], sc["done"] + 1, sc["loops"]))
        sc["phase"], sc["next"] = "start", time.perf_counter()


# ---------------------------------------------------------------------------
# Giao diện
# ---------------------------------------------------------------------------
THEME = {
    "key": "#ff00ff",         # màu "trong suốt" của lớp nền (Windows đục lỗ chỗ màu này)
    "key_text": "#010101",    # màu "trong suốt" của lớp chữ
    "fill": "#0f172a",        # nền nút bình thường
    "fill_hover": "#334155",  # nền khi rê chuột vào (lúc đang chỉnh)
    "fill_edit": "#a16207",   # nền vàng sẫm = đang chờ gán phím
    "text_left": "#ffffff",   # chữ trắng = click chuột trái
    "text_right": "#fdba74",  # chữ cam = click chuột phải
    "text_middle": "#c4b5fd", # chữ tím = click chuột giữa
    "muted": "#cbd5e1",
    "outline": "#000000",     # viền đen quanh chữ để đọc được trên mọi nền game
    "caret": "#facc15",
    "left": "#38bdf8",        # màu nháy sáng khi bấm phím
    "right": "#fb923c",
    "middle": "#a78bfa",
    "warn": "#f87171",
}
FONT_UI = "Segoe UI" if IS_WINDOWS else "DejaVu Sans"
MODE_TAGS = {"hold": "GIỮ", "turbo": "TURBO", "swipe": "VUỐT"}
RESIZE_CURSORS = ("size_nw_se", "size_ne_sw") if IS_WINDOWS else ("sizing", "sizing")


def _outlined_text(canvas, x, y, text, color, font, width=1):
    """Vẽ chữ có viền đen mỏng (đọc rõ cả trên nền sáng lẫn tối)."""
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx or dy:
                canvas.create_text(x + dx, y + dy, text=text, fill=THEME["outline"], font=font)
    canvas.create_text(x, y, text=text, fill=color, font=font)

ICON_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAANTElEQVR42uWae5BcxXXGf6f7vmZ2"
    "V7tC0hqZCARGAWRQgUUAEWD1AEw5AUHIKtgEqBRVKYpAMC4wYMCSAiRSwKGweIkYu3gKaxHPJCYY"
    "PZaiENioHAsQ2LwEAiQkEe1KuzN35t7ukz/u7KInYrFiU8mturVTO3e6v6/769PfOX1hD1wzVU3H"
    "Ug06Ve3unu1UtR1LNZipavZE3/K5f6kqHcuw3VMk3/6rE1/S1iq0am+tBCCtcbUEvc8cKb3bP9ux"
    "VIPuyThE9PdDQFU6wXSJuIF/HbdcJzjvJkuuk1TdePUyGnQYStzopQayWYyuFbGrNJDl1thlz02S"
    "lVvPTBf4oRIZEoHOhWq7ZhTA/+RFHRFm7luqnK25OypoikQVNAPNHeodqG/0YhBjkcAiIYhA3l9X"
    "CewvRHggC+2DvzxaPt6+jz1KYKDhCf+5tqmledTF3nGRTew+PgNfTVHvc1AQMSJGsAFiiubVK7gc"
    "Va+oehDEmMCUEkwILnUfGMutW956Zd7Kcw/vBwLoALodoL8bAVVhFsJs8cd2Zydj5WYT2/Gu4vH1"
    "1KFexATGJAkSgrqCkK/04es1AEwUY8rNmFKC2GKWfJqiPveIURMl1iYGhVWjJnDpv7XapzX3uGIC"
    "DeA/HwFVGdDksc+667ByDSq4aprjnZUwEtsU4isZlTdXUnn5RSq/XUn9o/dwW3rRBgGJYmxLK9GX"
    "9qX8xxMoH3Y05QMnYMohrpLhazUNW5tdbeOm4P2f/4x1D99/Nx9++BytLY9L73Ob9FNIyO7Adyx9"
    "J6kHY+4NSrYz6029eo+IGNtcIu/dTM/SR9m05FHSt1bh00pD6yFYi4hpNOXBOTTPUO8wSZnkK+MZ"
    "PvUMWjtOJxndytr/eJrK3Zf7syatMQce0sKrb8Y88FT0zqae4Cyp/voXuyIhnyabjsmro7rZ5wnb"
    "FJ6U99Qy9S40UYREAT1LHmP9g/NI3/0NEsaYpIQYAwqquhPpCiICAuo9Pq2i9ZTyuENpntqJf+p2"
    "Hp/1DhOOjqGWOxL1i5c0hZ1XtXzQFAyb8P77L2waQLcbAiqdWoTJY5bWHg5aojPznjRT70NbKuH6"
    "e/jg9pn0LHkUEyWYpFyMsPdDC8fGIGIwWYX/3lDnX66CS/+2St9asLZorunLLvv72SPCeT+256m+"
    "dp/IZAvd2+w7ZsedsgF+cfX6cFh0Zt5Ty1R9aMtl6uve5e3vfpOexY8QDNsLiRLU5UMHD+B98dsw"
    "IRjexoQDHa5fCQIILBgD1Iwc/pW62r33nRIYUTp2Mg47hEoRN6k7m2qS+Oqst57jXWCShPra1bxz"
    "9Tmkq18naBtZdK5+D1gBT173vP2hxcZKloMrlgxENnj9tc068q/O/+u/qOtUurvzzoXb2hWzte67"
    "XkUnvqRldf5OvKIuNxKG4vt7eff6C6ivW4NtbkXzjD11eQ+lWLllYZmPPrS0tHuSstI8Wnn5xRoP"
    "LB/DmBNPDj54kTsnvqTlrldRVGUHAh3Llllmiw821y4OWqJxLq3nYIzEIR/ePovqm69gW9qKkd9B"
    "zmbwtsYUi3Vnoy2yzbPGGBBDEitvrLGceNFw7lzQxFMvxtz0r2VOnb0/TeffaOKRbbmEjAs21y5m"
    "tviOZcvstou4wei452jLs/rrYs0oX69p0NJkNj3zBO/N+TuCYcNR53YSsJRKNQXVwiOoEsURURg2"
    "otEAScE5T6VS/SR0NCJWU1MZa4VqTUhTCGNLtqmHA74ziz86929IP+rzNknEO78hDKODnzuOnsaI"
    "aFCMfuEq86X1s4OWqD3rqTqxkc17N7N+wS2YKCnswA7TryRJxNeOOAxjBPWKsZb33nuftevWEwQB"
    "qoo1hrRWo1RKOOG4o4s42CAXJzG/fOnXZFlGKYZyAuDQIKJv8UOkJ52BSZqMr2cubCu1533Z2Uh0"
    "a8dSDbohDwC6J+OYqQatnad1FPXYppCNjz5Euvo3BK0jdpCOMUKtXme/9i/zzL8/iLWfrK0rr5nD"
    "3JtuZcTIvVBVarU6YRiy4J7bOGna8du0c90/3UL3s8uJ4xg/OEiKhCUqb7xCb/eTjDzjHPLeOg1s"
    "5zFTb++ejAMwnQsXWkR00smMx9ojXLWGmMC6Sp2exYuQMC7i/C43bKVez1BVsqz46xth1VpLmhbg"
    "H1v4I06adjx57sjzQopXXTuH739/LnEcbSO3gXYlSuhZvAhXqReYqjWw9ohJJzMeEe1cuNCa9aM6"
    "C0XWatOCUmDVO2dKMembr1B9exUmKe02zovINrcqiLVUqzWSOOKJh3/M5BMmkWU5IhAElu9+7wbm"
    "zJ3HXu0jUd15eDJJierbq0jffAVTilHvXFAKLLXaNID1ozrFtG8oJOnh2IY4kQD6X36h4W2GnvkF"
    "oUVrKU3lEk8+8hOO/9OjyLIMYw3WWi678jpuvOk2RrSPwLtdW38xBp9W6H/5BSQYWPUNrED7BjTo"
    "miEOVTFLa4f4DBAx6qDyxkrE2N248Z1f/f39NLc08eSin3DkxAlkWYa1FmMM3758Frfcchcj2kcO"
    "SmnX+gQxlsobK1FXYPMZGDgEVekScQZg4gqGqTJac4+IEV+pUV/3HhKEn6r/nUkJ4Evto3j0kfsa"
    "4PNB8Bddeu1nB99wsRKE1Ne9h6/UEDGiuUeV0RNXMIwi84EEWp2hRX2OWIvr24zb0lu4qiH5s0Ju"
    "V152IdZanHOEYQDABRdfxfz59zCifRR5nn/2Rq3FbenFV/uwzcNQn4OhJYFWoNcAaG+thCdGPRiL"
    "r6dovTbo54d6WWtx3iNi6O+vcM75lzD/R/cPHXyhGrRew9dTMLbwX554oOIR8L9wee8xDTnlzrFm"
    "zYcggsie78sM1G0w1BAD3mGiBIniIel/eykNhNPWYS387PH7OOXEDjZu+HhQUp+9iuORKMZECXgH"
    "YsBQk9a4OkgghV48W8QEqHOYUjO2pbXhaYfSWRGyVr78WmP6i9kolRIW/fQuvnHKtKGTcA7b0oop"
    "NaPOISYAz5YUegcJrJjIZhHWSmBQ9WrKMdHe+6J5NqR1MLAD337XvVx4yfcas6A45yiXSjz80Hz+"
    "/BsnfmYSIgbNM6K998WUY1S9SmAQYe2KiWxuWAm1iKiH10xYzJlYKI+bUBSnPodu29paueOHP+Ta"
    "2Tc2PJLgnKOUJHQtmM+pf3YyG9d/TBiGu61aqXeUx01AbIHNhODhtcJKqDXrRxUQDTxffBI0h6bD"
    "jiny3c+RLnrvseUR3DB3Hldc/Y9YawZJJHFM14N3MP20r7Nx/cZPnQn1HpOUaTrsGDRvMJIGVmD9"
    "KMS0b+hq+Np4cV7NnRhrfbVGcuChlA4Yj0+rjQR1KIsBnHOMGjWSf77xNi676vqChBQk4jjmp/ff"
    "wenTT9k1CWPwaZXSAeNJDjwUX60hxtq8mjvieHFhJbrUdM2Y4VCV5U+zCud+ZUsx6nNnyxFt085E"
    "s93vB977be6Bxexczoj2kfzgB3fwnSv+YTBby7KcMAxYcO9tTJ9+ChvXrcduN0giBs1qtE07E1uO"
    "CkylGJz71fKnWYWqdM2YUViJjmVYZotHzD0SIYjB9We0TZlOMvYgfFopwtcu7EO5XMIYQxRFGGMK"
    "bTdI5HnOiPYR3HzzfL59+azG9wHGGJIk5rGFd3PueWdRqVQHd3KkMHHJ2INomzId158VBeIC2z1F"
    "Won9nVJKAZz3lMslJh31NYw1qFesNbz227dYvXoN4VZppTGGLVv6OOG4o9lreBuuMVOBtWRZxtJn"
    "lw96KbGWfPMm9r3yNoafeBr5ln5voljU+Q3BdimlfHLQsDTonjIlP3pJekXYEs/JetIcCGxTwpo5"
    "l7Bp8aKinLJdRcJ7pb9SGRxxBZIkJo52TFKMMfT19ZM790larIoxhubmpgJTEJL3bGT4tDMZc+Ut"
    "uP4UIA/bkiDbUrvyxanJ3AGs21bmGuXEiaeShJvr/2XCYJxLU2+C0PhaH29f8U3Sd14vyirbpZd2"
    "O9O39TrY1S69/QbovUdsgOvrJdn/YA6YuwATN+PzzNskMT7L38iGRYeveJKUWehA0dlsJWbt/Cqy"
    "4kipiDUXYASxgdcsU9PUyn7X3Em09xhcX29RvN1ms3Tb3LsCP0Bu++e9L2yz6+sl2nsM+11zJ6ap"
    "Fc0yFRv4Aou5YMWRUun8KrL1Kc42K7NrhrhOVbu8I1zi09oNYWsUYGzu05Ro9Fj2v+E+krEHk/ds"
    "RGywy4U9NLtpEBuQ92wkGXsw+99wH9Hosfg0BWPzsDUKfFq7YXlHuKRTdzy9+YMXd31awddT2qae"
    "wT4XzsY2teGqVcSYLGhLwnxLfdELU+K/7FS1XYIH2V11+vdYXs9qJPsdRPu3LqZt6uloPcfX64ix"
    "WdAWh64/+3nkPzite9nY+ta6/0IdcLRNOYOgdRiur4qqejGGsDUxedV1Rfmac7un7J9ufVL0xTti"
    "6s/QrK4Y62wpCRAFp9c/f4K9dnsMX+xDvrLB19wqnF76fEf4NDPV7Eo2X9xj1r4N81Z+fXT/UM6K"
    "//8cdP+feNXgi/iyxx65/pCv2/wPvzcGV5lgmxwAAAAASUVORK5CYII="
)


def parse_buttons(items):
    """Đọc danh sách nút từ file JSON, bỏ qua dữ liệu hỏng."""
    out = []
    if not isinstance(items, list):
        return out
    for it in items:
        if not isinstance(it, dict):
            continue
        try:
            x, y = int(it.get("x")), int(it.get("y"))
        except (TypeError, ValueError):
            continue
        try:
            size = int(it.get("size") or 0)
        except (TypeError, ValueError):
            size = 0
        key = it.get("key")
        if isinstance(key, bool) or not isinstance(key, int) or not 0 < key < 0xFF:
            key = None
        mouse = it.get("mouse") if it.get("mouse") in MOUSE_BUTTONS else "left"
        mode = it.get("mode") if it.get("mode") in MODES else "click"
        try:
            delay = max(0, min(MAX_DELAY_MS, int(it.get("delay", DEFAULT_DELAY_MS))))
        except (TypeError, ValueError):
            delay = DEFAULT_DELAY_MS
        x2, y2 = it.get("x2"), it.get("y2")
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in (x2, y2)):
            x2 = y2 = None
        try:
            swipe_ms = int(it.get("swipe_ms", DEFAULT_SWIPE_MS))
        except (TypeError, ValueError):
            swipe_ms = DEFAULT_SWIPE_MS
        swipe_ms = max(SWIPE_MS_RANGE[0], min(SWIPE_MS_RANGE[1], swipe_ms))
        out.append({"x": x, "y": y, "size": size, "key": key, "mouse": mouse, "mode": mode,
                    "delay": delay, "in_script": bool(it.get("in_script", True)),
                    "x2": x2, "y2": y2, "swipe_ms": swipe_ms})
    return out


def parse_scripts(items, n_buttons):
    """Đọc danh sách script từ file JSON. Trả về None nếu là file kiểu cũ (chưa có "scripts")."""
    if not isinstance(items, list):
        return None
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        name = it.get("name") if isinstance(it.get("name"), str) else ""
        key = it.get("key")
        if isinstance(key, bool) or not isinstance(key, int) or not 0 < key < 0xFF:
            key = None
        try:
            loops = max(1, min(999999, int(it.get("loops", 1))))
        except (TypeError, ValueError):
            loops = 1
        steps = []
        for st in it.get("steps") or []:
            if not isinstance(st, dict):
                continue
            idx = st.get("button")
            if isinstance(idx, bool) or not isinstance(idx, int) or not 0 <= idx < n_buttons:
                continue
            try:
                delay = max(0, min(MAX_DELAY_MS, int(st.get("delay", DEFAULT_STEP_DELAY_MS))))
            except (TypeError, ValueError):
                delay = DEFAULT_STEP_DELAY_MS
            steps.append({"button": idx, "delay": delay})
        out.append({"name": name.strip()[:40], "key": key, "loops": loops,
                    "forever": bool(it.get("forever", False)), "steps": steps,
                    # mặc định BẬT (bản 1.6 lưu "lock" mặc định tắt -> bỏ qua, dùng tên mới)
                    "lock": it.get("lock_keys") is not False,
                    "f9": it.get("f9") is not False})
    return out


def _legacy_loop_settings(data):
    """(số vòng, lặp vĩnh viễn) của script trong file bản cũ (≤ 1.3)."""
    loops, forever = 1, False
    if isinstance(data, dict):
        v = data.get("script_loops")
        if isinstance(v, int) and not isinstance(v, bool):
            loops = max(1, min(999999, v))
        forever = data.get("script_forever") is True
    return loops, forever


def sanitize_cfg(data):
    cfg = dict(DEFAULT_CFG)
    if not isinstance(data, dict):
        return cfg
    for k, default in DEFAULT_CFG.items():
        v = data.get(k)
        if isinstance(v, (bool, int, float)) and not (isinstance(v, bool) != isinstance(default, bool)):
            v = type(default)(v)
            lim = CFG_LIMITS.get(k)
            if lim:
                v = type(default)(min(max(v, lim[0]), lim[1]))
            cfg[k] = v
    return cfg


def _make_overlay(app, key, width, height):
    """Cửa sổ nhỏ không viền, luôn trên cùng; chỗ tô màu `key` sẽ trong suốt (Windows)."""
    top = tk.Toplevel(app.root)
    top.withdraw()
    top.overrideredirect(True)
    top.configure(bg=key)
    top.attributes("-topmost", True)
    if app.api.is_windows:
        top.attributes("-transparentcolor", key)
        top.attributes("-alpha", 0.0)         # apply_mode() sẽ đặt độ đậm thật
    cv = tk.Canvas(top, width=width, height=height, bg=key, highlightthickness=0, bd=0)
    cv.pack()
    return top, cv


def write_json(path, data):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


class Circle(object):
    """Một nút tròn = 2 cửa sổ nhỏ chồng khít lên nhau, không viền, luôn nằm trên cùng:
      - lớp NỀN: hình tròn mờ (độ đậm chỉnh được), nhận chuột để kéo / phóng to / thu nhỏ
      - lớp CHỮ: tên phím, luôn rõ nét, chuột đi xuyên qua
    Phần góc vuông tô "màu trong suốt" nên Windows đục lỗ -> nhìn thấy hình tròn."""

    _ids = itertools.count(1)
    MIN_SIZE, MAX_SIZE = 24, 320

    def __init__(self, app, cx, cy, size, key=None, button="left", mode="click",
                 x2=None, y2=None, swipe_ms=DEFAULT_SWIPE_MS):
        self.app = app
        self.id = next(Circle._ids)
        self.cx, self.cy = int(cx), int(cy)
        self.size = int(max(self.MIN_SIZE, min(self.MAX_SIZE, size)))
        self.key = key
        self.button = button if button in MOUSE_BUTTONS else "left"
        self.mode = mode if mode in MODES else "click"
        self.x2, self.y2 = x2, y2       # nút vuốt: điểm đích B
        self.swipe_ms = int(swipe_ms)   # nút vuốt: thời gian vuốt (ms)
        self.guide = None               # mũi tên + chấm B (chỉ có ở nút vuốt)
        self.editing = False
        self.hover = False
        self._caret_on = True
        self._caret_job = None
        self._flash_color = None
        self._flash_job = None
        self._drag = None
        self._shown = False
        self._cursor = None

        self.top, self.canvas = self._make_layer(THEME["key"])          # lớp nền
        self.ftop, self.fcanvas = self._make_layer(THEME["key_text"])   # lớp chữ
        self._place()
        for cv in (self.canvas, self.fcanvas):
            cv.bind("<ButtonPress-1>", self._on_press)
            cv.bind("<B1-Motion>", self._on_motion)
            cv.bind("<ButtonRelease-1>", self._on_release)
            cv.bind("<ButtonPress-3>", self._on_menu)
            cv.bind("<Motion>", self._on_hover_move)
            cv.bind("<Leave>", self._on_leave)
            cv.bind("<MouseWheel>", lambda e: self._wheel(1 if e.delta > 0 else -1))
            cv.bind("<Button-4>", lambda e: self._wheel(1))
            cv.bind("<Button-5>", lambda e: self._wheel(-1))
        self.redraw()
        if app.api.is_windows:            # trên Windows nút luôn "hiện", ẩn bằng độ trong suốt
            self.top.deiconify()
            self.ftop.deiconify()
            self._shown = True
        self.hwnd = app.api.toplevel_hwnd(self.top)
        self.fhwnd = app.api.toplevel_hwnd(self.ftop)
        app.api.set_owner(self.fhwnd, self.hwnd)      # lớp chữ luôn nằm trên lớp nền
        self.apply_mode()
        if self.mode == "swipe":
            self._ensure_swipe()

    def _make_layer(self, key):
        return _make_overlay(self.app, key, self.size, self.size)

    # ---- nút vuốt ----
    def _ensure_swipe(self):
        if self.x2 is None or self.y2 is None:           # điểm đích mặc định: bên phải nút
            vx, vy, vw, vh = self.app.vscreen()
            d = self.app.px(160)
            x2 = self.cx + d if self.cx + d < vx + vw - self.app.px(20) else self.cx - d
            self.x2, self.y2 = self.app.clamp_point(x2, self.cy)
        if self.guide is None:
            self.guide = SwipeGuide(self)

    def set_mode(self, mode):
        self.mode = mode if mode in MODES else "click"
        if self.mode == "swipe":
            self._ensure_swipe()
        elif self.guide is not None:
            self.guide.destroy()
            self.guide = None
        self.redraw()

    def target(self):
        """Thông tin để engine click / vuốt."""
        if self.mode == "swipe" and self.x2 is not None:
            return Target(self.id, self.cx, self.cy, self.button, "swipe", self.x2, self.y2,
                          self.swipe_ms)
        mode = "click" if self.mode == "swipe" else self.mode
        return Target(self.id, self.cx, self.cy, self.button, mode)

    # ---- trạng thái hiển thị ----
    def _visible(self):
        return self.app.show_buttons or self.editing

    def _alphas(self):
        """Trả về (độ đậm lớp nền, độ đậm lớp chữ)."""
        if not self._visible():
            return 0.0, 0.0
        cfg = self.app.cfg
        bg = cfg["bg_alpha"]
        if self._flash_color:               # nháy sáng khi bấm phím: nền đậm lên một chút
            bg = max(bg, 0.6)
        if self.app.enabled:                # đang chơi: mờ thêm cho đỡ che game
            return bg * cfg["play_dim"], cfg["play_dim"]
        return bg, 1.0

    def apply_alpha(self):
        if self.app.api.is_windows:
            bg, fg = self._alphas()
            self.top.attributes("-alpha", bg)
            self.ftop.attributes("-alpha", fg)

    def apply_mode(self):
        """Đang chơi: mờ hơn + chuột đi xuyên qua. Đang chỉnh: rõ hơn + kéo được."""
        app = self.app
        visible = self._visible()
        if app.api.is_windows:
            self.apply_alpha()
        elif visible and not self._shown:
            self.top.deiconify()
            self.ftop.deiconify()
            self._shown = True
        elif not visible and self._shown:
            self.ftop.withdraw()
            self.top.withdraw()
            self._shown = False
        app.api.set_window_style(self.hwnd, click_through=app.enabled or not visible)
        app.api.set_window_style(self.fhwnd, click_through=True)   # lớp chữ: luôn xuyên qua
        if app.enabled:
            self.hover = False
        self._set_cursor("" if app.enabled else "fleur")
        self.redraw()
        if self.guide is not None:
            self.guide.apply_mode()

    def _place(self):
        d = self.size
        geo = "%dx%d+%d+%d" % (d, d, self.cx - d // 2, self.cy - d // 2)
        self.top.geometry(geo)
        self.ftop.geometry(geo)

    def redraw(self):
        self._draw_bg()
        self._draw_fg()

    def _draw_bg(self):
        c = self.canvas
        c.delete("all")
        d = self.size
        if self._flash_color:
            fill = self._flash_color
        elif self.editing:
            fill = THEME["fill_edit"]
        elif self.hover:
            fill = THEME["fill_hover"]
        else:
            fill = THEME["fill"]
        c.create_oval(1, 1, d - 1, d - 1, fill=fill, outline="")      # không viền

    def _draw_fg(self):
        c = self.fcanvas
        c.delete("all")
        d = self.size
        color = THEME.get("text_" + self.button, THEME["text_left"])
        tag = MODE_TAGS.get(self.mode)
        mid = d / 2.0 - (d * 0.07 if tag else 0)
        if self.editing:
            label = ""
        elif self.key is None:
            label, color = "?", THEME["muted"]
        else:
            label = vk_label(self.key, self.app.api)
        if label:
            fs = max(8, int(min(d * 0.40, d * 0.78 / (0.62 * max(1, len(label))))))
            _outlined_text(c, d / 2.0, mid, label, color, (FONT_UI, -fs, "bold"),
                           1 if fs < 30 else 2)
        if tag and d >= 34:
            ts = max(8, int(d * 0.17))
            _outlined_text(c, d / 2.0, d * 0.755, tag, color, (FONT_UI, -ts, "bold"))
        if self.editing and self._caret_on:       # dấu nháy |
            h, w = d * 0.42, max(2, d // 24)
            c.create_line(d / 2.0, mid - h / 2, d / 2.0, mid + h / 2,
                          fill=THEME["outline"], width=w + 2)
            c.create_line(d / 2.0, mid - h / 2, d / 2.0, mid + h / 2,
                          fill=THEME["caret"], width=w)

    # ---- dấu nháy & nháy sáng ----
    def start_caret(self):
        self.stop_caret()
        self._caret_job = self.top.after(530, self._blink)

    def _blink(self):
        self._caret_on = not self._caret_on
        self._draw_fg()
        self._caret_job = self.top.after(530, self._blink)

    def stop_caret(self):
        if self._caret_job:
            self.top.after_cancel(self._caret_job)
            self._caret_job = None
        self._caret_on = True

    def flash(self, color=None, ms=150):
        self._flash_color = color or THEME.get(self.button, THEME["left"])
        self.apply_alpha()
        self._draw_bg()
        if self._flash_job:
            self.top.after_cancel(self._flash_job)
        self._flash_job = self.top.after(ms, self._end_flash)

    def _end_flash(self):
        self._flash_job = None
        self._flash_color = None
        self.apply_alpha()
        self._draw_bg()

    # ---- di chuyển / phóng to / thu nhỏ (tâm nút giữ nguyên) ----
    def move_to(self, cx, cy):
        cx, cy = self.app.clamp_point(cx, cy)
        if (cx, cy) == (self.cx, self.cy):
            return
        if self.x2 is not None:          # nút vuốt: điểm đích B đi theo, giữ nguyên hướng vuốt
            self.x2, self.y2 = self.app.clamp_point(self.x2 + cx - self.cx, self.y2 + cy - self.cy)
        self.cx, self.cy = cx, cy
        self._place()
        if self.guide is not None:
            self.guide.update()
        if self.editing:
            self.app.position_hint(self)

    def set_size(self, size, save=True):
        s = int(round(max(self.MIN_SIZE, min(self.MAX_SIZE, size))))
        if s == self.size:
            return
        self.size = s
        self.canvas.configure(width=s, height=s)
        self.fcanvas.configure(width=s, height=s)
        self._place()
        self.redraw()
        if self.guide is not None:
            self.guide.update()
        if self.editing:
            self.app.position_hint(self)
        if save:
            self.app.layout_changed()

    def resize(self, delta):
        self.set_size(self.size + delta)

    def _wheel(self, step):
        if not self.app.enabled:
            self.resize(step * max(4, int(self.size * 0.08)))

    def _in_rim(self, x, y):
        """(x, y) tính trong nút: có nằm ở MÉP nút (vùng kéo để đổi cỡ) không?"""
        r = self.size / 2.0
        return math.hypot(x - r, y - r) >= r - max(self.app.px(6), r * 0.28)

    def _set_cursor(self, name):
        if name != self._cursor:
            self._cursor = name
            self.canvas.configure(cursor=name)
            self.fcanvas.configure(cursor=name)

    def _set_hover(self, value):
        value = value and not self.app.enabled
        if value != self.hover:
            self.hover = value
            self._draw_bg()

    def _on_hover_move(self, e):
        if self.app.enabled or self._drag:
            return
        self._set_hover(True)
        if self._in_rim(e.x, e.y):          # ở mép: con trỏ mũi tên chéo = kéo để đổi cỡ
            r = self.size / 2.0
            diag = (e.x - r) * (e.y - r) >= 0
            self._set_cursor(RESIZE_CURSORS[0] if diag else RESIZE_CURSORS[1])
        else:
            self._set_cursor("fleur")

    def _on_leave(self, e):
        if not self._drag:
            self._set_hover(False)

    # ---- chuột: bấm = gán phím, kéo giữa = di chuyển, kéo mép = đổi cỡ, Ctrl+kéo = nhân bản ----
    def _on_press(self, e):
        if self.app.enabled:
            return
        if e.state & 0x0004:
            mode = "dup"
        elif self._in_rim(e.x, e.y):
            mode = "resize"
        else:
            mode = "move"
        self._drag = {"mode": mode, "x": e.x_root, "y": e.y_root, "moved": False,
                      "target": None, "size": self.size,
                      "dist": math.hypot(e.x_root - self.cx, e.y_root - self.cy)}

    def _on_motion(self, e):
        d = self._drag
        if not d or self.app.enabled:
            return
        dx, dy = e.x_root - d["x"], e.y_root - d["y"]
        if not d["moved"]:
            if abs(dx) + abs(dy) < 4:
                return
            d["moved"] = True
            if d["mode"] == "dup":
                d["target"] = self.app.duplicate(self, offset=False, start_edit=False)
            else:
                d["target"] = self
            d["cx"], d["cy"] = d["target"].cx, d["target"].cy
        if d["mode"] == "resize":           # mép nút đi theo con trỏ, tâm đứng yên
            dist = math.hypot(e.x_root - self.cx, e.y_root - self.cy)
            self.set_size(d["size"] + 2 * (dist - d["dist"]), save=False)
        else:
            d["target"].move_to(d["cx"] + dx, d["cy"] + dy)

    def _on_release(self, e):
        d, self._drag = self._drag, None
        if not d or self.app.enabled:
            return
        if d["mode"] == "dup":
            target = d["target"] if d["moved"] else self.app.duplicate(self, start_edit=False)
            target.start_edit()
        elif not d["moved"]:
            self.start_edit()
        self.app.layout_changed()

    def _on_menu(self, e):
        if not self.app.enabled:
            self.app.show_circle_menu(self, e.x_root, e.y_root)

    def start_edit(self):
        self.app.begin_edit(self)

    def to_dict(self):
        return {"x": self.cx, "y": self.cy, "size": self.size, "key": self.key,
                "mouse": self.button, "mode": self.mode, "x2": self.x2, "y2": self.y2,
                "swipe_ms": self.swipe_ms}

    def destroy(self):
        self.stop_caret()
        if self._flash_job:
            try:
                self.top.after_cancel(self._flash_job)
            except tk.TclError:
                pass
        if self.guide is not None:
            self.guide.destroy()
            self.guide = None
        self.ftop.destroy()        # lớp chữ trước (nó "thuộc về" lớp nền)
        self.top.destroy()


class SwipeGuide(object):
    """Mũi tên từ nút vuốt tới điểm đích B (chấm vàng kéo được). Chỉ hiện khi đang chỉnh."""

    ALPHA = 0.9

    def __init__(self, circle):
        self.c = circle
        self.app = app = circle.app
        self.m = app.px(30)                       # đường kính chấm B
        self._drag = None
        self._shown = False
        self.ltop, self.lcanvas = _make_overlay(app, THEME["key"], 10, 10)          # mũi tên
        self.btop, self.bcanvas = _make_overlay(app, THEME["key"], self.m, self.m)  # chấm B
        self.bcanvas.bind("<ButtonPress-1>", self._on_press)
        self.bcanvas.bind("<B1-Motion>", self._on_motion)
        self.bcanvas.bind("<ButtonRelease-1>", self._on_release)
        self.bcanvas.bind("<ButtonPress-3>", circle._on_menu)
        self._draw_marker()
        self.update()
        if app.api.is_windows:
            self.ltop.deiconify()
            self.btop.deiconify()
            self._shown = True
        self.lhwnd = app.api.toplevel_hwnd(self.ltop)
        self.bhwnd = app.api.toplevel_hwnd(self.btop)
        self.apply_mode()

    def _visible(self):
        return self.c._visible() and not self.app.enabled

    def apply_mode(self):
        app = self.app
        visible = self._visible()
        if app.api.is_windows:
            a = self.ALPHA if visible else 0.0
            self.ltop.attributes("-alpha", a)
            self.btop.attributes("-alpha", a)
        elif visible and not self._shown:
            self.ltop.deiconify()
            self.btop.deiconify()
            self._shown = True
        elif not visible and self._shown:
            self.ltop.withdraw()
            self.btop.withdraw()
            self._shown = False
        app.api.set_window_style(self.lhwnd, click_through=True)
        app.api.set_window_style(self.bhwnd, click_through=not visible)
        self.bcanvas.configure(cursor="fleur" if visible else "")

    def _draw_marker(self):
        cv, m = self.bcanvas, self.m
        cv.delete("all")
        w = max(2, self.app.px(3))
        cv.create_oval(2, 2, m - 2, m - 2, fill=THEME["fill"], outline=THEME["caret"], width=w)
        r = max(2, m // 8)
        cv.create_oval(m / 2.0 - r, m / 2.0 - r, m / 2.0 + r, m / 2.0 + r,
                       fill=THEME["caret"], outline="")

    def update(self):
        """Đặt chấm B đúng chỗ và vẽ lại mũi tên từ mép nút tới mép chấm B."""
        c, m, px = self.c, self.m, self.app.px
        bx, by = c.x2, c.y2
        self.btop.geometry("%dx%d+%d+%d" % (m, m, bx - m // 2, by - m // 2))
        cv = self.lcanvas
        cv.delete("all")
        dx, dy = bx - c.cx, by - c.cy
        dist = math.hypot(dx, dy)
        ra, rb = c.size / 2.0 + 2, m / 2.0 + 2
        if dist <= ra + rb + 6:                  # B nằm sát nút: không cần mũi tên
            cv.configure(width=1, height=1)
            self.ltop.geometry("1x1+%d+%d" % (c.cx, c.cy))
            return
        ux, uy = dx / dist, dy / dist
        sx, sy = c.cx + ux * ra, c.cy + uy * ra
        ex, ey = bx - ux * rb, by - uy * rb
        pad = px(14)
        x0, y0 = int(min(sx, ex)) - pad, int(min(sy, ey)) - pad
        w, h = int(max(sx, ex)) + pad - x0, int(max(sy, ey)) + pad - y0
        cv.configure(width=w, height=h)
        self.ltop.geometry("%dx%d+%d+%d" % (w, h, x0, y0))
        lw = max(2, px(3))
        a = (px(12), px(14), px(5))
        pts = (sx - x0, sy - y0, ex - x0, ey - y0)
        cv.create_line(*pts, fill=THEME["outline"], width=lw + 3, arrow="last",
                       arrowshape=(a[0] + 2, a[1] + 2, a[2] + 2))
        cv.create_line(*pts, fill=THEME["caret"], width=lw, arrow="last", arrowshape=a)

    def _on_press(self, e):
        if not self.app.enabled:
            self._drag = (e.x_root, e.y_root, self.c.x2, self.c.y2)

    def _on_motion(self, e):
        if not self._drag or self.app.enabled:
            return
        x0, y0, bx, by = self._drag
        self.c.x2, self.c.y2 = self.app.clamp_point(bx + e.x_root - x0, by + e.y_root - y0)
        self.update()

    def _on_release(self, e):
        if self._drag is not None:
            self._drag = None
            self.app.layout_changed()

    def destroy(self):
        self.ltop.destroy()
        self.btop.destroy()


class Bubble(object):
    """Khung chữ nhỏ nổi trên màn hình (thông báo F8, gợi ý khi gán phím). Chuột đi xuyên qua."""

    def __init__(self, app, font):
        self.app = app
        self._job = None
        top = tk.Toplevel(app.root)
        top.withdraw()
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        self.label = tk.Label(top, text="", font=font, padx=app.px(14), pady=app.px(7), bd=0)
        self.label.pack()
        self.top = top
        self.hwnd = None
        if app.api.is_windows:
            top.attributes("-alpha", 0.0)
            top.geometry("+0+0")
            top.deiconify()
            self.hwnd = app.api.toplevel_hwnd(top)
            app.api.set_window_style(self.hwnd, click_through=True)

    def show(self, text, x, y, anchor="n", bg="#111827", fg="#ffffff", ms=None):
        self.label.configure(text=text, bg=bg, fg=fg)
        self.top.configure(bg=bg)
        self.top.update_idletasks()
        w, h = self.top.winfo_reqwidth(), self.top.winfo_reqheight()
        gy = y if anchor == "n" else y - h
        vx, vy, vw, vh = self.app.vscreen()          # không cho tràn ra ngoài màn hình
        gx = min(max(x - w / 2, vx), vx + vw - w)
        gy = min(max(gy, vy), vy + vh - h)
        self.top.geometry("+%d+%d" % (int(gx), int(gy)))
        if self.hwnd:
            self.top.attributes("-alpha", 0.95)
            self.app.api.set_topmost(self.hwnd)
        else:
            self.top.deiconify()
            self.top.lift()
        self._cancel()
        if ms:
            self._job = self.top.after(ms, self.hide)

    def hide(self):
        self._cancel()
        if self.hwnd:
            self.top.attributes("-alpha", 0.0)
        else:
            self.top.withdraw()

    def _cancel(self):
        if self._job:
            try:
                self.top.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None


_TK_KEYSYM_VK = {
    "space": 0x20, "Return": 0x0D, "Escape": 0x1B, "Tab": 0x09, "BackSpace": 0x08,
    "Left": 0x25, "Up": 0x26, "Right": 0x27, "Down": 0x28,
    "Shift_L": 0xA0, "Shift_R": 0xA1, "Control_L": 0xA2, "Control_R": 0xA3,
    "Alt_L": 0xA4, "Alt_R": 0xA5,
}


def _tk_keysym_to_vk(keysym):
    """Chỉ dùng ở chế độ thử (không phải Windows)."""
    if keysym in _TK_KEYSYM_VK:
        return _TK_KEYSYM_VK[keysym]
    if len(keysym) == 1 and keysym.isalnum():
        return ord(keysym.upper())
    m = re.match(r"^F(\d{1,2})$", keysym)
    if m and 1 <= int(m.group(1)) <= 24:
        return 0x6F + int(m.group(1))
    return None


class App(object):
    """Cửa sổ điều khiển chính."""

    def __init__(self, api, config_path):
        self.api = api
        self.config_path = config_path
        self.cfg = dict(DEFAULT_CFG)
        self.profile_dir = ""
        self._start_buttons = []
        self._start_scripts = None      # danh sách script đọc từ file (None = file kiểu cũ)
        self._start_script_sel = 0
        self._legacy_loops, self._legacy_forever = 1, False
        self._window_pos = None
        self._read_config()

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title(WINDOW_TITLE if api.is_windows else WINDOW_TITLE + " (chế độ thử)")
        self.root.report_callback_exception = self._tk_error
        self.scale = max(1.0, self.root.winfo_fpixels("1i") / 96.0)
        self._setup_style()

        self.ui_q = queue.Queue()
        self.engine = ClickEngine(api, self.ui_q, self.cfg)
        self.circles = {}               # id -> Circle (giữ thứ tự tạo)
        self.editing = None             # nút đang chờ gán phím
        self.enabled = False            # luôn khởi động ở trạng thái TẮT cho an toàn
        self.show_buttons = bool(self.cfg["show_buttons"])
        self.hook = None
        self.hook_error = None
        self._save_job = None
        self._notice_job = None
        self._edit_job = None
        self._poll_job = None
        self._top_job = None
        self._fg_job = None
        self._menu_refs = None
        self._is_admin = bool(api.is_windows and api.is_admin())
        self._last_fg_pid = None        # tiến trình của cửa sổ đang được chọn (lần xem trước)
        self._elev_warned = set()       # đã cảnh báo "cửa sổ chạy quyền Admin" cho các pid này
        self.scripts = []               # các script: {id, name, key, loops, forever, steps}
        self.sel_sid = None             # script đang chọn trong tab Script
        self.running = {}               # các script đang chạy (cùng lúc được): id -> số vòng
        self._quiet_start = set()       # script vừa chạy theo nhóm F9: không báo từng cái
        self._script_capture = None     # script đang chờ gán phím chạy
        self._sid_seq = 0
        self._script_sig = None
        self._script_vars = []
        self._sc_bar_on = False
        self._loading_script_ui = False

        self.var_enabled = tk.BooleanVar(master=self.root, value=False)
        self.var_return = tk.BooleanVar(master=self.root, value=bool(self.cfg["return_cursor"]))
        self.var_show = tk.BooleanVar(master=self.root, value=self.show_buttons)
        self._build_ui()
        # Biết lúc nào con trỏ đang ở 1 ô nhập của KeyClick để không click khi gõ chữ/số.
        self.root.bind_all("<FocusIn>", self._on_focus_change, add="+")
        self.root.bind_all("<FocusOut>", self._on_focus_change, add="+")
        self.root.bind_all("<ButtonPress-1>", self._on_any_click, add="+")
        for cls in ("TEntry", "TSpinbox"):     # Enter / Esc trong ô nhập = gõ xong
            for seq in ("<Return>", "<KP_Enter>", "<Escape>"):
                self.root.bind_class(cls, seq, self._on_typing_done, add="+")
        self._set_icon()
        self.toast = Bubble(self, self.f_toast)
        self.hint = Bubble(self, self.f_hint)

        created = self._create_buttons(self._start_buttons)
        self._install_scripts(self._start_scripts, created, self._start_buttons,
                              self._start_script_sel, self._legacy_loops, self._legacy_forever)
        self.layout_changed(save=False)

        self._start_hook()
        if not api.is_windows:
            self._install_tk_key_fallback()
        self._update_status()
        self._place_main_window()
        self.root.deiconify()
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self._poll_job = self.root.after(15, self._poll)
        self._top_job = self.root.after(2000, self._keep_on_top)
        if api.is_windows:
            self._fg_job = self.root.after(700, self._watch_foreground)

    # ------------------------------------------------------------------ tiện ích
    def px(self, v):
        return int(round(v * self.scale))

    def vscreen(self):
        v = None
        try:
            v = self.api.virtual_screen()
        except Exception:
            v = None
        if not v:
            v = (0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        return v

    def clamp_point(self, x, y):
        vx, vy, vw, vh = self.vscreen()
        return int(min(max(x, vx), vx + vw - 1)), int(min(max(y, vy), vy + vh - 1))

    def default_size(self):
        return int(self.cfg["button_size"]) or self.px(52)

    def _tk_error(self, exc, val, tb):
        log("Tk callback:\n" + "".join(traceback.format_exception(exc, val, tb)))

    @staticmethod
    def _typing_mode(w):
        """Ô nhập của KeyClick: "text" (ô Tên), "number" (ô ms, ô Loop) hoặc None.
        Hộp chọn script (chỉ chọn, không gõ được) và ô bị khoá không tính là ô nhập."""
        if not isinstance(w, (tk.Entry, tk.Spinbox)):     # gồm cả ttk.Entry/Spinbox/Combobox
            return None
        try:
            if isinstance(w, ttk.Widget):
                if not w.instate(["!disabled", "!readonly"]):
                    return None
            elif str(w.cget("state")) != "normal":
                return None
        except tk.TclError:
            return None
        return "number" if isinstance(w, (ttk.Spinbox, tk.Spinbox)) else "text"

    def _focus_widget(self):
        try:
            return self.root.focus_get()
        except Exception:                    # vd danh sách thả xuống của hộp chọn
            return None

    def _on_focus_change(self, e=None):
        """Con trỏ đang ở ô nhập chữ/số của KeyClick? (ô Tên, ô ms, ô Loop)"""
        mode = self._typing_mode(self._focus_widget())
        if mode != self.engine.typing:
            self.engine.typing = mode
            self._update_status()

    def _stop_typing(self):
        """Đưa con trỏ ra khỏi ô nhập: các phím đã gán click lại ngay.
        (Cả khi đang ở game: lần sau quay lại cửa sổ KeyClick, con trỏ không còn ở ô nhập.)"""
        w = self._focus_widget()
        if w is None:
            try:
                w = self.root.nametowidget(self.root.tk.call("focus", "-lastfor", str(self.root)))
            except Exception:
                w = None
        if self._typing_mode(w) is not None:
            self.root.focus_set()
        self.engine.typing = None

    def _on_typing_done(self, e=None):
        if self.engine.typing is not None:
            self._stop_typing()
            self._update_status()

    def _on_any_click(self, e):
        """Bấm vào chỗ khác trong KeyClick (nút, ô tick, tab, nút tròn…) = thôi gõ chữ."""
        w = e.widget
        if not isinstance(w, tk.Misc) or isinstance(w, ttk.Combobox):
            return
        if self._typing_mode(w) is None and self.engine.typing is not None:
            self._stop_typing()
            self._update_status()

    # ------------------------------------------------------------------ giao diện
    def _setup_style(self):
        style = ttk.Style(self.root)
        if not self.api.is_windows and "clam" in style.theme_names():
            style.theme_use("clam")
        base = tkfont.nametofont("TkDefaultFont")
        base.configure(size=10)
        try:
            tkfont.nametofont("TkTextFont").configure(size=10)
        except tk.TclError:
            pass
        self.f_bold = base.copy()
        self.f_bold.configure(weight="bold")
        self.f_small = base.copy()
        self.f_small.configure(size=9)
        self.f_toast = tkfont.Font(root=self.root, family=FONT_UI, size=13, weight="bold")
        self.f_hint = tkfont.Font(root=self.root, family=FONT_UI, size=10, weight="bold")
        style.configure("Small.TLabel", font=self.f_small, foreground="#475569")
        style.configure("Notice.TLabel", font=self.f_small, foreground="#b45309")

    def _build_ui(self):
        S = self.px
        root = self.root
        root.resizable(False, False)
        outer = ttk.Frame(root, padding=(S(14), S(12), S(14), S(12)))
        outer.pack(fill="both", expand=True)

        # Dòng trạng thái luôn 1 dòng, không đòi rộng thêm: chữ đổi mà cửa sổ không nhảy.
        self.status = tk.Label(outer, anchor="w", padx=S(10), pady=S(6), font=self.f_bold, bd=0,
                               width=1, height=1)
        self.status.pack(fill="x")

        self.notebook = ttk.Notebook(outer)
        self.notebook.pack(fill="both", expand=True, pady=(S(10), 0))
        tab_main = ttk.Frame(self.notebook, padding=(S(12), S(6), S(12), S(12)))
        tab_script = ttk.Frame(self.notebook, padding=(S(12), S(10), S(12), S(12)))
        self.notebook.add(tab_main, text="  Nút bấm  ")
        self.notebook.add(tab_script, text="  Script  ")
        self._build_main_tab(tab_main)
        self._build_script_tab(tab_script)

    def _build_main_tab(self, outer):
        S = self.px
        opts = ttk.Frame(outer, padding=(0, S(4), 0, S(2)))
        opts.pack(fill="x")
        self.cb_enabled = ttk.Checkbutton(opts, variable=self.var_enabled,
                                          command=self._on_cb_enabled)
        self.cb_return = ttk.Checkbutton(opts, text="Trả chuột về vị trí cũ sau khi click",
                                         variable=self.var_return, command=self._on_cb_return)
        self.cb_show = ttk.Checkbutton(opts, text="Hiện các nút trên màn hình",
                                       variable=self.var_show, command=self._on_cb_show)
        for cb in (self.cb_enabled, self.cb_return, self.cb_show):
            cb.pack(anchor="w", pady=S(3))
        self.cb_enabled.configure(
            text="Bật phím tắt  (%s để bật/tắt nhanh)" % vk_label(self.engine.toggle_vk))

        pct = int(round(self.cfg["bg_alpha"] * 100))
        op = ttk.Frame(opts)
        op.pack(anchor="w", pady=(S(6), 0))
        ttk.Label(op, text="Độ đậm nền nút").pack(side="left")
        self.var_bg = tk.DoubleVar(master=self.root, value=pct)
        self.scale_bg = ttk.Scale(op, from_=5, to=100, orient="horizontal", length=S(140),
                                  variable=self.var_bg, command=self._on_bg_alpha)
        self.scale_bg.pack(side="left", padx=(S(10), S(6)))
        self.lbl_bg = ttk.Label(op, text="%d%%" % pct, width=5)
        self.lbl_bg.pack(side="left")

        ttk.Separator(outer).pack(fill="x", pady=(S(10), S(12)))

        row = ttk.Frame(outer)
        row.pack(fill="x")
        ttk.Button(row, text="＋  Thêm nút", command=self.add_circle).pack(side="left")
        ttk.Button(row, text="＋  Nút vuốt",
                   command=lambda: self.add_circle(mode="swipe")).pack(side="left", padx=(S(8), 0))
        row2 = ttk.Frame(outer)
        row2.pack(fill="x", pady=(S(8), 0))
        ttk.Button(row2, text="Mở bộ phím…", command=self.open_profile).pack(side="left")
        ttk.Button(row2, text="Lưu bộ phím…", command=self.save_profile).pack(
            side="left", padx=(S(8), 0))
        ttk.Button(row2, text="Xoá hết", command=self.clear_all).pack(side="left", padx=(S(8), 0))

        box, self.lbl_count = self._fixed_label(outer, 1, self.f_small, style="Small.TLabel")
        box.pack(fill="x", pady=(S(10), 0))
        box, self.lbl_notice = self._fixed_label(outer, 2, self.f_small, style="Notice.TLabel")
        box.pack(fill="x")

        tips = ("• Bấm vào nút tròn → nhấn phím để gán (Esc: huỷ)\n"
                "• Kéo giữa nút để di chuyển\n"
                "• Kéo mép nút hoặc lăn chuột: phóng to / thu nhỏ\n"
                "• Ctrl + kéo, hoặc chuột phải → Nhân bản\n"
                "• Chuột phải: click trái/phải, giữ, turbo, vuốt, xoá…\n"
                "• Nút vuốt: kéo chấm vàng tới chỗ cần vuốt tới\n"
                "• Khi đang BẬT, nút bị khoá và chuột đi xuyên qua")
        ttk.Label(outer, text=tips, style="Small.TLabel", justify="left").pack(
            anchor="w", pady=(S(6), 0))

        if self.api.is_windows:
            adm = ttk.Frame(outer)
            adm.pack(fill="x", pady=(S(10), 0))
            if self._is_admin:
                ttk.Label(adm, text="✔ Đang chạy với quyền Admin", style="Small.TLabel").pack(
                    anchor="w")
            else:
                ttk.Label(adm, text="Game / giả lập chạy bằng quyền Admin thì KeyClick cũng phải "
                          "chạy Admin, nếu không Windows sẽ chặn phím và click:",
                          style="Small.TLabel", wraplength=S(340), justify="left").pack(anchor="w")
                ttk.Button(adm, text="Chạy lại bằng quyền Admin",
                           command=self.relaunch_admin).pack(anchor="w", pady=(S(4), 0))
            self.var_admin = tk.BooleanVar(master=self.root, value=bool(self.cfg["run_as_admin"]))
            self.cb_admin = ttk.Checkbutton(adm, text="Luôn chạy bằng quyền Admin",
                                            variable=self.var_admin, command=self._on_cb_admin)
            self.cb_admin.pack(anchor="w", pady=(S(4), 0))

    # ------------------------------------------------------------------ tab Script
    #  Nhiều script, mỗi script có: tên, phím chạy, các bước (nút + thời gian chờ), số lần lặp.
    #  Đang BẬT phím tắt: nhấn phím chạy để chạy script đó. Script có lặp: nhấn lại để dừng.
    #  Esc luôn dừng. F9 chạy / dừng script đang chọn trong tab này.
    def _build_script_tab(self, outer):
        S = self.px
        run_key = vk_label(self.engine.script_vk)
        top = ttk.Frame(outer)
        top.pack(fill="x")
        ttk.Label(top, text="Script:", font=self.f_bold).pack(side="left")
        self.var_sel = tk.StringVar(master=self.root)
        self.cb_scripts = ttk.Combobox(top, textvariable=self.var_sel, state="readonly", width=19)
        self.cb_scripts.pack(side="left", padx=(S(6), S(6)))
        self.cb_scripts.bind("<<ComboboxSelected>>", self._on_select_script)
        ttk.Button(top, text="＋ Mới", width=6, command=self.new_script).pack(side="left")
        ttk.Button(top, text="Xoá", width=5, command=self.delete_script).pack(
            side="left", padx=(S(4), 0))

        rown = ttk.Frame(outer)
        rown.pack(fill="x", pady=(S(8), 0))
        ttk.Label(rown, text="Tên:").pack(side="left")
        self.var_sname = tk.StringVar(master=self.root)
        self.ent_sname = ttk.Entry(rown, textvariable=self.var_sname)
        self.ent_sname.pack(side="left", fill="x", expand=True, padx=(S(4), 0))
        self.var_sname.trace_add("write", lambda *a: self._on_script_name())

        row = ttk.Frame(outer)
        row.pack(fill="x", pady=(S(6), 0))
        ttk.Label(row, text="Phím chạy:").pack(side="left")
        self.lbl_skey = tk.Label(row, font=self.f_bold, bd=0, padx=S(4), pady=S(1), width=10)
        self.lbl_skey.pack(side="left", padx=(S(6), S(4)))
        self.btn_skey = ttk.Button(row, text="Gán…", width=6, command=self.begin_script_key)
        self.btn_skey.pack(side="left")
        self.btn_skey_clear = ttk.Button(row, text="Bỏ phím", width=8,
                                         command=self.clear_script_key)
        self.btn_skey_clear.pack(side="left", padx=(S(4), 0))
        ttk.Label(row, text="(không bắt buộc)", style="Small.TLabel").pack(
            side="left", padx=(S(6), 0))

        box, self.lbl_summary = self._fixed_label(outer, 2, self.f_bold, font=self.f_bold)
        box.pack(fill="x", pady=(S(10), S(4)))

        bg = ttk.Style(self.root).lookup("TFrame", "background") or self.root.cget("bg")
        box = ttk.Frame(outer)
        box.pack(fill="x")
        self.sc_canvas = tk.Canvas(box, highlightthickness=0, bd=0, bg=bg, width=S(340),
                                   height=S(LIST_H))         # cao cố định, dài quá thì cuộn
        self.sc_canvas.pack(side="left", fill="x", expand=True)
        self.sc_bar = ttk.Scrollbar(box, orient="vertical", command=self.sc_canvas.yview)
        self.sc_canvas.configure(yscrollcommand=self.sc_bar.set)
        self.sc_inner = ttk.Frame(self.sc_canvas)
        self._sc_item = self.sc_canvas.create_window(0, 0, window=self.sc_inner, anchor="nw")
        self.sc_inner.bind("<Configure>", self._on_script_list_size)
        self.sc_canvas.bind("<Configure>",
                            lambda e: self.sc_canvas.itemconfigure(self._sc_item, width=e.width))
        self.root.bind_all("<MouseWheel>", self._on_script_wheel, add="+")

        add = ttk.Frame(outer)
        add.pack(fill="x", pady=(S(8), 0))
        self.mb_add = ttk.Menubutton(add, text="＋ Thêm bước")
        self.menu_add = tk.Menu(self.mb_add, tearoff=0, postcommand=self._fill_add_menu)
        self.mb_add.configure(menu=self.menu_add)
        self.mb_add.pack(side="left")
        ttk.Button(add, text="＋ Tất cả nút có phím", command=self.add_all_steps).pack(
            side="left", padx=(S(8), 0))

        loop = ttk.Frame(outer)
        loop.pack(fill="x", pady=(S(10), 0))
        ttk.Label(loop, text="Loop:", font=self.f_bold).pack(side="left")
        self.var_loops = tk.StringVar(master=self.root, value="1")
        self.sp_loops = ttk.Spinbox(loop, from_=1, to=999999, increment=1, width=7,
                                    textvariable=self.var_loops)
        self.sp_loops.pack(side="left", padx=(S(6), S(4)))
        ttk.Label(loop, text="lần").pack(side="left")
        self.var_forever = tk.BooleanVar(master=self.root, value=False)
        ttk.Checkbutton(loop, text="Lặp vĩnh viễn", variable=self.var_forever,
                        command=self._on_forever).pack(side="left", padx=(S(14), 0))
        self.var_loops.trace_add("write", lambda *a: self._on_loops())
        # Ô tick: nhấn F9 thì chạy CÙNG LÚC mọi combo có tick ô này.
        self.var_f9 = tk.BooleanVar(master=self.root, value=True)
        self.cb_f9 = ttk.Checkbutton(outer, variable=self.var_f9, command=self._on_f9,
                                     text="Chạy khi nhấn %s  (chạy cùng lúc các combo có tick)"
                                     % run_key)
        self.cb_f9.pack(anchor="w", pady=(S(6), 0))
        # Ô tick: đang chạy combo thì phím của các nút trong combo (vd A, S) không bấm tay được.
        self.var_lock = tk.BooleanVar(master=self.root, value=True)
        self.cb_lock = ttk.Checkbutton(outer, variable=self.var_lock, command=self._on_lock,
                                       text="Khoá phím các nút trong combo khi đang chạy")
        self.cb_lock.pack(anchor="w", pady=(S(2), 0))

        run = ttk.Frame(outer)
        run.pack(fill="x", pady=(S(10), 0))
        self.btn_run = ttk.Button(run, text="▶  Chạy  (%s)" % run_key, command=self.run_script)
        self.btn_run.pack(side="left")
        self.btn_stop = ttk.Button(run, text="■  Dừng  (Esc)", command=self.stop_script)
        self.btn_stop.pack(side="left", padx=(S(8), 0))
        self.btn_test = ttk.Button(run, text="Thử combo này", command=self.test_script)
        self.btn_test.pack(side="left", padx=(S(8), 0))
        box, self.lbl_script = self._fixed_label(outer, 2, self.f_small, style="Notice.TLabel")
        box.pack(fill="x", pady=(S(6), 0))
        ttk.Label(outer, style="Small.TLabel", justify="left", text=(
            "• %s: chạy cùng lúc các combo có tick “Chạy khi nhấn %s”.\n"
            "• Phím chạy riêng: chạy / dừng riêng combo đó.  Esc: dừng hết.\n"
            "• Script có lặp: nhấn phím chạy lần nữa để dừng.\n"
            "• “chờ” = thời gian chờ trước khi chạy bước tiếp theo."
            % (run_key, run_key))).pack(anchor="w", pady=(S(4), 0))
        self._update_script_buttons()

    def _fixed_label(self, parent, lines, line_font, **kw):
        """Ô chữ cao cố định `lines` dòng: chữ thay đổi mà cửa sổ không co giãn, không nhảy."""
        box = ttk.Frame(parent, height=lines * line_font.metrics("linespace") + self.px(2))
        box.pack_propagate(False)
        lbl = ttk.Label(box, wraplength=self.px(340), justify="left", anchor="nw", **kw)
        lbl.pack(fill="both", expand=True)
        return box, lbl

    def _on_script_list_size(self, e=None):
        """Danh sách dài quá thì hiện thanh cuộn (khung luôn cao như nhau, cửa sổ không nhảy)."""
        h = self.sc_inner.winfo_reqheight()
        max_h = self.px(LIST_H)
        self.sc_canvas.configure(scrollregion=(0, 0, self.sc_inner.winfo_reqwidth(), h))
        need = h > max_h
        if need and not self._sc_bar_on:
            self.sc_bar.pack(side="right", fill="y")
        elif not need and self._sc_bar_on:
            self.sc_bar.pack_forget()
            self.sc_canvas.yview_moveto(0)
        self._sc_bar_on = need

    def _on_script_wheel(self, e):
        if not self._sc_bar_on:
            return
        w = self.root.winfo_containing(e.x_root, e.y_root)
        if w is not None and str(w).startswith(str(self.sc_canvas)):
            self.sc_canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")

    @staticmethod
    def _step_desc(c):
        side = {"left": "trái", "right": "phải", "middle": "giữa"}.get(c.button, "trái")
        if c.mode == "hold":
            return "giữ chuột %s trong lúc chờ" % side
        if c.mode == "turbo":
            return "turbo chuột %s trong lúc chờ" % side
        if c.mode == "swipe":
            return "vuốt chuột %s (%d ms)" % (side, c.swipe_ms)
        return "click chuột %s" % side

    # ---- dữ liệu script ----
    def _new_script(self, name=None, key=None, steps=None, loops=1, forever=False, lock=True,
                    f9=True):
        """lock: khoá phím các nút trong combo khi đang chạy (mặc định bật);
        f9: chạy khi nhấn F9 — F9 chạy CÙNG LÚC mọi combo có tick này (mặc định bật)."""
        self._sid_seq += 1
        return {"id": self._sid_seq, "name": name or "Combo %d" % self._sid_seq, "key": key,
                "loops": int(loops), "forever": bool(forever), "steps": list(steps or []),
                "lock": bool(lock), "f9": bool(f9)}

    def _script(self, sid):
        for sc in self.scripts:
            if sc["id"] == sid:
                return sc
        return None

    def _sel_script(self):
        return self._script(self.sel_sid)

    @staticmethod
    def _script_loops(sc):
        return None if sc["forever"] else sc["loops"]

    def _script_targets(self, sc):
        return [(self.circles[st["cid"]].target(), st["delay"])
                for st in sc["steps"] if st["cid"] in self.circles]

    def _step_keys(self, sc):
        """Phím của các nút trong script, theo thứ tự bước (không lặp lại)."""
        out = []
        for st in sc["steps"]:
            c = self.circles.get(st["cid"])
            if c is not None and c.key is not None and c.key not in out:
                out.append(c.key)
        return out

    def _lock_keys(self, sc):
        """Ô "Khoá phím…" có tick: các phím này không bấm tay được khi script đang chạy."""
        return frozenset(self._step_keys(sc)) if sc["lock"] else frozenset()

    def _sync_scripts(self):
        """Báo cho engine phím nào chạy script nào (gọi lại mỗi khi nút / script thay đổi)."""
        m = {}
        for sc in self.scripts:
            if sc["key"] is not None:
                steps = self._script_targets(sc)
                if steps:
                    m[sc["key"]] = (sc["id"], steps, self._script_loops(sc), self._lock_keys(sc))
        self.engine.set_script_keys(m)

    def _circle_label(self, c):
        if c.key is not None:
            return vk_label(c.key, self.api)
        return "#%d" % (list(self.circles).index(c.id) + 1)

    def _script_title(self, n, sc):
        tags = []
        if sc["key"] is not None:
            tags.append(vk_label(sc["key"], self.api))
        if sc["f9"]:
            tags.append(vk_label(self.engine.script_vk))
        return "%d. %s  [%s]" % (n + 1, sc["name"] or "(không tên)", ", ".join(tags) or "–")

    def _scripts_data(self):
        """Script để lưu vào file: bước trỏ tới nút bằng số thứ tự trong danh sách nút."""
        index = dict((cid, i) for i, cid in enumerate(self.circles))
        out = []
        for sc in self.scripts:
            out.append({"name": sc["name"], "key": sc["key"], "loops": sc["loops"],
                        "forever": sc["forever"], "lock_keys": sc["lock"], "f9": sc["f9"],
                        "steps": [{"button": index[st["cid"]], "delay": st["delay"]}
                                  for st in sc["steps"] if st["cid"] in index]})
        return out

    def _install_scripts(self, raw, created, buttons, sel=0, legacy_loops=1, legacy_forever=False):
        """Dựng lại danh sách script sau khi đã tạo các nút (created: theo thứ tự trong file)."""
        self.scripts = []
        parsed = parse_scripts(raw, len(created))
        reserved = {self.engine.toggle_vk, self.engine.script_vk, VK_ESCAPE}
        if parsed is None:             # file của bản cũ (≤ 1.3): 1 script gồm các nút có phím
            steps = [{"cid": c.id, "delay": b.get("delay", DEFAULT_DELAY_MS)}
                     for b, c in zip(buttons, created)
                     if c.key is not None and b.get("in_script", True)]
            self.scripts.append(self._new_script("Script 1", None, steps, legacy_loops,
                                                 legacy_forever))
        else:
            used = set(c.key for c in created if c.key is not None) | reserved
            for p in parsed:
                key = p["key"] if p["key"] not in used else None
                if key is not None:
                    used.add(key)
                steps = [{"cid": created[s["button"]].id, "delay": s["delay"]} for s in p["steps"]]
                self.scripts.append(self._new_script(p["name"] or None, key, steps, p["loops"],
                                                     p["forever"], p["lock"], p["f9"]))
        if not self.scripts:
            self.scripts.append(self._new_script())
        if not (isinstance(sel, int) and not isinstance(sel, bool) and 0 <= sel < len(self.scripts)):
            sel = 0
        self.sel_sid = self.scripts[sel]["id"]
        self._script_sig = None

    def _script_changed(self):
        self._sync_scripts()
        self._refresh_script_tab()
        self._schedule_save()

    # ---- hiển thị tab Script ----
    def _refresh_script_tab(self, force=False):
        if self._sel_script() is None and self.scripts:
            self.sel_sid = self.scripts[0]["id"]
        sc = self._sel_script()
        self._refresh_script_selector()
        sig = None
        if sc is not None:
            sig = (sc["id"], sc["forever"] or sc["loops"] != 1,
                   tuple((st["cid"], self._circle_sig(st["cid"])) for st in sc["steps"]))
        if force or sig != self._script_sig:
            self._script_sig = sig
            self._load_script_fields(sc)
            self._rebuild_script_rows(sc)
        self._update_skey_label()
        self._update_script_summary()
        self._update_script_buttons()

    def _circle_sig(self, cid):
        c = self.circles.get(cid)
        if c is None:
            return None
        return (self._circle_label(c), c.button, c.mode, c.swipe_ms)

    def _refresh_script_selector(self):
        titles = [self._script_title(n, sc) for n, sc in enumerate(self.scripts)]
        self.cb_scripts.configure(values=titles)
        sc = self._sel_script()
        self.var_sel.set(titles[self.scripts.index(sc)] if sc is not None else "")

    def _load_script_fields(self, sc):
        self._loading_script_ui = True
        try:
            self.var_sname.set(sc["name"] if sc else "")
            self.var_loops.set(str(sc["loops"]) if sc else "1")
            self.var_forever.set(bool(sc["forever"]) if sc else False)
            self.sp_loops.state(["disabled"] if (sc is None or sc["forever"]) else ["!disabled"])
            self.var_lock.set(bool(sc["lock"]) if sc else True)
            self.var_f9.set(bool(sc["f9"]) if sc else True)
        finally:
            self._loading_script_ui = False

    def _update_skey_label(self):
        sc = self._sel_script()
        has_key = sc is not None and sc["key"] is not None
        if self._script_capture is not None:
            self.lbl_skey.configure(text="nhấn phím…", bg="#facc15", fg="#422006")
            self.btn_skey.configure(text="Huỷ")
        elif has_key:
            self.lbl_skey.configure(text=vk_label(sc["key"], self.api), bg="#0f172a", fg="#ffffff")
            self.btn_skey.configure(text="Đổi…")
        else:
            self.lbl_skey.configure(text="không có", bg="#e2e8f0", fg="#64748b")
            self.btn_skey.configure(text="Gán…")
        self.btn_skey_clear.state(["!disabled"] if (has_key and self._script_capture is None)
                                  else ["disabled"])

    def _rebuild_script_rows(self, sc):
        S = self.px
        for w in self.sc_inner.winfo_children():
            w.destroy()
        self._script_vars = []
        steps = [st for st in sc["steps"] if st["cid"] in self.circles] if sc else []
        if not steps:
            ttk.Label(self.sc_inner, style="Small.TLabel", justify="left", text=(
                "Chưa có bước nào.\n"
                "Bấm “＋ Thêm bước” để chọn nút sẽ chạy (thêm lần lượt theo thứ tự).")).pack(
                anchor="w", pady=S(6))
            return
        looping = sc["forever"] or sc["loops"] != 1
        for n, st in enumerate(steps):
            c = self.circles[st["cid"]]
            last = n == len(steps) - 1
            row = ttk.Frame(self.sc_inner)
            row.pack(fill="x", pady=(S(3), 0))
            ttk.Label(row, text="%d." % (n + 1), width=3, style="Small.TLabel").pack(side="left")
            tk.Label(row, text=self._circle_label(c), font=self.f_bold, bd=0, padx=S(8),
                     pady=S(1), bg="#0f172a",
                     fg=THEME.get("text_" + c.button, "#ffffff")).pack(side="left", padx=(0, S(8)))
            ttk.Label(row, text=self._step_desc(c), style="Small.TLabel").pack(side="left")
            rm = ttk.Button(row, text="✕", width=2, command=lambda i=n: self.remove_step(i))
            down = ttk.Button(row, text="▼", width=2, command=lambda i=n: self.move_step(i, +1))
            up = ttk.Button(row, text="▲", width=2, command=lambda i=n: self.move_step(i, -1))
            rm.pack(side="right")
            down.pack(side="right", padx=(0, S(2)))
            up.pack(side="right", padx=(0, S(2)))
            if n == 0:
                up.state(["disabled"])
            if last:
                down.state(["disabled"])
            wait = ttk.Frame(self.sc_inner)
            wait.pack(fill="x", padx=(S(30), 0), pady=(S(2), S(2)))
            ttk.Label(wait, text="│  chờ", style="Small.TLabel").pack(side="left")
            v_d = tk.StringVar(master=self.root, value=str(st["delay"]))
            ttk.Spinbox(wait, from_=0, to=MAX_DELAY_MS, increment=50, width=7,
                        textvariable=v_d).pack(side="left", padx=(S(6), S(4)))
            v_d.trace_add("write", lambda *a, st=st, v=v_d: self._on_delay(st, v))
            suffix = ""
            if last and looping:
                suffix = "   ↺ rồi lặp lại"
            elif last and c.mode in ("click", "swipe"):
                suffix = "   (bước cuối: không cần chờ)"
            ttk.Label(wait, text="ms" + suffix, style="Small.TLabel").pack(side="left")
            self._script_vars.append(v_d)

    def _update_script_summary(self):
        """Dòng tóm tắt, ví dụ:  Q ▸  U – 100 ms – I – 200 ms – O"""
        sc = self._sel_script()
        if sc is None:
            self.lbl_summary.configure(text="")
            return
        tags = []                       # chạy bằng gì: phím riêng và/hoặc F9
        if sc["key"] is not None:
            tags.append(vk_label(sc["key"], self.api))
        if sc["f9"]:
            tags.append(vk_label(self.engine.script_vk))
        key = " / ".join(tags) if tags else "(không phím)"
        steps = [st for st in sc["steps"] if st["cid"] in self.circles]
        if not steps:
            self.lbl_summary.configure(text="%s ▸  (trống)" % key)
            return
        looping = sc["forever"] or sc["loops"] != 1
        parts = []
        for n, st in enumerate(steps):
            parts.append(self._circle_label(self.circles[st["cid"]]))
            if n < len(steps) - 1 or looping:
                parts.append("%d ms" % st["delay"])
        tail = ("   ↺ " + ("∞" if sc["forever"] else "×%d" % sc["loops"])) if looping else ""
        text = "%s ▸  %s%s" % (key, "  –  ".join(parts), tail)
        limit = self.px(340) * 1.75                 # ô tóm tắt chỉ có 2 dòng
        while self.f_bold.measure(text) > limit and len(parts) > 1:
            parts.pop()                             # combo dài: rút gọn bằng "…"
            text = "%s ▸  %s  …%s" % (key, "  –  ".join(parts), tail)
        self.lbl_summary.configure(text=text)

    # ---- sửa script ----
    def _on_select_script(self, e=None):
        i = self.cb_scripts.current()
        if 0 <= i < len(self.scripts):
            self._end_script_capture()
            self.sel_sid = self.scripts[i]["id"]
            self._refresh_script_tab(force=True)
            self._schedule_save()

    def new_script(self):
        sc = self._new_script()
        self.scripts.append(sc)
        self.sel_sid = sc["id"]
        self._end_script_capture()
        self._script_changed()
        if not self.enabled:                # đang chơi thì không đưa con trỏ vào ô Tên
            self.ent_sname.focus_set()
            self.ent_sname.select_range(0, "end")

    def delete_script(self):
        sc = self._sel_script()
        if sc is None:
            return
        if sc["steps"] and not messagebox.askyesno(
                APP_NAME, "Xoá script “%s”?" % (sc["name"] or "(không tên)"), parent=self.root):
            return
        if sc["id"] in self.running:
            self.stop_script(sc["id"])
        self._end_script_capture()
        i = self.scripts.index(sc)
        self.scripts.remove(sc)
        if not self.scripts:
            self.scripts.append(self._new_script())
        self.sel_sid = self.scripts[min(i, len(self.scripts) - 1)]["id"]
        self._script_changed()

    def _on_script_name(self):
        if self._loading_script_ui:
            return
        sc = self._sel_script()
        if sc is None:
            return
        name = self.var_sname.get().strip()[:40]
        if name != sc["name"]:
            sc["name"] = name
            self._refresh_script_selector()
            self._schedule_save()

    def _fill_add_menu(self):
        m = self.menu_add
        m.delete(0, "end")
        if not self.circles:
            m.add_command(label="(chưa có nút nào – tạo ở tab “Nút bấm”)", state="disabled")
            return
        for c in self.circles.values():
            m.add_command(label="%s      %s" % (self._circle_label(c), self._step_desc(c)),
                          command=lambda cid=c.id: self.add_step(cid))

    def add_step(self, cid):
        sc = self._sel_script()
        if sc is None or cid not in self.circles:
            return
        sc["steps"].append({"cid": cid, "delay": DEFAULT_STEP_DELAY_MS})
        self._script_changed()

    def add_all_steps(self):
        sc = self._sel_script()
        keyed = [c for c in self.circles.values() if c.key is not None]
        if sc is None or not keyed:
            self._script_msg("Chưa có nút nào được gán phím.")
            return
        for c in keyed:
            sc["steps"].append({"cid": c.id, "delay": DEFAULT_STEP_DELAY_MS})
        self._script_changed()

    def remove_step(self, i):
        sc = self._sel_script()
        if sc is not None and 0 <= i < len(sc["steps"]):
            del sc["steps"][i]
            self._script_changed()

    def move_step(self, i, direction):
        sc = self._sel_script()
        if sc is None:
            return
        j = i + direction
        if 0 <= i < len(sc["steps"]) and 0 <= j < len(sc["steps"]):
            sc["steps"][i], sc["steps"][j] = sc["steps"][j], sc["steps"][i]
            self._script_changed()

    def _on_delay(self, st, var):
        try:
            ms = int(str(var.get()).strip())
        except ValueError:
            return
        ms = max(0, min(MAX_DELAY_MS, ms))
        if ms != st["delay"]:
            st["delay"] = ms
            self._update_script_summary()
            self._sync_scripts()
            self._schedule_save()

    def _loops_value(self):
        try:
            n = int(str(self.var_loops.get()).strip())
        except ValueError:
            return None
        return max(1, min(999999, n))

    def _on_loops(self):
        if self._loading_script_ui:
            return
        sc, n = self._sel_script(), self._loops_value()
        if sc is not None and n is not None and n != sc["loops"]:
            sc["loops"] = n
            self._script_changed()

    def _on_forever(self):
        if self._loading_script_ui:
            return
        sc = self._sel_script()
        if sc is None:
            return
        sc["forever"] = bool(self.var_forever.get())
        self.sp_loops.state(["disabled"] if sc["forever"] else ["!disabled"])
        self._script_changed()

    def _on_f9(self):
        """Ô "Chạy khi nhấn F9": F9 chạy cùng lúc mọi combo có tick."""
        if self._loading_script_ui:
            return
        sc = self._sel_script()
        if sc is None:
            return
        sc["f9"] = bool(self.var_f9.get())
        self._script_changed()
        key = vk_label(self.engine.script_vk)
        group = [x["name"] or "script" for x in self.scripts if x["f9"]]
        if len(group) > 1:
            self._script_msg("%s chạy cùng lúc %d combo: %s." % (key, len(group), ", ".join(group)))
        elif group:
            self._script_msg("%s chạy combo: %s." % (key, group[0]))
        else:
            self._script_msg("Chưa có combo nào chạy bằng %s." % key)

    def _on_lock(self):
        """Ô "Khoá phím các nút trong combo khi đang chạy"."""
        if self._loading_script_ui:
            return
        sc = self._sel_script()
        if sc is None:
            return
        sc["lock"] = bool(self.var_lock.get())
        self._script_changed()
        if sc["id"] in self.running:              # đang chạy: áp dụng ngay
            self.engine.set_script_lock(sc["id"], self._lock_keys(sc))
        keys = ", ".join(vk_label(k, self.api) for k in self._step_keys(sc)) or "các nút"
        if sc["lock"]:
            self._script_msg("Khi “%s” đang chạy, bấm tay %s sẽ không click." % (sc["name"], keys))
        else:
            self._script_msg("Khi “%s” đang chạy vẫn bấm tay được %s." % (sc["name"], keys))

    # ---- phím chạy script ----
    def begin_script_key(self):
        sc = self._sel_script()
        if sc is None:
            return
        if self._script_capture is not None:     # đang chờ phím -> bấm lần nữa = huỷ
            self._end_script_capture()
            return
        if self.editing is not None:
            self.end_edit()
        self._script_capture = sc["id"]
        self.engine.capture_id = ("script", sc["id"])
        self._update_skey_label()
        self._script_msg("Nhấn 1 phím để làm phím chạy cho “%s”   (Esc: huỷ)"
                         % (sc["name"] or "script"))
        self._update_status()
        if self._edit_job:
            self.root.after_cancel(self._edit_job)
        self._edit_job = self.root.after(20000, self._edit_timeout)

    def _end_script_capture(self):
        if self._script_capture is None:
            return
        self._script_capture = None
        cap = self.engine.capture_id
        if isinstance(cap, tuple) and cap[0] == "script":
            self.engine.capture_id = None
        if self._edit_job:
            self.root.after_cancel(self._edit_job)
            self._edit_job = None
        self._update_skey_label()
        self._script_msg("")
        self._update_status()

    def _on_script_key_captured(self, sid, vk):
        if self._script_capture != sid:
            return
        sc = self._script(sid)
        if vk == VK_ESCAPE or sc is None:
            self._end_script_capture()
            return
        name = vk_label(vk, self.api)
        if any(c.key == vk for c in self.circles.values()):
            # Phím của nút tròn luôn để click như thường: combo không được lấy mất.
            self.engine.capture_id = ("script", sid)          # vẫn chờ phím khác
            if self._edit_job:
                self.root.after_cancel(self._edit_job)
            self._edit_job = self.root.after(20000, self._edit_timeout)
            self._script_msg("%s là phím của nút tròn (vẫn để click như thường). "
                             "Nhấn phím khác – Esc: huỷ." % name)
            return
        self._end_script_capture()
        self._claim_key(vk, ("script", sid))
        sc["key"] = vk
        self._script_msg("Phím chạy của “%s”: %s" % (sc["name"] or "script", name))
        self.layout_changed()

    def clear_script_key(self):
        """Bỏ phím chạy của script đang chọn: không cần phím riêng. Các phím của nút vẫn
        click bình thường; muốn chạy combo thì nhấn F9 hoặc nút ▶ Chạy."""
        sc = self._sel_script()
        self._end_script_capture()
        if sc is None or sc["key"] is None:
            return
        sc["key"] = None
        self._script_changed()
        key = vk_label(self.engine.script_vk)
        if sc["f9"]:
            how = "combo này chạy bằng %s." % key
        else:
            how = "tick “Chạy khi nhấn %s” để chạy combo bằng %s." % (key, key)
        self._script_msg("Đã bỏ phím chạy. Phím các nút vẫn click như thường; " + how)

    def _claim_key(self, vk, owner):
        """1 phím chỉ làm 1 việc: lấy phím vk khỏi nút / script khác đang dùng nó."""
        name = vk_label(vk, self.api)
        for c in self.circles.values():
            if c.key == vk and owner != ("circle", c.id):
                c.key = None
                c.flash(THEME["warn"], 700)
                c.redraw()
                self.notify("Phím %s đã chuyển từ nút cũ sang chỗ mới." % name)
        for sc in self.scripts:
            if sc["key"] == vk and owner != ("script", sc["id"]):
                sc["key"] = None
                msg = "Phím %s chuyển từ script “%s” sang chỗ mới." % (name, sc["name"] or "script")
                if sc["f9"]:
                    msg += " Script đó vẫn chạy bằng %s." % vk_label(self.engine.script_vk)
                self.notify(msg)
                self._script_msg(msg)

    # ---- chạy / dừng ----
    #  Nhiều combo chạy CÙNG LÚC được:
    #   - F9 (hoặc nút "▶ Chạy (F9)"): chạy cùng lúc mọi combo có tick "Chạy khi nhấn F9";
    #     đang có combo chạy thì F9 = dừng hết.
    #   - Phím chạy riêng của combo: chạy / dừng riêng combo đó (combo khác vẫn chạy).
    #   - Esc: dừng hết.
    def _update_script_buttons(self):
        self.btn_run.state(["disabled"] if self.running else ["!disabled"])
        self.btn_stop.state(["!disabled"] if self.running else ["disabled"])
        sel = self.sel_sid
        self.btn_test.state(["disabled"] if (sel is None or sel in self.running)
                            else ["!disabled"])

    def _script_msg(self, text):
        self.lbl_script.configure(text=text)

    def _script_name(self, sid):
        sc = self._script(sid)
        return (sc["name"] or "script") if sc else "script"

    def _f9_scripts(self):
        """Các combo có tick "Chạy khi nhấn F9" và có ít nhất 1 bước."""
        return [sc for sc in self.scripts if sc["f9"] and self._script_targets(sc)]

    def _can_run(self):
        if self.hook_error:
            self._script_msg("Không chạy được: KeyClick không bắt được phím nên không dừng "
                             "script bằng Esc được.")
            return False
        if self.editing is not None:
            self.end_edit()
        self._end_script_capture()
        if not self.enabled:
            self.set_enabled(True)          # chế độ chơi: nút tròn để chuột đi xuyên qua
        return True

    def _start(self, sc):
        loops = self._script_loops(sc)
        self.running[sc["id"]] = loops
        self.engine.start_script(sc["id"], self._script_targets(sc), loops, self._lock_keys(sc))

    def run_script(self):
        """Phím F9 / nút "▶ Chạy (F9)": chạy CÙNG LÚC các combo có tick "Chạy khi nhấn F9"."""
        if self.running:
            return
        group = self._f9_scripts()
        if not group:
            sc = self._sel_script()
            if sc is not None and not self._script_targets(sc):
                text = "Script “%s” chưa có bước nào: bấm “＋ Thêm bước”." % sc["name"]
            else:
                text = "Chưa có combo nào tick “Chạy khi nhấn %s”." % vk_label(self.engine.script_vk)
            self._script_msg(text)
            self.toast.show("Chưa có combo nào để chạy", self.root.winfo_screenwidth() // 2,
                            self.px(28), "n", "#334155", "#ffffff", ms=1500)
            return
        if not self._can_run():
            return
        self._quiet_start = set(sc["id"] for sc in group)
        for sc in group:
            self._start(sc)
        names = ", ".join("“%s”" % (sc["name"] or "script") for sc in group)
        if len(group) == 1:
            self._script_msg("Đang chạy %s…   (Esc để dừng)" % names)
            toast = "Script %s: CHẠY  –  Esc để dừng" % names
        else:
            self._script_msg("Đang chạy cùng lúc %d combo: %s   (Esc: dừng hết)"
                             % (len(group), names))
            toast = "Chạy cùng lúc %d combo  –  Esc để dừng" % len(group)
        self.toast.show(toast, self.root.winfo_screenwidth() // 2, self.px(28), "n", "#6d28d9",
                        "#ffffff", ms=1500)
        self._update_status()
        self._update_script_buttons()

    def test_script(self):
        """Nút "Thử combo này": chạy riêng combo đang chọn (để thử lúc đang sửa)."""
        sc = self._sel_script()
        if sc is None or sc["id"] in self.running:
            return
        if not self._script_targets(sc):
            self._script_msg("Script “%s” chưa có bước nào: bấm “＋ Thêm bước”." % sc["name"])
            return
        if not self._can_run():
            return
        self._start(sc)
        self._script_msg("Đang thử “%s”…   (Esc để dừng)" % (sc["name"] or "script"))
        self._update_status()
        self._update_script_buttons()

    def stop_script(self, sid=None):
        """Dừng 1 combo (sid) hoặc tất cả combo đang chạy."""
        if sid is None:
            if self.running:
                self.engine.stop_script()
        elif sid in self.running:
            self.engine.stop_script(sid)

    def _on_script_started(self, sid, loops):
        self.running[sid] = loops
        self._update_status()
        self._update_script_buttons()
        if sid in self._quiet_start:                # chạy theo nhóm F9: đã báo 1 lần rồi
            self._quiet_start.discard(sid)
        elif loops != 1:                            # combo 1 lần bấm bằng phím: không báo
            self.toast.show("Script “%s”: CHẠY  –  Esc để dừng" % self._script_name(sid),
                            self.root.winfo_screenwidth() // 2, self.px(28), "n", "#6d28d9",
                            "#ffffff", ms=1500)

    def _on_script_progress(self, sid, n, loops):
        if len(self.running) > 1:                   # nhiều combo cùng chạy: giữ dòng tổng
            return
        name = self._script_name(sid)
        if loops == 1:
            self._script_msg("“%s” đang chạy…" % name)
        else:
            self._script_msg("“%s” đang chạy · vòng %d/%s   (Esc để dừng)"
                             % (name, n, "∞" if loops is None else loops))

    def _on_script_done(self, sid, reason, done):
        if sid is None:
            loops = None
            self.running.clear()
        else:
            loops = self.running.pop(sid, 1)
        self._quiet_start.discard(sid)
        looping = loops != 1
        self._update_status()
        self._update_script_buttons()
        name = self._script_name(sid)
        if reason == "error":
            msg = "Script dừng vì có lỗi (xem keyclick.log)."
        elif reason == "empty":
            msg = "Script “%s” chưa có bước nào." % name
        elif sid is None:
            msg = "Đã dừng."
        elif reason == "done":
            msg = "“%s”: xong%s." % (name, " %d vòng" % done if looping else "")
        else:
            msg = "“%s”: đã dừng%s." % (name, " sau %d vòng" % done if looping else "")
        if self.running:                            # còn combo khác đang chạy
            msg += "  Còn %d combo đang chạy." % len(self.running)
        self._script_msg(msg)
        if looping or reason == "error":
            toast = {"done": "XONG", "error": "LỖI"}.get(reason, "DỪNG")
            text = ("Script “%s”: %s" % (name, toast)) if self.running or sid is not None \
                else "Script: %s" % toast
            if not self.running and reason == "stopped":
                text = "Đã dừng hết combo"
            self.toast.show(text, self.root.winfo_screenwidth() // 2, self.px(28), "n",
                            "#334155", "#ffffff", ms=1300)

    def _set_icon(self):
        try:
            self._icon = tk.PhotoImage(master=self.root, data=ICON_PNG_B64)
            self.root.iconphoto(True, self._icon)
        except Exception:
            pass

    def _place_main_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        vx, vy, vw, vh = self.vscreen()
        pos = self._window_pos
        if not (pos and vx <= pos[0] <= vx + vw - 120 and vy <= pos[1] <= vy + vh - 80):
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            pos = (max(0, (sw - w) // 2), max(0, (sh - h) // 3))
        self.root.geometry("+%d+%d" % (pos[0], pos[1]))

    def _window_position(self):
        m = re.match(r"^\d+x\d+\+(-?\d+)\+(-?\d+)$", self.root.geometry())
        return [int(m.group(1)), int(m.group(2))] if m else None

    def _update_status(self):
        key = vk_label(self.engine.toggle_vk)
        if self.hook_error:
            text, bg, fg = "⚠  Không bắt được phím: " + self.hook_error, "#fee2e2", "#991b1b"
        elif len(self.running) > 1:
            text = "▶  %d combo ĐANG CHẠY – Esc: dừng hết" % len(self.running)
            bg, fg = "#ede9fe", "#5b21b6"
        elif self.running:
            text = "▶  “%s” ĐANG CHẠY – Esc để dừng" % self._script_name(next(iter(self.running)))
            bg, fg = "#ede9fe", "#5b21b6"
        elif self.editing is not None:
            text, bg, fg = "✎  Nhấn 1 phím để gán cho nút  (Esc: huỷ)", "#fef9c3", "#854d0e"
        elif self._script_capture is not None:
            text, bg, fg = "✎  Nhấn 1 phím làm phím chạy  (Esc: huỷ)", "#fef9c3", "#854d0e"
        elif self.enabled and self.engine.typing == "text":
            text, bg, fg = "✎  Đang gõ chữ – phím tạm không click", "#fef9c3", "#854d0e"
        elif self.enabled and self.engine.typing == "number":
            text, bg, fg = "✎  Đang sửa số – phím số để gõ", "#fef9c3", "#854d0e"
        elif self.enabled:
            text, bg, fg = "●  ĐANG BẬT – nhấn phím để click  (%s: tắt)" % key, "#dcfce7", "#166534"
        else:
            text, bg, fg = "○  ĐANG TẮT – kéo/sửa nút tròn  (%s: bật)" % key, "#e2e8f0", "#334155"
        self.status.configure(text=text, bg=bg, fg=fg)

    def _update_counts(self):
        n = len(self.circles)
        keys = [vk_label(c.key, self.api) for c in self.circles.values() if c.key is not None]
        if n == 0:
            text = "Chưa có nút nào – bấm “＋ Thêm nút” để tạo."
        else:
            text = "%d nút · đã gán %d phím" % (n, len(keys))
            if keys:                    # vừa 1 dòng
                text += ": " + ", ".join(keys[:8]) + ("…" if len(keys) > 8 else "")
        self.lbl_count.configure(text=text)

    def notify(self, text, ms=5000):
        self.lbl_notice.configure(text=text)
        if self._notice_job:
            self.root.after_cancel(self._notice_job)
        self._notice_job = self.root.after(ms, lambda: self.lbl_notice.configure(text=""))

    # ------------------------------------------------------------------ 3 ô tick
    def _on_cb_enabled(self):
        self.set_enabled(self.var_enabled.get())

    def _on_cb_return(self):
        on = bool(self.var_return.get())
        self.engine.return_cursor = on
        self.cfg["return_cursor"] = on
        self._schedule_save()

    def _on_cb_show(self):
        self.set_show(self.var_show.get())

    def _on_cb_admin(self):
        """Ô "Luôn chạy bằng quyền Admin": lần sau mở KeyClick sẽ tự xin quyền Admin."""
        on = bool(self.var_admin.get())
        self.cfg["run_as_admin"] = on
        self.save_config()
        if not on:
            self.notify("Lần sau mở, KeyClick sẽ chạy bình thường (không xin quyền Admin).")
        elif self._is_admin:
            self.notify("Lần sau mở, KeyClick sẽ tự chạy bằng quyền Admin.")
        elif messagebox.askyesno(
                APP_NAME, "Chạy lại KeyClick bằng quyền Admin ngay bây giờ?\n\n"
                "Từ giờ mỗi lần mở, KeyClick sẽ tự xin quyền Admin (Windows hỏi Yes/No).",
                parent=self.root):
            self.relaunch_admin()
        else:
            self.notify("Lần sau mở, KeyClick sẽ tự xin quyền Admin.")

    def _on_bg_alpha(self, value=None):
        """Thanh trượt "Độ đậm nền nút": chỉ đổi độ mờ của NỀN, chữ vẫn rõ."""
        pct = max(5, min(100, int(round(float(self.var_bg.get())))))
        self.lbl_bg.configure(text="%d%%" % pct)
        alpha = pct / 100.0
        if alpha == self.cfg["bg_alpha"]:
            return
        self.cfg["bg_alpha"] = alpha
        for c in self.circles.values():
            c.apply_alpha()
        self._schedule_save()

    def set_enabled(self, on, from_hotkey=False):
        on = bool(on)
        if on and self.hook_error:
            self.var_enabled.set(False)
            self.notify("Không bật được: " + self.hook_error)
            return
        if on and self.editing is not None:
            self.end_edit()
        if on:
            self._end_script_capture()
            self._stop_typing()             # đang gõ dở trong ô Tên/ô số: thôi gõ, phím click
        changed = on != self.enabled
        self.enabled = on
        self.var_enabled.set(on)
        self.engine.enabled = on
        if not on:
            self.stop_script()              # tắt phím tắt = dừng luôn script
            self.engine.release_all()
        for c in self.circles.values():
            c.apply_mode()
        self._update_status()
        if from_hotkey:
            self.show_toast(on)
        if (on and changed and not any(c.key is not None for c in self.circles.values())
                and not any(sc["key"] is not None for sc in self.scripts)):
            self.notify("Chưa có nút nào được gán phím. Bấm “＋ Thêm nút” để tạo.")

    def set_show(self, on):
        on = bool(on)
        if not on and self.editing is not None:
            self.end_edit()
        self.show_buttons = on
        self.var_show.set(on)
        self.cfg["show_buttons"] = on
        for c in self.circles.values():
            c.apply_mode()
        self._schedule_save()

    def show_toast(self, on):
        if on:
            text, bg = "KeyClick: BẬT  –  nhấn phím để click", "#15803d"
        else:
            text, bg = "KeyClick: TẮT  –  có thể chỉnh nút", "#334155"
        self.toast.show(text, self.root.winfo_screenwidth() // 2, self.px(28), "n", bg,
                        "#ffffff", ms=1300)

    # ------------------------------------------------------------------ nút tròn
    def _create_circle(self, cx, cy, size, key=None, button="left", mode="click",
                       x2=None, y2=None, swipe_ms=DEFAULT_SWIPE_MS):
        cx, cy = self.clamp_point(cx, cy)
        if x2 is not None and y2 is not None:
            x2, y2 = self.clamp_point(x2, y2)
        c = Circle(self, cx, cy, size, key, button, mode, x2, y2, swipe_ms)
        self.circles[c.id] = c
        return c

    def _create_from_dict(self, b):
        return self._create_circle(b["x"], b["y"], b["size"] or self.default_size(),
                                   b["key"], b["mouse"], b["mode"],
                                   b.get("x2"), b.get("y2"), b.get("swipe_ms", DEFAULT_SWIPE_MS))

    def _create_buttons(self, buttons):
        """Tạo các nút từ file; trả về danh sách nút theo đúng thứ tự trong file."""
        created, used = [], set()
        for b in buttons:
            if b["key"] is not None and b["key"] in used:   # trùng phím -> bỏ phím
                b["key"] = None
            used.add(b["key"])
            created.append(self._create_from_dict(b))
        return created

    def add_circle(self, mode="click"):
        if self.enabled:
            self.set_enabled(False)
        if not self.show_buttons:
            self.set_show(True)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        x, y = sw // 2, sh // 2
        step = self.px(44)
        for _ in range(60):            # tránh đè lên nút đã có
            if not any(abs(c.cx - x) < step // 2 and abs(c.cy - y) < step // 2
                       for c in self.circles.values()):
                break
            x += step
            if x > sw - step:
                x, y = sw // 2 - 4 * step, y + step
        c = self._create_circle(x, y, self.default_size(), mode=mode)
        c.start_edit()
        self.layout_changed()
        return c

    def duplicate(self, src, offset=True, start_edit=True):
        if self.enabled:
            self.set_enabled(False)
        x, y = src.cx, src.cy
        if offset:
            gap = src.size + self.px(10)
            vx, vy, vw, vh = self.vscreen()
            x = src.cx + gap if src.cx + gap + src.size // 2 < vx + vw else src.cx - gap
        x2 = y2 = None
        if src.x2 is not None:           # nút vuốt: bản sao giữ nguyên hướng vuốt
            x2, y2 = src.x2 + x - src.cx, src.y2 + y - src.cy
        c = self._create_circle(x, y, src.size, None, src.button, src.mode, x2, y2, src.swipe_ms)
        if start_edit:
            c.start_edit()
        self.layout_changed()
        return c

    def delete_circle(self, c):
        if self.editing is c:
            self.end_edit()
        for sc in self.scripts:                # bỏ nút này khỏi các script
            sc["steps"] = [st for st in sc["steps"] if st["cid"] != c.id]
        self.circles.pop(c.id, None)
        c.destroy()
        self.layout_changed()

    def clear_all(self):
        if not self.circles:
            return
        if not messagebox.askyesno(APP_NAME, "Xoá tất cả %d nút?" % len(self.circles),
                                   parent=self.root):
            return
        for c in list(self.circles.values()):
            self.delete_circle(c)

    def set_circle_prop(self, c, prop, value):
        if prop == "mode":
            c.set_mode(value)            # chuyển sang/khỏi "vuốt" thì hiện/ẩn mũi tên
        else:
            setattr(c, prop, value)
            c.redraw()
        self.layout_changed()

    def clear_key(self, c):
        c.key = None
        c.redraw()
        self.layout_changed()

    def set_turbo_interval(self, ms):
        self.cfg["turbo_interval_ms"] = int(ms)
        self.engine.set_timing(turbo_interval_ms=int(ms))
        self._schedule_save()

    def show_circle_menu(self, c, x, y):
        m = tk.Menu(self.root, tearoff=0)
        vb = tk.StringVar(master=self.root, value=c.button)
        vm = tk.StringVar(master=self.root, value=c.mode)
        vt = tk.IntVar(master=self.root, value=int(self.cfg["turbo_interval_ms"]))
        current = vk_label(c.key, self.api) if c.key is not None else "chưa có"
        m.add_command(label="Gán phím…   (đang là: %s)" % current, command=c.start_edit)
        m.add_command(label="Nhân bản", command=lambda: self.duplicate(c))
        m.add_separator()
        for val, text in (("left", "Click chuột trái"), ("right", "Click chuột phải"),
                          ("middle", "Click chuột giữa")):
            m.add_radiobutton(label=text, value=val, variable=vb,
                              command=lambda v=val: self.set_circle_prop(c, "button", v))
        m.add_separator()
        for val, text in (("click", "Nhấn phím = click 1 lần"),
                          ("hold", "Giữ phím = giữ chuột (kéo / ngắm skill)"),
                          ("turbo", "Giữ phím = click liên tục (turbo)"),
                          ("swipe", "Nhấn phím = vuốt (từ nút tới chấm vàng)")):
            m.add_radiobutton(label=text, value=val, variable=vm,
                              command=lambda v=val: self.set_circle_prop(c, "mode", v))
        sub = tk.Menu(m, tearoff=0)
        for cps in (5, 10, 15, 20, 30):
            ms = int(round(1000.0 / cps))
            sub.add_radiobutton(label="%d lần/giây" % cps, value=ms, variable=vt,
                                command=lambda v=ms: self.set_turbo_interval(v))
        m.add_cascade(label="Tốc độ turbo", menu=sub)
        vs = tk.IntVar(master=self.root, value=c.swipe_ms)
        sub2 = tk.Menu(m, tearoff=0)
        for ms in (100, 200, 300, 500, 800, 1200):
            sub2.add_radiobutton(label="%d ms%s" % (ms, "  (nhanh)" if ms == 100 else ""),
                                 value=ms, variable=vs,
                                 command=lambda v=ms: self.set_circle_prop(c, "swipe_ms", v))
        m.add_cascade(label="Thời gian vuốt", menu=sub2,
                      state="normal" if c.mode == "swipe" else "disabled")
        m.add_separator()
        m.add_command(label="To hơn", command=lambda: c.resize(+6))
        m.add_command(label="Nhỏ hơn", command=lambda: c.resize(-6))
        m.add_separator()
        m.add_command(label="Bỏ gán phím", command=lambda: self.clear_key(c),
                      state="normal" if c.key is not None else "disabled")
        m.add_command(label="Xoá nút này", command=lambda: self.delete_circle(c))
        self._menu_refs = (m, sub, sub2, vb, vm, vt, vs)
        try:
            self.api.force_foreground(c.hwnd)   # để menu tự đóng khi bấm ra ngoài
        except Exception:
            pass
        try:
            m.tk_popup(x, y)
        finally:
            m.grab_release()
            self._raise_circle(c)

    def _raise_circle(self, c):
        """Đưa nút lên trên cùng: lớp nền trước, lớp chữ sau (chữ luôn nằm trên nền)."""
        try:
            self.api.set_topmost(c.hwnd)
            self.api.set_topmost(c.fhwnd)
        except Exception:
            log_exc("raise")

    # ------------------------------------------------------------------ gán phím
    def begin_edit(self, c):
        if self.enabled:
            self.set_enabled(False)
        self._end_script_capture()
        prev = self.editing
        if prev is not None and prev is not c:
            prev.editing = False
            prev.stop_caret()
            prev.apply_mode()
        self.editing = c
        c.editing = True
        c.start_caret()
        c.apply_mode()
        self.engine.capture_id = ("circle", c.id)
        self.position_hint(c)
        self._update_status()
        if self._edit_job:
            self.root.after_cancel(self._edit_job)
        self._edit_job = self.root.after(20000, self._edit_timeout)

    def end_edit(self):
        c, self.editing = self.editing, None
        cap = self.engine.capture_id
        if cap is None or (isinstance(cap, tuple) and cap[0] == "circle"):
            self.engine.capture_id = None
        if self._edit_job:
            self.root.after_cancel(self._edit_job)
            self._edit_job = None
        if c is not None:
            c.editing = False
            c.stop_caret()
            c.apply_mode()
        self.hint.hide()
        self._update_status()

    def _edit_timeout(self):
        self._edit_job = None
        if self.editing is not None:
            self.end_edit()
        self._end_script_capture()

    def position_hint(self, c):
        text = "Nhấn 1 phím để gán  ·  Esc: huỷ"
        vx, vy, vw, vh = self.vscreen()
        above = c.cy - c.size // 2 - self.px(8)
        if above - self.px(40) > vy:
            self.hint.show(text, c.cx, above, "s", "#facc15", "#422006")
        else:
            self.hint.show(text, c.cx, c.cy + c.size // 2 + self.px(8), "n", "#facc15", "#422006")

    def on_captured(self, token, vk):
        if not isinstance(token, tuple):
            return
        if token[0] == "script":
            self._on_script_key_captured(token[1], vk)
            return
        c = self.circles.get(token[1])
        if c is None or self.editing is not c:
            return
        if vk == VK_ESCAPE:
            self.end_edit()
            return
        self._claim_key(vk, ("circle", c.id))     # 1 phím chỉ dùng cho 1 nút / 1 script
        c.key = vk
        self.end_edit()
        self.layout_changed()

    def layout_changed(self, save=True):
        if self.running:                  # nút thay đổi giữa chừng -> dừng script cho an toàn
            self.stop_script()
        mapping = {}
        for c in self.circles.values():
            if c.key is not None:
                mapping[c.key] = c.target()
        self.engine.set_mappings(mapping)
        self._sync_scripts()
        self._update_counts()
        self._refresh_script_tab()
        if save:
            self._schedule_save()

    # ------------------------------------------------------------------ vòng lặp
    def _poll(self):
        try:
            for _ in range(200):
                self._handle(self.ui_q.get_nowait())
        except queue.Empty:
            pass
        except Exception:
            log_exc("poll")
        self._poll_job = self.root.after(15, self._poll)

    def _handle(self, ev):
        kind = ev[0]
        if kind == "toggle":
            self.set_enabled(not self.enabled, from_hotkey=True)
        elif kind == "captured":
            self.on_captured(ev[1], ev[2])
        elif kind == "flash":
            c = self.circles.get(ev[1])
            if c is not None:
                c.flash()
        elif kind == "locked":              # bấm tay phím đang bị khoá (combo đang chạy)
            c = self.circles.get(ev[1])
            if c is not None:
                c.flash(THEME["warn"], 250)
        elif kind == "script_toggle":       # F9: chạy cùng lúc các combo có tick / dừng hết
            if self.running:
                self.stop_script()
            else:
                self.run_script()
        elif kind == "script_started":
            self._on_script_started(ev[1], ev[2])
        elif kind == "script_progress":
            self._on_script_progress(ev[1], ev[2], ev[3])
        elif kind == "script_done":
            self._on_script_done(ev[1], ev[2], ev[3])

    def _keep_on_top(self):
        try:
            if self.enabled and self.show_buttons and self.api.is_windows:
                for c in self.circles.values():
                    self._raise_circle(c)
        except Exception:
            log_exc("topmost")
        self._top_job = self.root.after(2000, self._keep_on_top)

    def _watch_foreground(self):
        try:
            self._check_foreground()
        except Exception:
            log_exc("foreground")
        self._fg_job = self.root.after(700, self._watch_foreground)

    def _check_foreground(self):
        """Mỗi lần chuyển sang cửa sổ khác (vd bấm vào game rồi phóng to):
        - đưa các nút tròn lên trên cùng lại ngay (không đợi 2 giây);
        - báo nếu cửa sổ đó chạy bằng quyền Admin mà KeyClick thì chưa: khi đó Windows
          chặn KeyClick nhận phím và click vào cửa sổ đó (nhấn A sẽ không click)."""
        hwnd, pid = self.api.foreground_window()
        if not pid or pid == self._last_fg_pid:
            return
        self._last_fg_pid = pid
        if pid == os.getpid():
            return
        if self.show_buttons:
            for c in self.circles.values():
                self._raise_circle(c)
        if self._is_admin or pid in self._elev_warned:
            return
        if not (self.enabled or any(c.key is not None for c in self.circles.values())
                or any(sc["key"] is not None for sc in self.scripts)):
            return                              # chưa dùng tới phím nào: khỏi báo
        if self.api.process_elevated(pid):
            self._elev_warned.add(pid)
            self._warn_elevated(pid)

    def _warn_elevated(self, pid):
        log("Cửa sổ đang chọn chạy bằng quyền Admin (pid %s)" % pid)
        self.toast.show("⚠ Cửa sổ này chạy bằng quyền Admin – hãy chạy KeyClick bằng quyền Admin",
                        self.root.winfo_screenwidth() // 2, self.px(28), "n", "#b91c1c",
                        "#ffffff", ms=5000)
        self.notify("Cửa sổ đó chạy quyền Admin nên Windows chặn KeyClick. Bấm “Chạy lại "
                    "bằng quyền Admin” ở dưới.", ms=20000)

    def _start_hook(self):
        err = None
        try:
            self.hook = self.api.start_keyboard_hook(self.engine.on_key)
            err = getattr(self.hook, "error", None)
        except Exception as e:
            err = str(e)
            log_exc("start hook")
        if err:
            self.hook_error = err
            log("Hook lỗi: %s" % err)
            self.cb_enabled.state(["disabled"])

    def _install_tk_key_fallback(self):
        """Chế độ thử: chỉ nhận phím khi cửa sổ KeyClick đang được chọn."""
        def handler(e, down):
            vk = _tk_keysym_to_vk(e.keysym)
            if vk and self.engine.on_key(vk, down):
                return "break"
        self.root.bind_all("<KeyPress>", lambda e: handler(e, True), add="+")
        self.root.bind_all("<KeyRelease>", lambda e: handler(e, False), add="+")

    # ------------------------------------------------------------------ lưu / mở
    def _read_config(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (IOError, OSError):
            return
        except Exception:
            log_exc("đọc config")
            return
        self.cfg = sanitize_cfg(data)
        if isinstance(data, dict):
            self._start_buttons = parse_buttons(data.get("buttons"))
            self._start_scripts = data.get("scripts")
            self._start_script_sel = data.get("script_sel", 0)
            self._legacy_loops, self._legacy_forever = _legacy_loop_settings(data)
            pos = data.get("window")
            if (isinstance(pos, list) and len(pos) == 2
                    and all(isinstance(p, int) and not isinstance(p, bool) for p in pos)):
                self._window_pos = pos
            if isinstance(data.get("profile_dir"), str):
                self.profile_dir = data["profile_dir"]

    def config_data(self):
        d = {"app": APP_NAME, "version": 1}
        d.update(self.cfg)
        d["return_cursor"] = bool(self.var_return.get())
        d["show_buttons"] = bool(self.show_buttons)
        d["profile_dir"] = self.profile_dir
        pos = self._window_position()
        if pos:
            d["window"] = pos
        d["buttons"] = [c.to_dict() for c in self.circles.values()]
        d["scripts"] = self._scripts_data()
        d["script_sel"] = self._sel_index()
        return d

    def _sel_index(self):
        sc = self._sel_script()
        return self.scripts.index(sc) if sc in self.scripts else 0

    def _schedule_save(self):
        if self._save_job:
            self.root.after_cancel(self._save_job)
        self._save_job = self.root.after(700, self.save_config)

    def save_config(self):
        self._save_job = None
        try:
            write_json(self.config_path, self.config_data())
        except Exception:
            log_exc("lưu config")

    def _profile_initialdir(self):
        if self.profile_dir and os.path.isdir(self.profile_dir):
            return self.profile_dir
        docs = os.path.join(os.path.expanduser("~"), "Documents")
        return docs if os.path.isdir(docs) else os.path.expanduser("~")

    def save_profile(self):
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Lưu bộ phím", defaultextension=".json",
            initialdir=self._profile_initialdir(), initialfile="bo-phim.json",
            filetypes=[("Bộ phím KeyClick", "*.json"), ("Tất cả", "*.*")])
        if not path:
            return
        data = {"app": APP_NAME, "type": "profile", "version": 2,
                "buttons": [c.to_dict() for c in self.circles.values()],
                "scripts": self._scripts_data(), "script_sel": self._sel_index()}
        try:
            write_json(path, data)
        except Exception as e:
            messagebox.showerror(APP_NAME, "Không lưu được:\n%s" % e, parent=self.root)
            return
        self.profile_dir = os.path.dirname(path)
        self._schedule_save()
        self.notify("Đã lưu bộ phím: " + os.path.basename(path))

    def open_profile(self):
        path = filedialog.askopenfilename(
            parent=self.root, title="Mở bộ phím", initialdir=self._profile_initialdir(),
            filetypes=[("Bộ phím KeyClick", "*.json"), ("Tất cả", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror(APP_NAME, "Không đọc được file:\n%s" % e, parent=self.root)
            return
        buttons = parse_buttons(data.get("buttons") if isinstance(data, dict) else None)
        if not buttons:
            messagebox.showwarning(APP_NAME, "File này không có nút nào.", parent=self.root)
            return
        loops, forever = _legacy_loop_settings(data)
        self.load_buttons(buttons, data.get("scripts"), data.get("script_sel", 0), loops, forever)
        self.profile_dir = os.path.dirname(path)
        self.notify("Đã mở: %s (%d nút, %d script)"
                    % (os.path.basename(path), len(buttons), len(self.scripts)))

    def load_buttons(self, buttons, scripts=None, sel=0, legacy_loops=1, legacy_forever=False):
        if self.enabled:
            self.set_enabled(False)
        if self.editing is not None:
            self.end_edit()
        self._end_script_capture()
        for c in list(self.circles.values()):
            c.destroy()
        self.circles.clear()
        created = self._create_buttons(buttons)
        self._install_scripts(scripts, created, buttons, sel, legacy_loops, legacy_forever)
        self.layout_changed()

    # ------------------------------------------------------------------ quyền Admin & thoát
    def relaunch_admin(self):
        self.save_config()
        self.api.release_single_instance()
        ok = False
        try:
            ok = self.api.relaunch_as_admin()
        except Exception:
            log_exc("relaunch admin")
        if ok:
            self.quit(save=False)
        else:
            self.api.acquire_single_instance()
            self.notify("Chưa chạy lại được bằng quyền Admin (có thể bạn đã bấm No).")

    def quit(self, save=True):
        if save:
            self.save_config()
        for job in (self._poll_job, self._top_job, self._fg_job, self._save_job,
                    self._notice_job, self._edit_job):
            if job:
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass
        if self.editing is not None:
            self.editing.stop_caret()
        try:
            if self.hook is not None:
                self.hook.stop()
        except Exception:
            pass
        try:
            self.engine.stop()
        except Exception:
            pass
        for c in list(self.circles.values()):   # huỷ lớp chữ trước lớp nền cho gọn
            try:
                c.destroy()
            except Exception:
                pass
        self.circles.clear()
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        self.root.mainloop()


def default_config_path():
    env = os.environ.get("KEYCLICK_CONFIG")
    if env:
        return env
    if IS_WINDOWS:
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, APP_NAME, "config.json")


def _config_wants_admin(cfg_path):
    """Ô "Luôn chạy bằng quyền Admin" có đang tick không (đọc thẳng file cấu hình)."""
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return False
    return isinstance(data, dict) and data.get("run_as_admin") is True


def main():
    global _LOG_PATH
    if sys.stdout is None:                     # pythonw / file .exe không có console
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    cfg_path = default_config_path()
    try:
        os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
        _LOG_PATH = os.path.join(os.path.dirname(cfg_path), "keyclick.log")
    except Exception:
        pass

    api = None
    try:
        api = WinAPI() if IS_WINDOWS else FakeAPI()
        if not api.acquire_single_instance():     # chỉ cho chạy 1 bản (tránh click 2 lần)
            if not api.bring_existing_to_front(WINDOW_TITLE):
                r = tk.Tk()
                r.withdraw()
                messagebox.showinfo(APP_NAME, "KeyClick đang chạy rồi.", parent=r)
                r.destroy()
            return
        declined = False
        if (IS_WINDOWS and RELAUNCH_ARG not in sys.argv[1:] and _config_wants_admin(cfg_path)
                and not api.is_admin()):          # đã tick "Luôn chạy bằng quyền Admin"
            api.release_single_instance()         # nhường "chỉ 1 bản" cho bản Admin
            if api.relaunch_as_admin():
                return
            declined = True                       # bấm No ở hộp UAC: chạy bình thường
            api.acquire_single_instance()
        app = App(api, cfg_path)
        if declined:
            app.notify("Chưa chạy được bằng quyền Admin (có thể bạn đã bấm No) – KeyClick "
                       "đang chạy bình thường.", ms=12000)
        app.run()
    except Exception:
        log_exc("main")
        _show_fatal(traceback.format_exc())
    finally:
        if api is not None:
            api.release_single_instance()


def _show_fatal(text):
    try:
        r = tk.Tk()
        r.withdraw()
        messagebox.showerror(APP_NAME, "Có lỗi xảy ra:\n\n" + text[-1500:], parent=r)
        r.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    main()
