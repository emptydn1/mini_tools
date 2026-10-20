#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KeyClick - Bấm phím thay cho click chuột (dùng được cho mọi tựa game)
=====================================================================

  1. Bấm "Thêm nút": một nút tròn hiện giữa màn hình, có dấu nháy nhấp nháy.
  2. Nhấn 1 phím (ví dụ A) để gán phím đó cho nút tròn.
  3. Kéo nút tròn tới chỗ cần click trong game.
  4. Nhấn F8 (hoặc bấm công tắc to ở đầu cửa sổ). Từ giờ nhấn A = click tại tâm nút tròn.

  Cửa sổ KeyClick (bản 1.9, nền tối):
  - Thẻ trạng thái ở trên cùng: công tắc bật/tắt + ĐANG BẬT / ĐANG TẮT / combo đang chạy.
  - Tab "Nút bấm": danh sách mọi nút trên màn hình (phím, kiểu click). Bút chì = gán phím,
    ⋯ = menu của nút; bấm vào 1 dòng thì nút đó nháy sáng trên màn hình.
  - Tab "Combo": danh sách combo (đang chạy có chấm xanh, nút ▶ / ■ chạy dừng từng combo),
    khung sửa combo đang chọn (các bước = các ĐIỂM của combo, nút "Thêm điểm"), nút
    "Chạy các combo F9" và "Dừng hết".
  - Tab "Cài đặt": độ đậm nền nút (có ô xem trước), "Hiện nút & điểm khi F8 bật", trả chuột
    về chỗ cũ, tốc độ turbo, phím tắt, quyền Admin.
  - Dòng thông báo cố định ở cuối cửa sổ. Cửa sổ có cỡ cố định: chữ đổi mà không nhảy.

  Nút tròn trên màn hình:
  - Bấm vào nút tròn: gán lại phím (Esc: huỷ).
  - Kéo giữa nút: di chuyển. Kéo MÉP nút hoặc lăn chuột: phóng to / thu nhỏ.
  - Ctrl + kéo nút, hoặc chuột phải > "Nhân bản": tạo bản sao rồi gõ phím mới cho nó.
  - Chuột phải vào nút: click trái/phải/giữa, chế độ click / giữ / turbo / vuốt / nhập chữ /
    bấm phím khác, đổi cỡ, xoá.
  - Nút tròn trắng dịu, mép mịn (Windows: mỗi điểm ảnh có độ trong suốt riêng).
  - Khi đang BẬT phím tắt, các nút bị khoá và chuột đi xuyên qua (không cản game).
  - Nút vuốt: nhấn phím = vuốt từ nút tới chấm vàng (kéo chấm vàng để chọn hướng);
    giữ phím = vuốt rồi giữ ở chấm vàng tới khi thả phím.
  - Nút nhập chữ (nút "Nhập chữ"): gõ sẵn 1 câu (vd "huy"); nhấn phím = dán câu đó vào chỗ
    đang gõ (hoặc gõ từng chữ), có thể click vào ô chat trước và nhấn Enter sau.
  - Nút phím (nút "Nút phím"): nhấn A = KeyClick bấm phím khác (vd Backspace); giữ A = giữ
    phím đó, thả A là thả.
  - Combo = chuỗi ĐIỂM riêng của combo đó (không cần phím, không nằm ở tab Nút bấm): bấm
    "Thêm điểm" rồi click lên màn hình vào các chỗ cần bấm, mỗi click là 1 bước; điểm là
    hình tròn xanh đánh số 1..n theo thứ tự bước (điểm của combo đang chọn luôn hiện). Bấm
    vào dòng bước / chuột phải vào điểm: click / giữ / turbo / vuốt / nhập chữ / bấm phím.
  - Lúc combo CHẠY (F9 / phím chạy / nút ▶), điểm của nó hiện trên màn hình (nhạt, chuột đi
    xuyên qua), điểm đang bấm sáng XANH LÁ; combo không phải combo đang chọn thì chạy xong
    điểm ẩn đi.
  - Công tắc "Hiện nút & điểm khi F8 bật" (tab Cài đặt, mặc định bật): tắt = F8 bật thì ẩn
    hết nút tròn và điểm combo (phím vẫn click, combo vẫn chạy); F8 tắt thì luôn hiện.
  - Combo chạy CÙNG LÚC được. F9 chạy cùng lúc mọi combo có bật "Chạy khi nhấn F9"; phím chạy
    riêng (không bắt buộc) chạy / dừng riêng từng combo; Esc dừng hết. Phím của nút tròn
    luôn để click (combo không lấy được).
  - Đang BẬT thì phím đã gán luôn click, dù cửa sổ nào đang ở trước (kể cả chính
    KeyClick); chỉ tạm dừng khi đang gõ trong ô Tên (ô số thì chỉ phím số dùng để gõ).
  - Game chạy quyền Admin: KeyClick báo ngay và có công tắc "Luôn chạy Admin".

Chạy trên Windows 10/11 với Python 3.8 trở lên (bản cài từ python.org đã có tkinter).
Không cần cài thêm thư viện nào. Muốn có file .exe thì chạy build_exe.bat.

Cấu trúc code:
  WinAPI        - gọi Windows API bằng ctypes: hook bàn phím toàn hệ thống, giả lập chuột,
                  giả lập phím (nút phím), dán chữ qua clipboard (nút nhập chữ)
  ClickEngine   - nhận phím từ hook, quyết định "nuốt" phím nào, giao việc click cho luồng riêng
  Circle        - một nút tròn trên màn hình (2 lớp cửa sổ: nền tròn mịn + chữ rõ, luôn trên cùng)
  ComboPoint    - một điểm của combo trên màn hình (như Circle nhưng xanh, có số, không có phím)
  PickLayer     - lớp mờ phủ màn hình để chọn điểm combo bằng cách click
  RButton, Switch, Card, ScrollArea, Field, StatusCard, MessageBar…
                - các phần giao diện vẽ tay (bo tròn, mép mịn) của cửa sổ chính
  App           - cửa sổ điều khiển (thẻ trạng thái, 3 tab, lưu/mở bộ phím...)
"""

import ctypes
import functools
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
from tkinter import filedialog, messagebox

APP_NAME = "KeyClick"
APP_VERSION = "1.9.8"
WINDOW_TITLE = "KeyClick – Bấm phím thay chuột"
IS_WINDOWS = sys.platform == "win32"

# ---------------------------------------------------------------------------
# Cấu hình mặc định - lưu tự động ở %APPDATA%\KeyClick\config.json
# ---------------------------------------------------------------------------
DEFAULT_CFG = {
    "return_cursor": True,      # Trả chuột về vị trí cũ sau khi click
    "show_play": True,          # F8 bật (đang chơi) vẫn hiện nút tròn + điểm combo; tắt = ẩn hết
    "toggle_key": 0x77,         # F8: bật/tắt nhanh (mã phím ảo Windows)
    "click_hold_ms": 40,        # thời gian giữ chuột trong 1 cú click
    "move_settle_ms": 10,       # chờ sau khi đưa chuột tới, để game kịp nhận "hover"
    "return_delay_ms": 10,      # chờ trước khi trả chuột về chỗ cũ
    "turbo_interval_ms": 100,   # chế độ turbo: 100 ms/lần = 10 click/giây
    "bg_alpha": 0.9,            # độ đậm NỀN của nút (0.05..1) - chữ trên nút luôn rõ
    "play_dim": 0.85,           # khi đang chơi, nút mờ thêm: nhân độ đậm với số này
    "button_size": 0,           # cỡ nút mới (pixel); 0 = tự chọn theo độ phân giải
    "script_key": 0x78,         # F9: chạy / dừng script đang chọn (Esc cũng dừng)
    "run_as_admin": False,      # Luôn chạy bằng quyền Admin (mở lên là tự xin quyền)
    "type_char_ms": 12,         # nút Nhập chữ, cách "gõ từng chữ": chờ giữa 2 chữ (ms)
}
RELAUNCH_ARG = "--relaunched"   # đánh dấu bản vừa được mở lại bằng quyền Admin
BUTTON_STYLE = 2                # kiểu nút: 2 = tròn mịn, trắng dịu (bản 1.8)
DEFAULT_DELAY_MS = 500          # (file cũ) thời gian chờ mặc định sau mỗi nút
DEFAULT_STEP_DELAY_MS = 200     # thời gian chờ mặc định khi thêm bước mới vào script
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
    "type_char_ms": (0, 500),
}
TIMING_KEYS = ("click_hold_ms", "move_settle_ms", "return_delay_ms", "turbo_interval_ms",
               "type_char_ms")

MOUSE_BUTTONS = ("left", "right", "middle")
MODES = ("click", "hold", "turbo", "swipe", "text", "key")
MOUSE_FREE_MODES = ("key",)     # kiểu nút không đụng tới chuột (nút Phím)
TEXT_METHODS = ("paste", "type")  # nút Nhập chữ: dán (Ctrl+V) / gõ từng chữ
MAX_TEXT_LEN = 1000
DEFAULT_SWIPE_MS = 200          # thời gian vuốt mặc định (từ nút tới điểm đích)
SWIPE_MS_RANGE = (30, 3000)

# ---------------------------------------------------------------------------
# Mã phím ảo (Virtual-Key) của Windows và tên hiển thị trên nút tròn
# ---------------------------------------------------------------------------
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
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

# Tên đầy đủ (dùng trong chữ mô tả, vd "Nhấn A = bấm Backspace"); phím khác dùng tên ngắn ở trên.
_VK_LONG_NAMES = {
    0x08: "Backspace", 0x0C: "Clear", 0x13: "Pause", 0x14: "Caps Lock", 0x1B: "Esc",
    0x21: "Page Up", 0x22: "Page Down", 0x25: "mũi tên ←", 0x26: "mũi tên ↑",
    0x27: "mũi tên →", 0x28: "mũi tên ↓", 0x2C: "Print Screen", 0x2D: "Insert", 0x2E: "Delete",
    0x5B: "Windows", 0x5C: "Windows phải", 0x5D: "Menu", 0x90: "Num Lock", 0x91: "Scroll Lock",
    0xA1: "Shift phải", 0xA3: "Ctrl phải", 0xA5: "Alt phải",
    0xAD: "Tắt tiếng", 0xAE: "Giảm âm lượng", 0xAF: "Tăng âm lượng", 0xB0: "Bài tiếp",
    0xB1: "Bài trước", 0xB2: "Dừng nhạc", 0xB3: "Phát / dừng",
}
for _i in range(10):
    _VK_LONG_NAMES[0x60 + _i] = "Num %d" % _i
# Phím "mở rộng" (có tiền tố E0): khi giả lập phải bật cờ KEYEVENTF_EXTENDEDKEY, nếu không
# game / ứng dụng có thể hiểu nhầm (vd mũi tên ← thành phím 4 bên bàn số).
EXTENDED_VKS = frozenset([0x03, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2C, 0x2D, 0x2E,
                          0x5B, 0x5C, 0x5D, 0x6F, 0x90, 0xA3, 0xA5] + list(range(0xA6, 0xB8)))


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


def vk_long_name(vk, api=None):
    """Tên đầy đủ của phím để ghi trong câu, ví dụ 0x08 -> 'Backspace'."""
    if vk is None:
        return ""
    return _VK_LONG_NAMES.get(vk) or vk_label(vk, api)


def valid_vk(v):
    """Mã phím ảo hợp lệ (1–254) hoặc None."""
    try:
        v = int(v)
    except (TypeError, ValueError):
        return None
    return v if 0 < v < 0xFF and v != VK_PACKET else None


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


class SIZE(ctypes.Structure):
    _fields_ = [("cx", _LONG), ("cy", _LONG)]


class RECT(ctypes.Structure):
    _fields_ = [("left", _LONG), ("top", _LONG), ("right", _LONG), ("bottom", _LONG)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [("BlendOp", ctypes.c_ubyte), ("BlendFlags", ctypes.c_ubyte),
                ("SourceConstantAlpha", ctypes.c_ubyte), ("AlphaFormat", ctypes.c_ubyte)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", _DWORD), ("biWidth", _LONG), ("biHeight", _LONG),
                ("biPlanes", _WORD), ("biBitCount", _WORD), ("biCompression", _DWORD),
                ("biSizeImage", _DWORD), ("biXPelsPerMeter", _LONG), ("biYPelsPerMeter", _LONG),
                ("biClrUsed", _DWORD), ("biClrImportant", _DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", _DWORD * 1)]


def _hex_rgb(color):
    """"#rrggbb" -> (r, g, b)"""
    c = color.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def render_disc(d, fill, fill_a, ring=None, ring_a=0.0, ring_w=0.0):
    """Ảnh d×d điểm ảnh của 1 hình tròn MÉP MỊN (khử răng cưa), dạng BGRA "premultiplied"
    (đúng kiểu UpdateLayeredWindow cần), các hàng xếp từ trên xuống.
      fill, ring: màu "#rrggbb" của ruột và viền; fill_a, ring_a: độ đậm 0..1;
      ring_w: độ dày viền (pixel, có thể lẻ). Mỗi điểm ở mép được phủ theo % diện tích nằm
      trong hình tròn -> mép tròn trơn, không răng cưa."""
    d = int(d)
    fr, fg, fb = _hex_rgb(fill)
    rr, rg, rb = _hex_rgb(ring or fill)
    fill_a = max(0.0, min(1.0, fill_a))
    ring_a = max(0.0, min(1.0, ring_a)) if ring_w > 0 else fill_a
    c = d / 2.0
    R = c - 0.5                       # bán kính ngoài (chừa nửa điểm ảnh cho mép mịn)
    inner = R - max(0.0, ring_w)      # bán kính phần ruột

    def pixel(dist):
        cov = R + 0.5 - dist          # phần điểm ảnh nằm trong hình tròn (0..1)
        if cov <= 0.0:
            return b"\0\0\0\0"
        if cov > 1.0:
            cov = 1.0
        t = dist - inner + 0.5        # 0 = ruột, 1 = viền (chuyển mượt ở giữa)
        t = 0.0 if t <= 0.0 else (1.0 if t >= 1.0 else t)
        a = (fill_a + (ring_a - fill_a) * t) * cov
        r = fr + (rr - fr) * t
        g = fg + (rg - fg) * t
        b = fb + (rb - fb) * t
        return bytes((int(b * a + 0.5), int(g * a + 0.5), int(r * a + 0.5), int(a * 255 + 0.5)))

    solid = pixel(0.0)
    empty = b"\0\0\0\0"
    out = bytearray()
    lim_in = inner - 0.5              # tâm điểm ảnh trong vòng này = ruột đặc (tính sẵn 1 lần)
    lim_out = R + 0.5                 # ngoài vòng này = trong suốt hoàn toàn
    for y in range(d):
        dy = y + 0.5 - c
        if abs(dy) >= lim_out:
            out += empty * d
            continue
        ho = math.sqrt(lim_out * lim_out - dy * dy)
        xo0 = max(0, int(math.floor(c - ho - 0.5)))
        xo1 = min(d - 1, int(math.ceil(c + ho - 0.5)))
        if lim_in > abs(dy):
            hi = math.sqrt(lim_in * lim_in - dy * dy)
            xi0 = int(math.ceil(c - hi - 0.5))
            xi1 = int(math.floor(c + hi - 0.5))
        else:
            xi0, xi1 = 1, 0                   # hàng này không có ruột đặc
        out += empty * xo0
        x = xo0
        while x <= xo1:
            if xi0 <= x <= xi1:
                out += solid * (xi1 - x + 1)
                x = xi1 + 1
                continue
            out += pixel(math.hypot(x + 0.5 - c, dy))
            x += 1
        out += empty * (d - 1 - xo1)
    return bytes(out)


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
    SWP_NOOWNERZORDER, SWP_NOSENDCHANGING = 0x0200, 0x0400
    GW_HWNDPREV = 3                  # cửa sổ nằm ngay TRÊN 1 cửa sổ (thứ tự trên / dưới)
    SM_SWAPBUTTON = 23
    EXTRA_INFO = 0x4B43              # "KC": đánh dấu sự kiện chuột / phím do KeyClick tạo
    INPUT_KEYBOARD = 1
    KEYEVENTF_EXTENDEDKEY, KEYEVENTF_KEYUP, KEYEVENTF_UNICODE = 0x0001, 0x0002, 0x0004
    CF_UNICODETEXT = 13
    MUTEX_NAME = "Local\\KeyClick.SingleInstance"

    WS_EX_LAYERED = 0x00080000

    def __init__(self, user32=None, kernel32=None, shell32=None, advapi32=None, gdi32=None,
                 set_dpi=True):
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
        if gdi32 is None:
            gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
        self.u, self.k, self.s, self.a, self.g = user32, kernel32, shell32, advapi32, gdi32
        self._mutex = None
        self._clip = None                # các hàm clipboard (khai báo khi cần lần đầu)
        self._clip_lock = threading.Lock()
        self._paste_lock = threading.Lock()
        self._clip_gen = 0
        self._restore_old = None         # chữ có sẵn trong clipboard trước khi dán, chờ trả lại
        self.smooth_ok = True            # vẽ nút tròn mịn (mỗi điểm ảnh 1 độ trong suốt)
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
        sig(u.GetWindow, w.HWND, w.HWND, w.UINT)
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
        sig(u.VkKeyScanW, ctypes.c_short, w.WCHAR)
        sig(u.SystemParametersInfoW, w.BOOL, w.UINT, w.UINT, ctypes.c_void_p, w.UINT)
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
        g = self.g
        sig(u.GetDC, w.HDC, w.HWND)
        sig(u.ReleaseDC, ctypes.c_int, w.HWND, w.HDC)
        sig(u.UpdateLayeredWindow, w.BOOL, w.HWND, w.HDC, ctypes.POINTER(POINT),
            ctypes.POINTER(SIZE), w.HDC, ctypes.POINTER(POINT), w.COLORREF,
            ctypes.POINTER(BLENDFUNCTION), w.DWORD)
        sig(g.CreateCompatibleDC, w.HDC, w.HDC)
        sig(g.CreateDIBSection, w.HBITMAP, w.HDC, ctypes.POINTER(BITMAPINFO), w.UINT,
            ctypes.POINTER(ctypes.c_void_p), w.HANDLE, w.DWORD)
        sig(g.SelectObject, w.HGDIOBJ, w.HDC, w.HGDIOBJ)
        sig(g.DeleteObject, w.BOOL, w.HGDIOBJ)
        sig(g.DeleteDC, w.BOOL, w.HDC)
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

    # -- bàn phím ảo: nút "Nhập chữ" (dán / gõ chữ) --
    def _key_input(self, vk=0, scan=0, flags=0):
        inp = INPUT()
        inp.type = self.INPUT_KEYBOARD
        inp.ki.wVk = vk
        inp.ki.wScan = scan
        inp.ki.dwFlags = flags
        inp.ki.dwExtraInfo = self.EXTRA_INFO     # hook của KeyClick nhận ra và bỏ qua
        return inp

    def _vk_events(self, vk, down=True, up=True):
        scan = self.u.MapVirtualKeyW(vk, 0) & 0xFF
        ext = self.KEYEVENTF_EXTENDEDKEY if vk in EXTENDED_VKS else 0
        out = []
        if down:
            out.append(self._key_input(vk, scan, ext))
        if up:
            out.append(self._key_input(vk, scan, ext | self.KEYEVENTF_KEYUP))
        return out

    def tap_key(self, vk):
        """Nhấn và thả 1 phím (vd Enter)."""
        self._send(self._vk_events(vk))

    def key_event(self, vk, down):
        """Nhấn (down=True) hoặc thả 1 phím – nút Phím: giữ A = giữ phím được đổi sang."""
        self._send(self._vk_events(vk, down=down, up=not down))

    def _char_events(self, ch):
        """Sự kiện phím để gõ 1 chữ: chữ/số tiếng Anh gõ như phím thật (game nào cũng nhận),
        chữ khác (có dấu tiếng Việt, emoji…) gõ bằng mã Unicode."""
        if ch in "\r\n":
            return self._vk_events(VK_RETURN)
        if ch == "\t":
            return self._vk_events(0x09)
        if " " <= ch <= "~":
            r = self.u.VkKeyScanW(ch)
            if r != -1 and (r & 0xFF) != 0xFF and not (r >> 8) & 0x06:   # không cần Ctrl / Alt
                vk = r & 0xFF
                if (r >> 8) & 0x01:                                       # cần Shift
                    return (self._vk_events(VK_SHIFT, up=False) + self._vk_events(vk)
                            + self._vk_events(VK_SHIFT, down=False))
                return self._vk_events(vk)
        out = []
        data = ch.encode("utf-16-le")
        for i in range(0, len(data), 2):
            unit = data[i] | (data[i + 1] << 8)
            out.append(self._key_input(0, unit, self.KEYEVENTF_UNICODE))
            out.append(self._key_input(0, unit, self.KEYEVENTF_UNICODE | self.KEYEVENTF_KEYUP))
        return out

    def type_chars(self, text, char_ms=12):
        for ch in text:
            self._send(self._char_events(ch))
            if char_ms > 0:
                time.sleep(char_ms / 1000.0)

    def type_text(self, text, method="paste", char_ms=12):
        """Nhập chữ vào ô đang được chọn: dán (Ctrl+V) hoặc gõ từng chữ."""
        if not text:
            return True
        if method == "paste":
            try:
                if self.paste_text(text):
                    return True
            except Exception:
                log_exc("paste")
            log("Không dán được (clipboard bận) – gõ từng chữ")
        self.type_chars(text, char_ms)
        return True

    def _clip_fns(self):
        if self._clip is None:
            u, k, w = self.u, self.k, self.wt

            def sig(fn, res, *args):
                fn.restype = res
                fn.argtypes = args
                return fn

            self._clip = {
                "open": sig(u.OpenClipboard, w.BOOL, w.HWND),
                "close": sig(u.CloseClipboard, w.BOOL),
                "empty": sig(u.EmptyClipboard, w.BOOL),
                "get": sig(u.GetClipboardData, w.HANDLE, w.UINT),
                "set": sig(u.SetClipboardData, w.HANDLE, w.UINT, w.HANDLE),
                "avail": sig(u.IsClipboardFormatAvailable, w.BOOL, w.UINT),
                "create": sig(u.CreateWindowExW, w.HWND, w.DWORD, w.LPCWSTR, w.LPCWSTR, w.DWORD,
                              ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, w.HWND,
                              w.HMENU, w.HINSTANCE, w.LPVOID),
                "destroy": sig(u.DestroyWindow, w.BOOL, w.HWND),
                "alloc": sig(k.GlobalAlloc, w.HGLOBAL, w.UINT, ctypes.c_size_t),
                "lock": sig(k.GlobalLock, w.LPVOID, w.HGLOBAL),
                "unlock": sig(k.GlobalUnlock, w.BOOL, w.HGLOBAL),
                "free": sig(k.GlobalFree, w.HGLOBAL, w.HGLOBAL),
            }
        return self._clip

    def _with_clipboard(self, fn):
        """Mở clipboard rồi chạy fn(c). Dùng 1 cửa sổ tạm làm "chủ" clipboard (nếu không có
        cửa sổ chủ thì SetClipboardData sẽ lỗi), xong thì huỷ cửa sổ đó. None = không mở được."""
        c = self._clip_fns()
        with self._clip_lock:
            hwnd = c["create"](0, "STATIC", None, 0, 0, 0, 0, 0, None, None, None, None)
            try:
                for _ in range(50):              # app khác đang giữ clipboard: thử lại ~0,5 s
                    if c["open"](hwnd):
                        break
                    time.sleep(0.01)
                else:
                    return None
                try:
                    return fn(c)
                finally:
                    c["close"]()
            finally:
                if hwnd:
                    c["destroy"](hwnd)

    def _clip_get(self, c):
        if not c["avail"](self.CF_UNICODETEXT):
            return None
        h = c["get"](self.CF_UNICODETEXT)
        p = c["lock"](h) if h else None
        if not p:
            return None
        try:
            return ctypes.wstring_at(p)
        finally:
            c["unlock"](h)

    def _clip_set(self, c, text):
        c["empty"]()
        data = (text + "\0").encode("utf-16-le")
        h = c["alloc"](0x0002, len(data))        # GMEM_MOVEABLE
        p = c["lock"](h) if h else None
        if not p:
            if h:
                c["free"](h)
            return False
        ctypes.memmove(p, data, len(data))
        c["unlock"](h)
        if not c["set"](self.CF_UNICODETEXT, h):
            c["free"](h)
            return False
        return True                              # từ giờ Windows giữ vùng nhớ này

    def paste_text(self, text, wait_ms=60, restore_ms=1500):
        """Dán chữ: đặt chữ vào clipboard rồi nhấn Ctrl+V. Chữ có sẵn trong clipboard được
        trả lại sau restore_ms (nếu trong lúc đó người dùng không copy gì khác)."""
        with self._paste_lock:
            self._clip_gen += 1
            gen = self._clip_gen
            got = self._with_clipboard(lambda c: (self._clip_get(c), self._clip_set(c, text)))
            if not got or not got[1]:
                return False
            if self._restore_old is None:        # (dán liên tiếp: giữ chữ GỐC của lần đầu)
                self._restore_old = got[0]
            time.sleep(wait_ms / 1000.0)         # để app (vd giả lập) kịp thấy clipboard mới
            self._send(self._vk_events(VK_CONTROL, up=False) + self._vk_events(0x56)
                       + self._vk_events(VK_CONTROL, down=False))
            if self._restore_old is not None:
                t = threading.Timer(restore_ms / 1000.0, self._restore_clip, (gen, text))
                t.daemon = True
                t.start()
            return True

    def _restore_clip(self, gen, ours):
        with self._paste_lock:
            if gen != self._clip_gen or self._restore_old is None:
                return                           # đã dán lần khác sau đó: lần đó sẽ trả lại
            old, self._restore_old = self._restore_old, None
            try:
                self._with_clipboard(lambda c: self._clip_get(c) == ours and self._clip_set(c, old))
            except Exception:
                log_exc("restore clipboard")

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

    # -- nút tròn mịn: mỗi điểm ảnh có độ trong suốt riêng (UpdateLayeredWindow) --
    def make_layered(self, hwnd):
        """Chuẩn bị cửa sổ để vẽ bằng layered_paint(). False = không dùng được."""
        if not hwnd or not self.smooth_ok:
            return False
        try:
            old = self._get_wl(hwnd, self.GWL_EXSTYLE)
            if old & self.WS_EX_LAYERED:                  # bỏ kiểu "trong suốt 1 màu" cũ
                self._set_wl(hwnd, self.GWL_EXSTYLE, old & ~self.WS_EX_LAYERED)
            self._set_wl(hwnd, self.GWL_EXSTYLE, old | self.WS_EX_LAYERED)
            return True
        except Exception:
            log_exc("make_layered")
            return False

    def layered_paint(self, hwnd, x, y, w, h, bgra, alpha=255):
        """Đặt ảnh BGRA (premultiplied, w×h) làm hình của cửa sổ hwnd tại (x, y) trên màn
        hình; alpha = độ đậm chung 0..255. True = thành công."""
        u, g = self.u, self.g
        screen = u.GetDC(None)
        if not screen:
            return False
        mem = bmp = old = None
        try:
            mem = g.CreateCompatibleDC(screen)
            if not mem:
                return False
            bmi = BITMAPINFO()
            bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.bmiHeader.biWidth = int(w)
            bmi.bmiHeader.biHeight = -int(h)          # số âm = các hàng xếp từ trên xuống
            bmi.bmiHeader.biPlanes = 1
            bmi.bmiHeader.biBitCount = 32
            bmi.bmiHeader.biCompression = 0           # BI_RGB
            bits = ctypes.c_void_p()
            bmp = g.CreateDIBSection(mem, ctypes.byref(bmi), 0, ctypes.byref(bits), None, 0)
            if not bmp or not bits.value:
                return False
            ctypes.memmove(bits.value, bgra, int(w) * int(h) * 4)
            old = g.SelectObject(mem, bmp)
            blend = BLENDFUNCTION(0, 0, max(0, min(255, int(alpha))), 1)  # AC_SRC_OVER, AC_SRC_ALPHA
            ok = u.UpdateLayeredWindow(hwnd, screen, ctypes.byref(POINT(int(x), int(y))),
                                       ctypes.byref(SIZE(int(w), int(h))), mem,
                                       ctypes.byref(POINT(0, 0)), 0, ctypes.byref(blend),
                                       2)                       # ULW_ALPHA
            return bool(ok)
        finally:
            if old:
                g.SelectObject(mem, old)
            if bmp:
                g.DeleteObject(bmp)
            if mem:
                g.DeleteDC(mem)
            u.ReleaseDC(None, screen)

    def set_topmost(self, hwnd):
        if hwnd:
            self.u.SetWindowPos(hwnd, ctypes.c_void_p(-1), 0, 0, 0, 0,  # HWND_TOPMOST
                                self.SWP_NOMOVE | self.SWP_NOSIZE | self.SWP_NOACTIVATE)

    def place_above(self, hwnd, below):
        """Đặt cửa sổ hwnd nằm ngay TRÊN cửa sổ `below` (below giữ nguyên chỗ). Dùng cho nút tròn
        / điểm combo: lớp chữ luôn phải nằm trên lớp nền, nền mà đè lên thì số / tên phím bị mờ.
        Đã đúng thứ tự thì không làm gì."""
        if not (hwnd and below):
            return
        prev = self.u.GetWindow(below, self.GW_HWNDPREV)      # cửa sổ đang nằm ngay trên `below`
        if prev == hwnd:
            return
        self.u.SetWindowPos(hwnd, prev if prev else ctypes.c_void_p(-1), 0, 0, 0, 0,
                            self.SWP_NOMOVE | self.SWP_NOSIZE | self.SWP_NOACTIVATE
                            | self.SWP_NOOWNERZORDER | self.SWP_NOSENDCHANGING)

    def set_owner(self, hwnd, owner):
        """Cho hwnd "thuộc về" owner: Windows luôn giữ hwnd nằm ngay trên owner."""
        if hwnd and owner:
            self._set_wl(hwnd, self.GWLP_HWNDPARENT, owner)

    def force_foreground(self, hwnd):
        if hwnd:
            self.u.SetForegroundWindow(hwnd)

    def dark_title_bar(self, hwnd, caption=None):
        """Thanh tiêu đề màu tối (Windows 10 1809+ / 11); Windows 11: tô đúng màu `caption`."""
        if not hwnd:
            return False
        try:
            dwm = ctypes.WinDLL("dwmapi")
            fn = dwm.DwmSetWindowAttribute
        except Exception:
            return False
        fn.restype = ctypes.c_long
        fn.argtypes = (self.wt.HWND, self.wt.DWORD, ctypes.c_void_p, self.wt.DWORD)
        on = ctypes.c_int(1)
        ok = (fn(hwnd, 20, ctypes.byref(on), 4) == 0          # DWMWA_USE_IMMERSIVE_DARK_MODE
              or fn(hwnd, 19, ctypes.byref(on), 4) == 0)      # (Windows 10 bản cũ)
        if caption:
            r, g, b = _hex_rgb(caption)
            col = ctypes.c_uint32(r | (g << 8) | (b << 16))
            fn(hwnd, 35, ctypes.byref(col), 4)                # DWMWA_CAPTION_COLOR (Windows 11)
        self.u.SetWindowPos(hwnd, None, 0, 0, 0, 0,
                            self.SWP_NOMOVE | self.SWP_NOSIZE | self.SWP_NOZORDER
                            | self.SWP_NOACTIVATE | self.SWP_FRAMECHANGED)
        return ok

    def work_area(self):
        """(x, y, rộng, cao) của màn hình chính trừ thanh taskbar."""
        r = RECT()
        if self.u.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0):   # SPI_GETWORKAREA
            if r.right > r.left and r.bottom > r.top:
                return r.left, r.top, r.right - r.left, r.bottom - r.top
        return None

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
        own = api.EXTRA_INFO

        def proc(n_code, w_param, l_param):
            if n_code == 0:  # HC_ACTION
                try:
                    kb = from_address(l_param)
                    if kb.dwExtraInfo == own:
                        pass   # phím do chính KeyClick gõ (nút Nhập chữ: Ctrl+V, chữ…): cho qua
                    elif w_param in downs:
                        if handler(kb.vkCode, True, kb.flags):
                            return 1   # "nuốt" phím: game không nhận được
                    elif w_param in ups:
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
        self.stacked = []                # các lần đặt lớp chữ ngay trên lớp nền (place_above)
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

    def type_text(self, text, method="paste", char_ms=12):
        with self._lock:
            self.events.append(("text", text, method))
        return True

    def tap_key(self, vk):
        with self._lock:
            self.events.append(("key", vk))

    def key_event(self, vk, down):
        with self._lock:
            self.events.append(("key_down" if down else "key_up", vk))

    def toplevel_hwnd(self, tkwin):
        return id(tkwin)

    def set_window_style(self, hwnd, click_through):
        self.styles[hwnd] = click_through

    def set_topmost(self, hwnd):
        pass

    def place_above(self, hwnd, below):
        self.stacked.append((hwnd, below))

    def set_owner(self, hwnd, owner):
        self.owners[hwnd] = owner

    def force_foreground(self, hwnd):
        pass

    def dark_title_bar(self, hwnd, caption=None):
        return False

    def work_area(self):
        return None

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
# text, enter, click, method: chỉ dùng cho nút Nhập chữ (chữ cần nhập, Enter sau đó,
#   click vào chỗ đặt nút trước, cách nhập "paste" / "type")
# out: chỉ dùng cho nút Phím (mã phím sẽ được bấm thay, vd Backspace)
Target = namedtuple("Target", "cid x y button mode x2 y2 dur text enter click method out",
                    defaults=(None, None, 0, "", False, False, "paste", None))


def _uses_mouse(t):
    """Bước / nút này có dùng chuột không (nút Phím và nút Nhập chữ không click thì không)."""
    return t.mode not in MOUSE_FREE_MODES and not (t.mode == "text" and not t.click)


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
        # Nút Phím (nhấn A = bấm Backspace): luồng hook ghi phím nào đang được đổi sang phím
        # nào; 1 luồng riêng gửi phím ra để không phải chờ các cú click / vuốt đang làm dở.
        self._remap = {}                # vk đang giữ -> vk KeyClick đang giữ thay (luồng hook)
        self._kq = queue.Queue()
        self._out_down = {}             # vk KeyClick đang giữ xuống -> số nút đang giữ nó
        self._worker = threading.Thread(target=self._run, name="KeyClick-worker")
        self._worker.daemon = True
        self._worker.start()
        self._keyer = threading.Thread(target=self._key_loop, name="KeyClick-keys")
        self._keyer.daemon = True
        self._keyer.start()

    # ---- gọi từ giao diện ----
    def set_mappings(self, mapping):
        self._map = dict(mapping)       # thay nguyên dict -> an toàn giữa các luồng

    def set_script_keys(self, mapping):
        """mapping: {phím: (id script, [(Target, chờ ms), ...], số vòng hoặc None)}"""
        self._script_keys = dict(mapping)

    def set_timing(self, **kw):
        t = dict(self.timing)
        t.update(kw)
        self.timing = t

    def release_all(self):
        self._q.put(("release",))
        self._kq.put(("release",))      # nhả các phím nút Phím đang giữ (không để kẹt phím)

    def start_script(self, sid, steps, loops):
        """Chạy thêm 1 script (các script khác đang chạy vẫn chạy tiếp).
        steps: [(Target, thời gian chờ ms), ...]; loops: số vòng, None = lặp vĩnh viễn."""
        self.script_running = True       # để Esc dừng được ngay
        self._q.put(("script_start", sid, list(steps), loops))

    def stop_script(self, sid=None):
        """Dừng 1 script (sid) hoặc tất cả (None)."""
        self._q.put(("script_stop", sid))

    def stop(self):
        self._kq.put(("release",))
        self._kq.put(None)
        self._q.put(("stop",))
        self._worker.join(1.0)
        self._keyer.join(1.0)

    # ---- gọi từ luồng hook bàn phím: trả về True = nuốt phím ----
    def on_key(self, vk, down, flags=0):
        if vk <= 0 or vk >= 0xFF or vk == VK_PACKET:
            return False
        if not down:
            self._down.discard(vk)
            kind = self._held.pop(vk, None)
            if kind == "action":
                self._q.put(("up", vk))
            elif kind == "remap":        # thả A -> thả luôn phím được đổi sang
                out = self._remap.pop(vk, None)
                if out is not None:
                    self._kq.put(("up", out))
            return kind is not None      # chỉ nuốt phím-thả nếu đã nuốt phím-nhấn

        kind = self._held.get(vk)
        if kind is not None:             # phím tự lặp khi giữ, trước đó đã nuốt
            if kind == "remap" and self.enabled and vk in self._remap:
                self._kq.put(("repeat", self._remap[vk]))   # giữ A = giữ phím kia: tự lặp y hệt
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
                if t.mode == "key":                             # nút Phím: bấm phím khác
                    if t.out is None:
                        return False
                    self._held[vk] = "remap"
                    self._remap[vk] = t.out
                    self._kq.put(("down", t.out))
                    self.ui_queue.put(("flash", t.cid))
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

    # ---- luồng gửi phím của nút Phím (nhấn A = bấm Backspace) ----
    def _key_loop(self):
        while True:
            ev = self._kq.get()
            try:
                if ev is None:
                    return
                self._key_event(*ev)
            except Exception:
                log_exc("keys")
            finally:
                self._kq.task_done()

    def _key_event(self, kind, vk=None):
        """down: nhấn (2 nút cùng đổi sang 1 phím thì phím đó chỉ thả khi thả cả 2);
        repeat: phím tự lặp khi đang giữ; up: thả; release: thả hết (tắt phím tắt / thoát)."""
        held = self._out_down
        if kind == "down":
            held[vk] = held.get(vk, 0) + 1
            self.api.key_event(vk, True)
        elif kind == "repeat":
            if held.get(vk):
                self.api.key_event(vk, True)
        elif kind == "up":
            n = held.get(vk, 0) - 1
            if n > 0:
                held[vk] = n
            elif vk in held:
                del held[vk]
                self.api.key_event(vk, False)
        elif kind == "release":
            for k in list(held):
                del held[k]
                self.api.key_event(k, False)

    def _tap_out(self, vk):
        """Bước combo của nút Phím: nhấn phím đó (giữ một chút như phím thật) rồi thả."""
        self.api.key_event(vk, True)
        self._sleep_ms(self.timing["click_hold_ms"])
        self.api.key_event(vk, False)

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
        if not _uses_mouse(t):           # nhập chữ không click: không đụng tới chuột
            self._type_text(t)
            return
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
        elif t.mode == "text":           # nhập chữ: (click vào ô) -> dán / gõ chữ -> (Enter)
            self._type_text(t)
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

    def _type_text(self, t):
        """Nút "Nhập chữ": click vào chỗ đặt nút (vd ô chat) nếu có chọn, dán hoặc gõ chữ,
        rồi nhấn Enter nếu có chọn."""
        if t.click:
            self._click(t)
            self._sleep_ms(40)                   # chờ ô nhập nhận con trỏ
        if t.text:
            self.api.type_text(t.text, t.method, self.timing["type_char_ms"])
        if t.enter:
            self._sleep_ms(30)
            self.api.tap_key(VK_RETURN)

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
    #  bắt đầu bước, nên nhịp chạy đều (vd chờ 500 ms = mỗi 0,5 giây 1 bước).
    #  Nhiều script chạy CÙNG LÚC được (vd 2–4 combo): mỗi script có lịch riêng, các cú
    #  click được xếp lần lượt vì chỉ có 1 con chuột. Bước cuối của lần chạy cuối không chờ.
    def _on_script_key(self, sid, steps, loops):
        """Nhấn phím chạy của 1 script (khi đang BẬT phím tắt). Script khác vẫn chạy tiếp."""
        sc = self._scripts.get(sid)
        if sc is not None:
            if sc["loops"] != 1:               # script có lặp: nhấn lại = dừng
                self._script_finish("stopped", sid)
            else:                               # combo 1 lần: cứ để chạy hết
                self._update_running()
            return
        self._script_begin(sid, steps, loops)

    def _script_begin(self, sid, steps, loops):
        if sid in self._scripts:
            self._script_finish("stopped", sid)
        if not steps:
            self._update_running()
            self.ui_queue.put(("script_done", sid, "empty", 0))
            return
        self._scripts[sid] = {"sid": sid, "steps": steps, "loops": loops, "i": 0, "done": 0,
                              "phase": "start", "next": time.perf_counter(), "end": 0.0}
        self._update_running()
        self.ui_queue.put(("script_started", sid, loops))
        self.ui_queue.put(("script_progress", sid, 1, loops))

    def _update_running(self):
        """Báo cho luồng hook: còn script nào chạy không (để Esc dừng được)."""
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
        if phase == "start" and not _uses_mouse(t):     # bấm phím / nhập chữ: không dùng chuột
            self.ui_queue.put(("flash", t.cid))
            if t.mode == "key":
                if t.out is not None:
                    self._tap_out(t.out)
            else:
                self._type_text(t)
            sc["phase"] = "wait"
            sc["next"] = now if self._script_is_last_step(sc) else now + wait
        elif phase == "start":                   # bắt đầu 1 bước
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
            elif t.mode == "text":               # nhập chữ rồi chờ
                self._type_text(t)
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
    "key": "#ff00ff",         # màu "trong suốt" của lớp nền khi phải dùng cách vẽ cũ
    "key_text": "#eef1f4",    # màu "trong suốt" của lớp chữ: gần màu nền nút -> mép chữ mịn
    "fill": "#f3f5f8",        # nền nút: trắng dịu, không chói
    "fill_hover": "#e2e8f0",  # nền khi rê chuột vào (lúc đang chỉnh)
    "fill_edit": "#fde68a",   # nền vàng nhạt = đang chờ gán phím
    "ring": "#64748b",        # viền mảnh quanh nút (thấy rõ cả trên nền sáng)
    "text_left": "#1f2937",   # chữ đen xám = click chuột trái
    "text_right": "#c2410c",  # chữ cam đậm = click chuột phải
    "text_middle": "#6d28d9", # chữ tím = click chuột giữa
    "muted": "#94a3b8",       # "?" = nút chưa gán phím
    "outline": "#ffffff",     # viền sáng mảnh quanh chữ (đọc rõ cả khi nền game tối)
    "caret_text": "#1f2937",  # dấu nháy trong nút khi chờ gán phím
    "caret": "#facc15",       # vàng: mũi tên + chấm B của nút vuốt
    "marker": "#0f172a",      # nền chấm B của nút vuốt
    "arrow_outline": "#000000",
    "left": "#38bdf8",        # màu nháy sáng khi bấm phím
    "right": "#fb923c",
    "middle": "#a78bfa",
    "warn": "#f87171",
}
MODE_TAGS = {"hold": "GIỮ", "turbo": "TURBO", "swipe": "VUỐT", "text": "CHỮ", "key": "PHÍM"}
# Điểm của combo: tròn XANH, chữ số trắng (khác nút tròn trắng có tên phím ở tab Nút bấm).
POINT_FILL, POINT_FILL_HI, POINT_RING = "#2563eb", "#3b82f6", "#dbeafe"
POINT_TEXT, POINT_OUTLINE = "#ffffff", "#1e3a8a"
POINT_KEY_TEXT = "#2866ec"      # màu "trong suốt" của lớp chữ: gần màu nền điểm -> mép chữ mịn
POINT_RUN = "#16a34a"           # combo đang chạy: điểm của bước đang làm sáng xanh lá
POINT_RUN_ALPHA = 0.6           # combo đang chạy: các điểm khác nhạt đi cho đỡ che game
PICK_SHADE = "#0b1220"          # lớp mờ khi đang chọn điểm trên màn hình


def _label_color(c):
    """Màu chữ tên phím của nút: theo nút chuột (trái đen, phải cam, giữa tím); nút không
    click chuột (nút Phím, Nhập chữ không click) thì luôn đen."""
    if c.mode == "key" or (c.mode == "text" and not c.text_click):
        return THEME["text_left"]
    return THEME.get("text_" + c.button, THEME["text_left"])
RESIZE_CURSORS = ("size_nw_se", "size_ne_sw") if IS_WINDOWS else ("sizing", "sizing")


def _outlined_text(canvas, x, y, text, color, font, width=1, outline=None):
    """Vẽ chữ có viền mỏng (đọc rõ cả trên nền sáng lẫn tối)."""
    outline = outline or THEME["outline"]
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx or dy:
                canvas.create_text(x + dx, y + dy, text=text, fill=outline, font=font)
    canvas.create_text(x, y, text=text, fill=color, font=font)


@functools.lru_cache(maxsize=96)
def _disc_image(d, fill, fill_a, ring, ring_a, ring_w):
    return render_disc(d, fill, fill_a, ring, ring_a, ring_w)

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


ACTION_KEYS = ("x", "y", "mouse", "mode", "x2", "y2", "swipe_ms", "text", "enter", "click_first",
               "method", "out")


def _parse_action(it):
    """Phần "làm gì, ở đâu" của 1 nút tròn / 1 điểm combo trong file JSON: vị trí, nút chuột,
    kiểu (click / giữ / turbo / vuốt / nhập chữ / bấm phím) và thông số của kiểu đó.
    None nếu không có vị trí hợp lệ."""
    try:
        x, y = int(it.get("x")), int(it.get("y"))
    except (TypeError, ValueError):
        return None
    mode = it.get("mode") if it.get("mode") in MODES else "click"
    x2, y2 = it.get("x2"), it.get("y2")
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (x2, y2)):
        x2 = y2 = None
    try:
        swipe_ms = int(it.get("swipe_ms", DEFAULT_SWIPE_MS))
    except (TypeError, ValueError):
        swipe_ms = DEFAULT_SWIPE_MS
    text = it.get("text") if isinstance(it.get("text"), str) else ""
    key_out = None if isinstance(it.get("out"), bool) else valid_vk(it.get("out"))
    if mode == "key" and key_out is None:           # nút Phím mà không có phím cần bấm
        mode = "click"
    return {"x": x, "y": y, "mouse": it.get("mouse") if it.get("mouse") in MOUSE_BUTTONS else "left",
            "mode": mode, "x2": x2, "y2": y2,
            "swipe_ms": max(SWIPE_MS_RANGE[0], min(SWIPE_MS_RANGE[1], swipe_ms)),
            "text": text[:MAX_TEXT_LEN], "enter": it.get("enter") is True,
            "click_first": it.get("click_first") is True,       # mặc định: không click
            "method": it.get("method") if it.get("method") in TEXT_METHODS else "paste",
            "out": key_out}


def action_to_dict(a):
    """Ghi phần "làm gì, ở đâu" ra file (bỏ các thông số không dùng tới cho gọn)."""
    d = {"x": a["x"], "y": a["y"], "mouse": a["mouse"], "mode": a["mode"],
         "x2": a["x2"], "y2": a["y2"], "swipe_ms": a["swipe_ms"]}
    if a["mode"] == "text" or a["text"]:
        d.update(text=a["text"], enter=a["enter"], click_first=a["click_first"],
                 method=a["method"])
    if a["out"] is not None:
        d["out"] = a["out"]
    return d


def action_target(a):
    """Target cho engine từ 1 nút tròn / 1 điểm combo (dict có "id" + ACTION_KEYS)."""
    mode, base = a["mode"], (a["id"], a["x"], a["y"], a["mouse"])
    if mode == "swipe" and a["x2"] is not None and a["y2"] is not None:
        return Target(*base, mode="swipe", x2=a["x2"], y2=a["y2"], dur=a["swipe_ms"])
    if mode == "text":
        return Target(*base, mode="text", text=a["text"], enter=a["enter"],
                      click=a["click_first"], method=a["method"])
    if mode == "key" and a["out"] is not None:
        return Target(*base, mode="key", out=a["out"])
    return Target(*base, mode=mode if mode in ("hold", "turbo") else "click")


def parse_buttons(items):
    """Đọc danh sách nút từ file JSON, bỏ qua dữ liệu hỏng."""
    out = []
    if not isinstance(items, list):
        return out
    for it in items:
        if not isinstance(it, dict):
            continue
        b = _parse_action(it)
        if b is None:
            continue
        try:
            size = int(it.get("size") or 0)
        except (TypeError, ValueError):
            size = 0
        key = it.get("key")
        if isinstance(key, bool) or not isinstance(key, int) or not 0 < key < 0xFF:
            key = None
        try:
            delay = max(0, min(MAX_DELAY_MS, int(it.get("delay", DEFAULT_DELAY_MS))))
        except (TypeError, ValueError):
            delay = DEFAULT_DELAY_MS
        b.update(size=size, key=key, delay=delay, in_script=bool(it.get("in_script", True)))
        out.append(b)
    return out


def parse_scripts(items, actions=()):
    """Đọc danh sách combo từ file JSON. Trả về None nếu là file kiểu cũ (chưa có "scripts").
    Mỗi bước là 1 điểm (vị trí + việc làm + thời gian chờ). File bản ≤ 1.9.3 ghi bước dạng
    {"button": i}: lấy vị trí + việc làm của nút thứ i (actions[i]) – combo cũ vẫn chạy y hệt."""
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
            if "button" in st:                          # kiểu cũ: trỏ tới nút tròn
                idx = st.get("button")
                if isinstance(idx, bool) or not isinstance(idx, int) or not 0 <= idx < len(actions):
                    continue
                p = dict((k, actions[idx][k]) for k in ACTION_KEYS)
            else:
                p = _parse_action(st)
                if p is None:
                    continue
            try:
                p["delay"] = max(0, min(MAX_DELAY_MS, int(st.get("delay", DEFAULT_STEP_DELAY_MS))))
            except (TypeError, ValueError):
                p["delay"] = DEFAULT_STEP_DELAY_MS
            steps.append(p)
        out.append({"name": name.strip()[:40], "key": key, "loops": loops,
                    "forever": bool(it.get("forever", False)), "steps": steps,
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


def _make_overlay(app, key, width, height, keyed=True):
    """Cửa sổ nhỏ không viền, luôn trên cùng; chỗ tô màu `key` sẽ trong suốt (Windows).
    keyed=False: cửa sổ sẽ được vẽ bằng ảnh có độ trong suốt từng điểm (nút tròn mịn)."""
    top = tk.Toplevel(app.root)
    top.withdraw()
    top.overrideredirect(True)
    top.configure(bg=key)
    top.attributes("-topmost", True)
    if app.api.is_windows and keyed:
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
      - lớp NỀN: hình tròn trắng dịu (độ đậm chỉnh được), nhận chuột để kéo / đổi cỡ.
        Windows: vẽ bằng ảnh có độ trong suốt TỪNG ĐIỂM (UpdateLayeredWindow) nên mép tròn
        mịn; máy nào không vẽ được thì quay về cách cũ (góc vuông tô "màu trong suốt").
      - lớp CHỮ: tên phím, luôn rõ nét, chuột đi xuyên qua"""

    _ids = itertools.count(1)
    MIN_SIZE, MAX_SIZE = 24, 320
    resizable = True                    # kéo mép / lăn chuột để đổi cỡ

    def __init__(self, app, cx, cy, size, key=None, button="left", mode="click",
                 x2=None, y2=None, swipe_ms=DEFAULT_SWIPE_MS, text="", text_enter=False,
                 text_click=False, text_method="paste", out=None):
        self.app = app
        self.text = text or ""          # nút Nhập chữ: chữ cần nhập
        self.text_enter = bool(text_enter)       # … nhấn Enter sau khi nhập
        self.text_click = bool(text_click)       # … click vào chỗ đặt nút trước khi nhập
        self.text_method = text_method if text_method in TEXT_METHODS else "paste"
        self.out = valid_vk(out)        # nút Phím: phím sẽ được bấm thay (vd Backspace)
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

        api = app.api
        smooth = api.is_windows and getattr(api, "smooth_ok", False)
        self._smooth = False            # lớp nền đang được vẽ mịn (UpdateLayeredWindow)
        self.top, self.canvas = _make_overlay(app, THEME["key"], self.size, self.size,
                                              keyed=not smooth)                  # lớp nền
        self.ftop, self.fcanvas = self._make_layer(THEME["key_text"])           # lớp chữ
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
        if smooth:                        # hiện tạm ngoài màn hình cho tới khi vẽ xong lớp nền
            self.top.geometry("+%d+%d" % (-32000, -32000))
        if api.is_windows:                # trên Windows nút luôn "hiện", ẩn bằng độ trong suốt
            self.top.deiconify()
            self.ftop.deiconify()
            self._shown = True
        self.hwnd = api.toplevel_hwnd(self.top)
        self.fhwnd = api.toplevel_hwnd(self.ftop)
        if app.enabled:                   # tạo lúc đang chơi (điểm của combo đang chạy): cho
            api.set_window_style(self.hwnd, click_through=True)    # chuột đi xuyên qua ngay,
            api.set_window_style(self.fhwnd, click_through=True)   # trước khi hiện lên
        if smooth:
            self._smooth = api.make_layered(self.hwnd)
            if not (self._smooth and self._paint_smooth()):
                self._to_classic()        # máy không vẽ mịn được: dùng cách cũ
            self._place()
        api.set_owner(self.fhwnd, self.hwnd)      # lớp chữ luôn nằm trên lớp nền
        self.apply_mode()
        self._fix_stack()                         # (chắc chắn: chữ không bị nền che mờ)
        if self.mode == "swipe":
            self._ensure_swipe()

    def _make_layer(self, key):
        return _make_overlay(self.app, key, self.size, self.size)

    # ---- nút vuốt ----
    def _ensure_swipe(self):
        if self.x2 is None or self.y2 is None:           # điểm đích mặc định: bên phải nút
            self.x2, self.y2 = self.app.default_swipe_target(self.cx, self.cy)
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

    def action(self):
        """Nút này làm gì, ở đâu (cùng dạng với 1 điểm combo)."""
        return {"id": self.id, "x": self.cx, "y": self.cy, "mouse": self.button,
                "mode": self.mode, "x2": self.x2, "y2": self.y2, "swipe_ms": self.swipe_ms,
                "text": self.text, "enter": self.text_enter, "click_first": self.text_click,
                "method": self.text_method, "out": self.out}

    def target(self):
        """Thông tin để engine click / vuốt / nhập chữ / bấm phím."""
        return action_target(self.action())

    def text_settings(self):
        return {"text": self.text, "enter": self.text_enter, "click": self.text_click,
                "method": self.text_method}

    # ---- trạng thái hiển thị ----
    def _visible(self):
        """F8 tắt (đang sửa): luôn hiện. F8 bật: theo công tắc "Hiện nút & điểm khi F8 bật"."""
        return self.editing or not self.app.enabled or self.app.cfg["show_play"]

    def _ring(self):
        return THEME["ring"]

    def _bg_fill(self):
        """(màu nền, độ đậm nền) theo trạng thái: nháy sáng / chờ gán phím / rê chuột / thường."""
        a = self.app.cfg["bg_alpha"]
        if self._flash_color:               # nháy sáng khi bấm phím: nền đậm lên một chút
            return self._flash_color, max(a, 0.6)
        if self.editing:
            return THEME["fill_edit"], max(a, 0.6)
        if self.hover:
            return THEME["fill_hover"], a
        return THEME["fill"], a

    def _global_alpha(self):
        """Độ đậm chung của cả nút: 0 = ẩn; đang chơi thì mờ thêm cho đỡ che game."""
        if not self._visible():
            return 0.0
        return self.app.cfg["play_dim"] if self.app.enabled else 1.0

    def _alphas(self):
        """Trả về (độ đậm lớp nền, độ đậm lớp chữ)."""
        g = self._global_alpha()
        return self._bg_fill()[1] * g, g

    def _paint_smooth(self):
        """Vẽ lớp nền: hình tròn mép mịn + viền mảnh, mỗi điểm ảnh 1 độ trong suốt."""
        d = self.size
        fill, a = self._bg_fill()
        ring_a = min(1.0, 0.1 + 0.45 * a)
        ring_w = round(max(1.2, d * 0.035), 1)
        img = _disc_image(d, fill, round(a, 3), self._ring(), round(ring_a, 3), ring_w)
        try:
            ok = self.app.api.layered_paint(self.hwnd, self.cx - d // 2, self.cy - d // 2,
                                            d, d, img, int(round(255 * self._global_alpha())))
        except Exception:
            log_exc("layered_paint")
            return False
        if ok:
            self._fix_stack()
        return ok

    _stack_failed = False

    def _fix_stack(self):
        """Windows: lớp chữ phải nằm ngay TRÊN lớp nền. Có lúc Windows đưa lớp nền lên trên
        (vd ngay khi vừa tạo điểm / vừa vẽ lại nền) – khi đó số / tên phím bị nền xanh / trắng
        che đi, trông như bị mờ. Gọi sau mỗi lần vẽ nền và 2 giây 1 lần (đã đúng thì bỏ qua)."""
        if not self.app.api.is_windows or Circle._stack_failed:
            return
        try:
            self.app.api.place_above(self.fhwnd, self.hwnd)
        except Exception:
            Circle._stack_failed = True             # máy không làm được: thôi, khỏi thử lại
            log_exc("stack")

    def _to_classic(self):
        """Không vẽ mịn được: quay về cách cũ (tô 1 màu trong suốt) cho nút này và nút sau."""
        if self._smooth or getattr(self.app.api, "smooth_ok", False):
            log("Không vẽ được nút tròn mịn – dùng cách vẽ cũ")
        self.app.api.smooth_ok = False
        self._smooth = False
        if self.app.api.is_windows:
            self.top.attributes("-transparentcolor", THEME["key"])
            self.top.attributes("-alpha", self._alphas()[0])
        self._draw_bg()

    def apply_alpha(self):
        if not self.app.api.is_windows:
            return
        if self._smooth:
            if not self._paint_smooth():
                self._to_classic()
        else:
            self.top.attributes("-alpha", self._alphas()[0])
            self._fix_stack()
        self.ftop.attributes("-alpha", self._global_alpha())

    def apply_mode(self):
        """Đang chơi: mờ hơn + chuột đi xuyên qua. Đang chỉnh: rõ hơn + kéo được."""
        app = self.app
        visible = self._visible()
        self.play = app.enabled             # đang hiện theo kiểu nào (chơi / chỉnh)
        if app.api.is_windows:
            self.apply_alpha()
        elif visible and not self._shown:
            self.top.deiconify()
            self.ftop.deiconify()
            self._shown = True
            self.top.update_idletasks()     # (máy thử, không phải Windows) lớp chữ nằm trên
            self.ftop.lift()
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
        if self._smooth:                    # Windows: hình tròn mịn
            if not self._paint_smooth():
                self._to_classic()
            return
        c = self.canvas                     # cách cũ: vẽ bằng Tk (mép không mịn bằng)
        c.delete("all")
        d = self.size
        fill = self._bg_fill()[0]
        w = max(1, int(round(d * 0.035)))
        c.create_oval(w / 2.0 + 0.5, w / 2.0 + 0.5, d - w / 2.0 - 0.5, d - w / 2.0 - 0.5,
                      fill=fill, outline=self._ring(), width=w)

    def _draw_fg(self):
        c = self.fcanvas
        c.delete("all")
        d = self.size
        color = _label_color(self)
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
            _outlined_text(c, d / 2.0, mid, label, color, (self.app.ui_family, -fs, "bold"),
                           1 if fs < 30 else 2)
        if tag and d >= 34:
            ts = max(8, int(d * 0.17))
            _outlined_text(c, d / 2.0, d * 0.755, tag, color, (self.app.ui_family, -ts, "bold"))
        if self.editing and self._caret_on:       # dấu nháy |
            h, w = d * 0.42, max(2, d // 24)
            c.create_line(d / 2.0, mid - h / 2, d / 2.0, mid + h / 2,
                          fill=THEME["outline"], width=w + 2)
            c.create_line(d / 2.0, mid - h / 2, d / 2.0, mid + h / 2,
                          fill=THEME["caret_text"], width=w)

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
        self._refresh_bg()
        if self._flash_job:
            self.top.after_cancel(self._flash_job)
        self._flash_job = self.top.after(ms, self._end_flash)

    def _end_flash(self):
        self._flash_job = None
        self._flash_color = None
        self._refresh_bg()

    def _refresh_bg(self):
        """Màu / độ đậm nền vừa đổi: vẽ lại lớp nền."""
        if self._smooth:
            self._draw_bg()                 # vẽ mịn đã gồm cả độ đậm
        else:
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
            self.changed()

    def resize(self, delta):
        self.set_size(self.size + delta)

    def _wheel(self, step):
        if self.resizable and not self.app.enabled:
            self.resize(step * max(4, int(self.size * 0.08)))

    def _in_rim(self, x, y):
        """(x, y) tính trong nút: có nằm ở MÉP nút (vùng kéo để đổi cỡ) không?"""
        if not self.resizable:
            return False
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
    def _press_mode(self, e):
        """Bấm chuột vào nút: Ctrl = nhân bản, ở mép = đổi cỡ, còn lại = di chuyển."""
        if e.state & 0x0004:
            return "dup"
        return "resize" if self._in_rim(e.x, e.y) else "move"

    def _on_press(self, e):
        if self.app.enabled:
            return
        mode = self._press_mode(e)
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
            self.on_click()
        self.changed()

    def on_click(self):
        """Bấm (không kéo) vào nút: gán lại phím."""
        self.start_edit()

    def changed(self):
        """Vị trí / cỡ / điểm vuốt vừa đổi: báo cho app (cập nhật phím, lưu lại)."""
        self.app.layout_changed()

    def _on_menu(self, e):
        if not self.app.enabled:
            self.app.show_circle_menu(self, e.x_root, e.y_root)

    def start_edit(self):
        self.app.begin_edit(self)

    def to_dict(self):
        d = {"x": self.cx, "y": self.cy, "size": self.size, "key": self.key}
        d.update(action_to_dict(self.action()))
        return d

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
        cv.create_oval(2, 2, m - 2, m - 2, fill=THEME["marker"], outline=THEME["caret"], width=w)
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
        cv.create_line(*pts, fill=THEME["arrow_outline"], width=lw + 3, arrow="last",
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
            self.c.changed()

    def destroy(self):
        self.ltop.destroy()
        self.btop.destroy()


class ComboPoint(Circle):
    """1 điểm của combo trên màn hình: hình tròn XANH có số thứ tự bước (1, 2, 3…), không có
    phím (khác nút tròn trắng ở tab Nút bấm – số của điểm chỉ là nhãn, không phải phím số).
    Kéo để dời chỗ; bấm = dòng bước của nó sáng lên; chuột phải = menu đổi việc làm.
    Hiện khi combo đó đang được chọn hoặc đang chạy (App._point_scripts). F8 bật thì nhạt hơn,
    chuột đi xuyên qua, điểm của bước đang làm sáng xanh lá (lit)."""

    resizable = False

    def __init__(self, app, p, num):
        self.p, self.num = p, num
        self.lit = False                  # combo đang chạy tới bước này
        Circle.__init__(self, app, p["x"], p["y"], app.point_size(), None, p["mouse"], p["mode"],
                        p["x2"], p["y2"], p["swipe_ms"], p["text"], p["enter"], p["click_first"],
                        p["method"], p["out"])
        self.id = p["id"]

    def _make_layer(self, key):
        return _make_overlay(self.app, POINT_KEY_TEXT, self.size, self.size)

    def _visible(self):
        return True                       # app chỉ tạo điểm khi cần hiện (sửa / đang chạy)

    def _ring(self):
        return POINT_RING

    def _bg_fill(self):
        if self._flash_color:
            return self._flash_color, 0.95
        if self.lit:
            return POINT_RUN, 0.95
        if self.app.enabled:              # combo đang chạy: nhạt đi cho đỡ che game
            return POINT_FILL, POINT_RUN_ALPHA
        return (POINT_FILL_HI if self.hover else POINT_FILL), 0.92

    def set_lit(self, on):
        """Combo đang chạy tới bước này (sáng xanh lá) / đã sang bước khác."""
        on = bool(on)
        if on != self.lit:
            self.lit = on
            self._refresh_bg()

    def _draw_fg(self):
        c = self.fcanvas
        c.delete("all")
        d = self.size
        tag = MODE_TAGS.get(self.mode)
        mid = d / 2.0 - (d * 0.08 if tag else 0)
        label = str(self.num)
        fs = max(8, int(min(d * 0.42, d * 0.8 / (0.62 * len(label)))))
        family = self.app.ui_family
        _outlined_text(c, d / 2.0, mid, label, POINT_TEXT, (family, -fs, "bold"), 1, POINT_OUTLINE)
        if tag and d >= 34:
            ts = max(7, int(d * 0.17))
            _outlined_text(c, d / 2.0, d * 0.76, tag, POINT_TEXT, (family, -ts, "bold"), 1,
                           POINT_OUTLINE)

    def _press_mode(self, e):
        return "move"                     # điểm: không nhân bản, không đổi cỡ

    def on_click(self):
        self.app.point_clicked(self.p)

    def changed(self):
        self.p.update(x=self.cx, y=self.cy, x2=self.x2, y2=self.y2)
        self.app.point_moved(self.p)

    def _on_menu(self, e):
        if not self.app.enabled:
            self.app.show_point_menu(self.p, e.x_root, e.y_root)

    def start_edit(self):
        pass                              # điểm không có phím

    def sync(self, p, num):
        """Theo dữ liệu điểm: số thứ tự mới (đổi thứ tự bước), việc làm mới, chỗ mới…"""
        self.p = p
        changed = num != self.num
        self.num = num
        for attr, k in (("button", "mouse"), ("swipe_ms", "swipe_ms"), ("text", "text"),
                        ("text_enter", "enter"), ("text_click", "click_first"),
                        ("text_method", "method"), ("out", "out")):
            if getattr(self, attr) != p[k]:
                setattr(self, attr, p[k])
                changed = True
        moved = (self.cx, self.cy, self.x2, self.y2) != (p["x"], p["y"], p["x2"], p["y2"])
        self.cx, self.cy, self.x2, self.y2 = p["x"], p["y"], p["x2"], p["y2"]
        if moved:
            self._place()
        if self.mode != p["mode"]:
            self.set_mode(p["mode"])          # vẽ lại, hiện / ẩn mũi tên vuốt
            p["x2"], p["y2"] = self.x2, self.y2
        elif changed or moved:
            self.redraw()
        if moved and self.guide is not None:
            self.guide.update()


class PickLayer(object):
    """Chọn điểm combo bằng cách click lên màn hình: 1 lớp mờ phủ hết các màn hình (con trỏ
    chữ thập) + dòng nhắc ở trên. Click trái = thêm 1 điểm (1 bước) đúng chỗ click; chuột phải
    = bỏ điểm vừa thêm; Esc / Enter / nút "Xong" = xong. Lớp mờ nhận hết cú click nên game
    không bị click trong lúc chọn."""

    def __init__(self, app, sid):
        S = app.px
        self.app, self.sid, self.added = app, sid, []
        vx, vy, vw, vh = app.vscreen()
        top = self.top = tk.Toplevel(app.root)
        top.withdraw()
        top.overrideredirect(True)
        top.configure(bg=PICK_SHADE, cursor="crosshair")
        top.attributes("-topmost", True)
        top.geometry("%dx%d+%d+%d" % (vw, vh, vx, vy))
        if app.api.is_windows:
            top.attributes("-alpha", 0.3)
        top.bind("<ButtonPress-1>", lambda e: app.pick_at(e.x_root, e.y_root))
        top.bind("<ButtonPress-3>", lambda e: app.pick_undo())
        for seq in ("<Escape>", "<Return>", "<KP_Enter>"):
            top.bind(seq, lambda e: app.end_pick())
        bar = self.bar = tk.Toplevel(app.root)              # dòng nhắc + nút Xong
        bar.withdraw()
        bar.overrideredirect(True)
        bar.attributes("-topmost", True)
        bar.configure(bg=UI["sel_line"])
        inner = tk.Frame(bar, bg=UI["card"], padx=S(16), pady=S(10))
        inner.pack(padx=1, pady=1)
        txt = tk.Frame(inner, bg=UI["card"])
        txt.pack(side="left")
        _label(txt, app, "Click vào các chỗ cần bấm trong game, theo thứ tự – mỗi click là 1 bước",
               "body_s", "bright").pack(anchor="w")
        self.lbl_info = _label(txt, app, "", "small", "muted")
        self.lbl_info.pack(anchor="w", pady=(S(3), 0))
        self.btn_done = RButton(inner, app, "Xong", kind="primary", height=S(36), width=S(84),
                                font=app.fonts["btn"], command=app.end_pick)
        self.btn_done.pack(side="left", padx=(S(18), 0))
        self.update_hint()

    def show(self):
        app, top, bar = self.app, self.top, self.bar
        top.deiconify()
        top.lift()
        bar.update_idletasks()
        x, y, w, h = app._work_area()
        bar.geometry("+%d+%d" % (x + max(0, (w - bar.winfo_reqwidth()) // 2), y + app.px(14)))
        bar.deiconify()
        for p in app.points.values():      # các điểm đã có nằm trên lớp mờ (kéo chỉnh được)
            app._raise_circle(p)
        self._raise_bar()
        try:
            top.focus_force()
        except tk.TclError:
            pass

    def _raise_bar(self):
        self.bar.lift()
        if self.app.api.is_windows:
            try:
                self.app.api.set_topmost(self.app.api.toplevel_hwnd(self.bar))
            except Exception:
                log_exc("pick bar")

    def update_hint(self):
        n = sum(1 for p in self.added if self.app._find_step(p)[0] is not None)
        self.lbl_info.configure(text="Đã thêm %d điểm  ·  Chuột phải: bỏ điểm vừa thêm  ·  "
                                     "Esc / Xong: xong" % n)

    def after_change(self):
        self.update_hint()
        self._raise_bar()

    def destroy(self):
        for w in (self.bar, self.top):
            try:
                w.destroy()
            except tk.TclError:
                pass


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


# ---------------------------------------------------------------------------
# Giao diện cửa sổ chính (bản 1.9): nền tối, thẻ bo tròn, công tắc, nút vẽ mịn.
#  Mọi hình bo tròn được vẽ sẵn thành ảnh (mép khử răng cưa, trộn sẵn với màu nền)
#  nên trông mịn như nhau trên mọi máy, không cần thư viện ngoài.
# ---------------------------------------------------------------------------
WIN_W, WIN_H = 480, 800         # cỡ cửa sổ chính (pixel ở 100%); màn hình thấp thì tự thấp lại
UI = {
    "bg": "#0f1621",            # nền cửa sổ
    "title": "#0a1018",         # thanh tiêu đề (Windows 11)
    "card": "#172131",          # thẻ, danh sách
    "card2": "#1a2536",         # các bước trong combo
    "row_hi": "#1b2738",        # dòng khi rê chuột
    "sel": "#1f2c40", "sel_line": "#3b5276",     # dòng đang chọn
    "line": "#243246",          # viền thẻ
    "sep": "#222e40",           # kẻ giữa các dòng
    "tip": "#131c29",           # khung gợi ý
    "field": "#0f1621", "field_line": "#34465f",
    "text": "#e6ebf2", "text2": "#a3b0c2", "muted": "#8b9ab0", "faint": "#5b6b80",
    "soft": "#d5dde8", "dim": "#c3ccd8", "bright": "#f1f5f9",
    "accent": "#2563eb", "accent_hi": "#1d4ed8", "accent_text": "#8fbcff",
    "btn": "#1b2636", "btn_hi": "#223049", "btn_line": "#34465f",
    "ghost_line": "#2c3a50", "ghost_hi": "#1a2433",
    "tab_on": "#2a3a52",
    "on": "#22c55e", "on_text": "#4ade80", "on_card": "#13261c", "on_line": "#1f4a33",
    "on_sub": "#a9c7b5", "on_key": "#1d3a2a", "on_key_line": "#2f5e44",
    "off_line": "#2a3850", "off_track": "#3a4a62", "off_knob": "#d5dde8",
    "warn_card": "#2a2312", "warn_line": "#5a4618", "warn_text": "#fcd34d", "warn_sub": "#e9dcb8",
    "warn_key": "#3a3015", "warn_key_line": "#6b5520",
    "err_card": "#2a171b", "err_line": "#5a2e35", "err_text": "#fca5a5", "err_sub": "#f0c4c4",
    "danger": "#fca5a5", "danger_line": "#4a2a2e", "danger_hi": "#2a171b",
    "play": "#1a3326", "play_hi": "#1f4030", "stop": "#3a1d22", "stop_hi": "#4a2329",
    "key_bg": "#243246", "key_line": "#34465f", "f9_bg": "#233a63", "f9_text": "#cfe0ff",
    "admin_card": "#1f1b12", "admin_line": "#4a3b16", "admin_text": "#e9dcb8", "admin_icon": "#fbbf24",
    "admin_btn": "#2d2512", "admin_btn_hi": "#3a3016", "admin_btn_line": "#8a6a1c",
    "admin_btn_text": "#fcd34d", "admin_track": "#4b4430", "admin_knob": "#e9dcb8",
    "chip": "#f3f5f8", "chip_ring": "#8a96a8", "hollow": "#6b7a90", "sample": "#31423a",
    "edit_chip": "#fde68a", "edit_ring": "#d4a72c", "capture": "#facc15", "capture_line": "#eab308",
    "capture_text": "#422006",
}
BADGES = {"hold": ("GIỮ", "#3a2e10", "#fcd34d"), "turbo": ("TURBO", "#2c2147", "#c4b5fd"),
          "swipe": ("VUỐT", "#0f3046", "#7dd3fc"), "text": ("CHỮ", "#0f3a2e", "#5eead4"),
          "key": ("PHÍM", "#3f1d33", "#f9a8d4")}
# Biểu tượng: font "Segoe Fluent Icons" (Windows 11) / "Segoe MDL2 Assets" (Windows 10);
# máy không có 2 font này thì dùng ký tự thường.
ICONS = {"add": ("", "+"), "edit": ("", "✎"), "more": ("", "⋯"),
         "delete": ("", "✕"), "play": ("", "▶"), "stop": ("", "■"),
         "up": ("", "▲"), "down": ("", "▼"), "close": ("", "✕"),
         "lock": ("", "▣"), "folder": ("", "▤"), "save": ("", "⤓"),
         "info": ("", "i"), "shield": ("", "!"), "swipe": ("", "➜"),
         "keyboard": ("", "⌨"), "remap": ("", "⇄"),
         "check": ("", "✓"), "warn": ("", "!"), "error": ("", "✕")}
ICON_FAMILIES = ("Segoe Fluent Icons", "Segoe MDL2 Assets")


def _blend(c1, c2, t):
    """Trộn 2 màu "#rrggbb": t = 0 -> c1, t = 1 -> c2."""
    a, b = _hex_rgb(c1), _hex_rgb(c2)
    return "#%02x%02x%02x" % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _ui(color):
    """Tên màu trong bảng UI ("card"...) hoặc mã màu "#rrggbb"."""
    return UI.get(color, color) if color else None


def render_rrect(w, h, r, fill, bg, border=None, bw=0.0):
    """Ảnh RGB w×h của hình chữ nhật bo góc MỊN nằm trên nền màu bg (dùng làm ảnh PPM).
    border, bw: màu và độ dày viền. r = w/2 = h/2 -> hình tròn.
    Chỉ tính từng điểm ảnh ở gần mép; phần giữa là các điểm/hàng giống nhau -> rất nhanh."""
    w, h = max(1, int(w)), max(1, int(h))
    r = max(0.0, min(float(r), w / 2.0, h / 2.0))
    F, B = _hex_rgb(fill or bg), _hex_rgb(bg)
    E = _hex_rgb(border) if (border and bw > 0) else None
    hw, hh = w / 2.0, h / 2.0
    bx, by = hw - r, hh - r
    hypot = math.hypot
    empty = bytes(B)

    def px(x, y):
        qx = abs(x + 0.5 - hw) - bx
        qy = abs(y + 0.5 - hh) - by
        sd = hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - r
        cov = 0.5 - sd                       # phần điểm ảnh nằm trong hình (0..1)
        if cov <= 0.0:
            return empty
        if cov > 1.0:
            cov = 1.0
        c = F
        if E is not None:
            t = sd + bw + 0.5                # 0 = ruột, 1 = viền
            if t > 0.0:
                t = 1.0 if t > 1.0 else t
                c = (F[0] + (E[0] - F[0]) * t, F[1] + (E[1] - F[1]) * t, F[2] + (E[2] - F[2]) * t)
        return bytes((int(B[0] + (c[0] - B[0]) * cov + 0.5), int(B[1] + (c[1] - B[1]) * cov + 0.5),
                      int(B[2] + (c[2] - B[2]) * cov + 0.5)))

    band = int(math.ceil(r + bw + 2))
    k = min(band, (w + 1) // 2)              # số cột ở mỗi bên cần tính từng điểm
    x_right = max(k, w - k)
    n_mid = x_right - k

    def row(y):
        mid = px(int(hw), y) * n_mid if n_mid > 0 else b""
        return (b"".join([px(x, y) for x in range(k)]) + mid
                + b"".join([px(x, y) for x in range(x_right, w)]))

    rows = []
    same = None                              # các hàng ở giữa giống hệt nhau
    for y in range(h):
        if band <= y < h - band:
            if same is None:
                same = row(y)
            rows.append(same)
        else:
            rows.append(row(y))
    return b"".join(rows)


def render_dashed_ring(d, color, bg, bw, n=10):
    """Vòng tròn nét đứt (nút chưa gán phím), ruột cùng màu nền."""
    d = int(d)
    C, B = _hex_rgb(color), _hex_rgb(bg)
    c = d / 2.0
    R = c - 0.5
    out = bytearray()
    for y in range(d):
        for x in range(d):
            dx, dy = x + 0.5 - c, y + 0.5 - c
            dist = math.hypot(dx, dy)
            cov = min(1.0, max(0.0, R + 0.5 - dist), max(0.0, dist - (R - bw) + 0.5))
            if cov > 0.0 and int((math.atan2(dy, dx) + math.pi) / math.pi * n) % 2:
                cov = 0.0
            out += bytes(int(B[i] + (C[i] - B[i]) * cov + 0.5) for i in range(3))
    return bytes(out)


def fit_text(font, text, width):
    """Cắt bớt chữ (thêm "…") cho vừa `width` pixel."""
    if width <= 0:
        return ""
    if font.measure(text) <= width:
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if font.measure(text[:mid].rstrip() + "…") <= width:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo].rstrip() + "…"


def fmt_ms(ms):
    """Thời gian dễ đọc: 200 ms, 1,5 giây, 2 phút, 1 giờ."""
    ms = int(ms)
    if ms < 1000:
        return "%d ms" % ms
    for unit, size in (("giờ", 3600000), ("phút", 60000), ("giây", 1000)):
        if ms >= size:
            v = ms / float(size)
            txt = ("%.1f" % v).rstrip("0").rstrip(".") if v < 100 else "%d" % round(v)
            return "%s %s" % (txt.replace(".", ","), unit)


def fit_chars(text, n):
    """Cắt chữ còn tối đa n ký tự (thêm "…"), gộp nhiều dòng thành 1."""
    text = " ⏎ ".join(text.splitlines())
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def wrap_text(font, text, width, max_lines):
    """Xuống dòng theo từ cho vừa `width`; quá `max_lines` dòng thì cắt bớt bằng "…"."""
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            cand = (cur + " " + word) if cur else word
            if not cur or font.measure(cand) <= width:
                cur = cand
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines - 1] + [" ".join(lines[max_lines - 1:]) + " …"]
    return "\n".join(fit_text(font, ln, width) for ln in lines)


class _ImageCache(object):
    """Ảnh vẽ sẵn (mép mịn) cho giao diện, dùng lại khi cùng kích thước / màu."""

    def __init__(self, root):
        self.root = root
        self._cache = {}

    def _photo(self, key, w, h, make):
        img = self._cache.get(key)
        if img is None:
            if len(self._cache) > 800:       # ảnh đang hiện vẫn được widget giữ lại
                self._cache.clear()
            img = tk.PhotoImage(master=self.root, format="PPM",
                                data=b"P6\n%d %d\n255\n" % (w, h) + make())
            self._cache[key] = img
        return img

    def rrect(self, w, h, r, fill, bg, border=None, bw=0.0):
        w, h = max(1, int(round(w))), max(1, int(round(h)))
        key = ("r", w, h, round(float(r), 2), fill, bg, border, round(float(bw), 2))
        return self._photo(key, w, h, lambda: render_rrect(w, h, r, fill, bg, border, bw))

    def disc(self, d, fill, bg, ring=None, ring_w=0.0):
        return self.rrect(d, d, d / 2.0, fill, bg, ring, ring_w)

    def dashed(self, d, color, bg, bw):
        d = int(d)
        return self._photo(("d", d, color, bg, round(float(bw), 2)), d, d,
                           lambda: render_dashed_ring(d, color, bg, bw))


def _bg_of(widget):
    try:
        return widget.cget("bg")
    except tk.TclError:
        return UI["bg"]


class _Drawn(tk.Canvas):
    """Khung vẽ (Canvas) không viền, không nhận focus; lớp cha của các widget vẽ tay."""

    def __init__(self, master, app, width, height, bg=None, cursor=""):
        self.app = app
        tk.Canvas.__init__(self, master, width=width, height=height, bg=bg or _bg_of(master),
                           highlightthickness=0, bd=0, takefocus=0, cursor=cursor)

    def size(self):
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1:
            w = int(float(self.cget("width")))
        if h <= 1:
            h = int(float(self.cget("height")))
        return w, h

    def set_bg(self, bg):
        if bg != self.cget("bg"):
            self.configure(bg=bg)
            self.redraw()

    def redraw(self):
        pass


def _set_disabled(widget, spec):
    """Giống .state() của ttk: None -> trả về các cờ; ["disabled"] / ["!disabled"] -> đặt."""
    if spec is None:
        return ("disabled",) if widget.disabled else ()
    old = widget.disabled
    for s in spec:
        if s == "disabled":
            widget.disabled = True
        elif s == "!disabled":
            widget.disabled = False
    if widget.disabled != old:
        widget.redraw()
    return ()


class RButton(_Drawn):
    """Nút bo tròn vẽ mịn: chữ và/hoặc biểu tượng. Bấm (nhả chuột trong nút) -> command()."""

    KINDS = {   # kiểu: (nền, nền khi rê chuột, viền, màu chữ); None = trong suốt
        "primary": ("accent", "accent_hi", None, "#ffffff"),
        "secondary": ("btn", "btn_hi", "btn_line", "text"),
        "ghost": (None, "ghost_hi", "ghost_line", "soft"),
        "outline": (None, "ghost_hi", "btn_line", "soft"),
        "danger": (None, "danger_hi", "danger_line", "danger"),
        "danger_fill": ("err_card", "stop_hi", "err_line", "danger"),
        "icon": (None, "key_bg", None, "text2"),
        "play": ("play", "play_hi", None, "on_text"),
        "stop": ("stop", "stop_hi", None, "danger"),
        "link": (None, "ghost_hi", None, "accent_text"),
        "link_danger": (None, "danger_hi", None, "danger"),
        "admin": ("admin_btn", "admin_btn_hi", "admin_btn_line", "admin_btn_text"),
    }

    def __init__(self, master, app, text="", icon=None, command=None, kind="secondary",
                 height=None, width=None, font=None, icon_font=None, radius=None, bg=None):
        S = app.px
        self.app, self.text, self.icon_name, self.command, self.kind = app, text, icon, command, kind
        self.h = height or S(36)
        self.font = font or app.fonts["btn_s"]
        self.ifont = icon_font or (app.fonts["icon"] if self.h >= S(34) else app.fonts["icon_s"])
        self.radius = radius if radius is not None else min(S(9), self.h / 2.0)
        self.disabled = self.hover = self.pressed = False
        self.fixed_w = width
        _Drawn.__init__(self, master, app, width or self._natural_width(), self.h, bg, "hand2")
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", lambda e: self.redraw())
        self.redraw()

    def _natural_width(self):
        S = self.app.px
        if not self.text:
            return self.h                    # nút chỉ có biểu tượng: vuông
        w = self.font.measure(self.text)
        if self.icon_name:
            w += self.ifont.measure(self.app.icon(self.icon_name)) + S(7)
        return w + 2 * (S(8) if self.kind in ("link", "link_danger") else S(14))

    def set_text(self, text):
        if text != self.text:
            self.text = text
            if not self.fixed_w:
                self.configure(width=self._natural_width())
            self.redraw()

    def set_icon(self, icon, kind=None):
        if icon != self.icon_name or (kind and kind != self.kind):
            self.icon_name = icon
            self.kind = kind or self.kind
            self.redraw()

    def state(self, spec=None):
        return _set_disabled(self, spec)

    def invoke(self):
        if not self.disabled and self.command:
            self.command()

    def _set_hover(self, on):
        if on != self.hover:
            self.hover = on
            self.redraw()

    def _on_press(self, e):
        if not self.disabled:
            self.pressed = True
            self.redraw()

    def _on_release(self, e):
        was, self.pressed = self.pressed, False
        if not self.winfo_exists():
            return
        self.redraw()
        if was and not self.disabled and 0 <= e.x < self.winfo_width() and 0 <= e.y < self.winfo_height():
            if self.command:
                self.command()

    def redraw(self):
        S = self.app.px
        w, h = self.size()
        bg = self.cget("bg")
        fill, hi, line, fg = (_ui(c) for c in self.KINDS.get(self.kind, self.KINDS["secondary"]))
        if self.disabled:
            fill = UI["btn"] if fill else None
            line = UI["line"] if line else None
            fg = UI["faint"]
        elif self.hover or self.pressed:
            fill = hi
        self.delete("all")
        if fill or line:
            self._img = self.app.img.rrect(w, h, self.radius, fill or bg, bg, line, 1.0 if line else 0)
            self.create_image(0, 0, image=self._img, anchor="nw")
        parts = []
        if self.icon_name:
            parts.append((self.app.icon(self.icon_name), self.ifont))
        if self.text:
            room = w - 2 * S(6) - (self.ifont.measure(parts[0][0]) + S(7) if parts else 0)
            parts.append((fit_text(self.font, self.text, room), self.font))
        gap = S(7) if len(parts) == 2 else 0
        total = sum(f.measure(t) for t, f in parts) + gap
        x = (w - total) / 2.0
        for t, f in parts:
            self.create_text(x, h / 2.0, text=t, font=f, fill=fg, anchor="w")
            x += f.measure(t) + gap


class Switch(_Drawn):
    """Công tắc bật/tắt vẽ mịn, gắn với 1 BooleanVar. Bấm -> đổi giá trị rồi gọi command()."""

    def __init__(self, master, app, variable, command=None, big=False, bg=None,
                 on_color=None, off_color=None, knob_off=None):
        S = app.px
        self.var, self.command = variable, command
        self.w, self.h = (S(52), S(30)) if big else (S(36), S(20))
        self.m = S(3) if big else S(2)
        self.on_color = _ui(on_color) or (UI["on"] if big else UI["accent"])
        self.off_color = _ui(off_color) or UI["off_track"]
        self.knob_off = _ui(knob_off) or UI["off_knob"]
        self.disabled = False
        _Drawn.__init__(self, master, app, self.w, self.h, bg, "hand2")
        self.bind("<ButtonRelease-1>", self._on_click)
        self._trace = variable.trace_add("write", lambda *a: self.redraw())
        self.bind("<Destroy>", self._on_destroy, add="+")
        self.redraw()

    def _on_destroy(self, e):
        if e.widget is self:
            try:
                self.var.trace_remove("write", self._trace)
            except (tk.TclError, ValueError):
                pass

    def state(self, spec=None):
        return _set_disabled(self, spec)

    def toggle(self):
        if not self.disabled:
            self.var.set(not bool(self.var.get()))
            if self.command:
                self.command()

    def _on_click(self, e):
        if 0 <= e.x < self.w and 0 <= e.y < self.h:
            self.toggle()

    def redraw(self):
        try:
            on = bool(self.var.get())
        except tk.TclError:
            return
        bg = self.cget("bg")
        track = self.on_color if on else self.off_color
        knob = "#ffffff" if on else self.knob_off
        if self.disabled:
            track, knob = _blend(track, bg, 0.55), _blend(knob, bg, 0.55)
        kd = self.h - 2 * self.m
        self._imgs = (self.app.img.rrect(self.w, self.h, self.h / 2.0, track, bg),
                      self.app.img.disc(kd, knob, track))
        self.delete("all")
        self.create_image(0, 0, image=self._imgs[0], anchor="nw")
        x = self.w - self.m - kd if on else self.m
        self.create_image(x, self.m, image=self._imgs[1], anchor="nw")


class Card(tk.Canvas):
    """Thẻ nền bo tròn (vẽ mịn). Đặt nội dung vào .body.
    fill_mode=False: thẻ cao theo nội dung. True: nội dung giãn theo cỡ thẻ (thẻ được
    pack/grid giãn ra), cỡ tối thiểu = cỡ nội dung yêu cầu."""

    def __init__(self, master, app, fill="card", border="line", radius=12, pad=12, bg=None,
                 fill_mode=False, padx=None, pady=None):
        self.app = app
        self.fill, self.border = _ui(fill), _ui(border)
        self.radius = app.px(radius)
        tk.Canvas.__init__(self, master, bg=bg or _bg_of(master), highlightthickness=0, bd=0,
                           width=1, height=1, takefocus=0)
        self.inset = int(math.ceil(self.radius * 0.3)) + 1
        px_ = max(0, app.px(pad if padx is None else padx) - self.inset)
        py_ = max(0, app.px(pad if pady is None else pady) - self.inset)
        self.body = tk.Frame(self, bg=self.fill, padx=px_, pady=py_)
        self._win = self.create_window(self.inset, self.inset, window=self.body, anchor="nw")
        self.fill_mode = fill_mode
        self._drawn = None
        cards = getattr(app, "_cards", None)
        if cards is not None:
            cards.append(self)
        self.body.bind("<Configure>", lambda e: self.fit(), add="+")
        self.bind("<Configure>", self._on_canvas, add="+")
        self.after_idle(self.fit)            # nội dung được thêm vào .body sau khi tạo thẻ

    def fit(self):
        """Cỡ yêu cầu của thẻ = cỡ nội dung (gọi lại nếu nội dung đổi cỡ)."""
        h = self.body.winfo_reqheight() + 2 * self.inset
        if int(float(self.cget("height"))) != h:
            self.configure(height=h)

    def _on_canvas(self, e):
        kw = {"width": max(1, e.width - 2 * self.inset)}
        if self.fill_mode:
            kw["height"] = max(1, e.height - 2 * self.inset)
        self.itemconfigure(self._win, **kw)
        self.redraw()

    def redraw(self):
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1 or h <= 1:
            return
        key = (w, h, self.fill, self.border, self.cget("bg"))
        if key == self._drawn:
            return
        self._drawn = key
        self._img = self.app.img.rrect(w, h, self.radius, self.fill, self.cget("bg"), self.border,
                                       1.0 if self.border else 0)
        self.delete("bgimg")
        self.create_image(0, 0, image=self._img, anchor="nw", tags="bgimg")
        self.tag_lower("bgimg")


class ScrollArea(tk.Frame):
    """Vùng cuộn dọc; nội dung đặt vào .inner. Thanh cuộn mảnh chỉ hiện khi cần.
    fit=True: nội dung giãn cao bằng vùng nhìn thấy (để các phần "expand" bên trong được
    giãn); vùng thấp hơn nội dung thì cuộn được (màn hình thấp)."""

    _areas = []

    def __init__(self, master, app, bg, min_height=1, fit=False):
        tk.Frame.__init__(self, master, bg=bg)
        self.app, self.bg, self.fit = app, bg, fit
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0, width=1,
                                height=max(1, int(min_height)), takefocus=0, yscrollincrement=1)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.bar = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0, width=app.px(8), height=1,
                             takefocus=0)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.need = False
        self._bar_on = False
        self._cfg = None
        self.inner.bind("<Configure>", lambda e: self.layout(), add="+")
        self.canvas.bind("<Configure>", lambda e: self.layout(), add="+")
        self.bar.bind("<Configure>", lambda e: self._draw_bar())
        self.bar.bind("<ButtonPress-1>", self._on_bar)
        self.bar.bind("<B1-Motion>", self._on_bar)
        ScrollArea._areas.append(self)
        self.bind("<Destroy>", lambda e: e.widget is self and self._forget(), add="+")

    def _forget(self):
        if self in ScrollArea._areas:
            ScrollArea._areas.remove(self)

    def layout(self):
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            return
        req = self.inner.winfo_reqheight()
        need = req > ch + 1
        if need != self._bar_on:                 # hiện/ẩn thanh cuộn -> vùng nhìn đổi rộng
            self._bar_on = need
            if need:
                self.bar.pack(side="right", fill="y")
            else:
                self.bar.pack_forget()
            return
        self.need = need
        h = max(ch, req) if self.fit else 0      # 0 = cao theo nội dung
        if (cw, h) != self._cfg:
            self._cfg = (cw, h)
            self.canvas.itemconfigure(self._win, width=cw, height=h)
        self.canvas.configure(scrollregion=(0, 0, cw, max(ch, req)))
        if not need:
            self.canvas.yview_moveto(0)
        self._draw_bar()

    def _draw_bar(self):
        self.bar.delete("all")
        if not self.need:
            return
        top, bottom = self.canvas.yview()
        H = max(1, self.bar.winfo_height())
        w = self.app.px(4)
        y0 = top * H
        y1 = max(y0 + self.app.px(16), bottom * H)
        x0 = (self.bar.winfo_width() - w) / 2.0
        self._img = self.app.img.rrect(w, max(w, y1 - y0), w / 2.0, UI["field_line"], self.bg)
        self.bar.create_image(x0, y0, image=self._img, anchor="nw")

    def scroll(self, pixels):
        if self.need:
            self.canvas.yview_scroll(int(pixels), "units")     # 1 unit = 1 pixel
            self._draw_bar()

    def _on_bar(self, e):
        if self.need:
            H = max(1, self.bar.winfo_height())
            top, bottom = self.canvas.yview()
            self.canvas.yview_moveto(max(0.0, min(1.0, e.y / float(H) - (bottom - top) / 2.0)))
            self._draw_bar()

    def see(self, widget):
        """Cuộn để thấy trọn widget (1 dòng trong .inner)."""
        self.inner.update_idletasks()
        self.layout()
        if not self.need:
            return
        y, h = widget.winfo_y(), widget.winfo_height()
        top, ch = self.canvas.canvasy(0), self.canvas.winfo_height()
        if y < top:
            self.canvas.yview_scroll(int(y - top), "units")
        elif y + h > top + ch:
            self.canvas.yview_scroll(int(y + h - top - ch), "units")
        self._draw_bar()

    @classmethod
    def wheel(cls, root, e):
        """Lăn chuột: cuộn vùng cuộn nằm trong cùng dưới con trỏ."""
        try:
            w = root.winfo_containing(e.x_root, e.y_root)
        except (tk.TclError, KeyError):
            return
        if w is None:
            return
        path, best = str(w), None
        for area in cls._areas:
            p = str(area)
            if area.need and (path == p or path.startswith(p + ".")):
                if best is None or len(p) > len(str(best)):
                    best = area
        if best is not None:
            up = getattr(e, "delta", 0) > 0 or getattr(e, "num", 0) == 4
            best.scroll(-best.app.px(48) if up else best.app.px(48))


class TabBar(_Drawn):
    """Các tab kiểu nút gạt (segmented). Bấm tab -> command(chỉ số)."""

    def __init__(self, master, app, labels, command, bg=None):
        S = app.px
        self.labels, self.command = list(labels), command
        self.index, self.badges = 0, {}
        _Drawn.__init__(self, master, app, 10, S(42), bg, "hand2")
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<ButtonRelease-1>", self._on_click)

    def _segments(self):
        S = self.app.px
        w = max(self.winfo_width(), 10)
        pad = gap = S(4)
        n = len(self.labels)
        sw = (w - 2 * pad - gap * (n - 1)) / float(n)
        return [(pad + i * (sw + gap), sw) for i in range(n)]

    def _on_click(self, e):
        for i, (x, sw) in enumerate(self._segments()):
            if x <= e.x <= x + sw:
                self.command(i)
                return

    def select(self, i):
        if i != self.index:
            self.index = i
            self.redraw()

    def set_badge(self, i, text):
        if self.badges.get(i) != text:
            self.badges[i] = text
            self.redraw()

    def redraw(self):
        S = self.app.px
        w, h = self.size()
        if w <= 10:
            return
        bg = self.cget("bg")
        imgs = [self.app.img.rrect(w, h, S(10), UI["card"], bg, UI["line"], 1.0)]
        self.delete("all")
        self.create_image(0, 0, image=imgs[0], anchor="nw")
        f_on, f_off, bf = self.app.fonts["body_s"], self.app.fonts["body"], self.app.fonts["key"]
        for i, (x, sw) in enumerate(self._segments()):
            on = i == self.index
            seg_bg = UI["tab_on"] if on else UI["card"]
            if on:
                imgs.append(self.app.img.rrect(sw, h - 2 * S(4), S(7), UI["tab_on"], UI["card"]))
                self.create_image(x, S(4), image=imgs[-1], anchor="nw")
            font = f_on if on else f_off
            label, badge = self.labels[i], self.badges.get(i)
            tw = font.measure(label)
            bw = bf.measure(badge) + S(12) if badge else 0
            cx = x + (sw - tw - (bw + S(6) if badge else 0)) / 2.0
            self.create_text(cx, h / 2.0, text=label, font=font, anchor="w",
                             fill=UI["bright"] if on else UI["text2"])
            if badge:
                bh = S(17)
                imgs.append(self.app.img.rrect(bw, bh, bh / 2.0, UI["f9_bg"], seg_bg))
                bx = cx + tw + S(6)
                self.create_image(bx, (h - bh) / 2.0, image=imgs[-1], anchor="nw")
                self.create_text(bx + bw / 2.0, h / 2.0, text=badge, font=bf, fill=UI["f9_text"])
        self._imgs = imgs


def draw_keycap(canvas, app, x, y, text, anchor="w", fill=None, line=None, fg=None, font=None,
                height=None, min_w=None, bg=None):
    """Vẽ 1 ô phím kiểu bàn phím (F8, Q, Esc…) lên canvas; trả về (x0, x1) đã dùng."""
    S = app.px
    font = font or app.fonts["key"]
    h = height or S(21)
    w = max(min_w or S(22), font.measure(text) + S(14))
    bg = bg or canvas.cget("bg")
    fill, line, fg = _ui(fill) or UI["key_bg"], _ui(line) or UI["key_line"], _ui(fg) or UI["text"]
    x0 = x if anchor == "w" else (x - w if anchor == "e" else x - w / 2.0)
    y0 = y - h / 2.0
    outer = app.img.rrect(w, h, S(5), line, bg)
    inner = app.img.rrect(w - 2, h - 3, max(1, S(5) - 1), fill, line)
    keep = getattr(canvas, "_keycaps", [])
    keep += [outer, inner]
    canvas._keycaps = keep[-24:]
    canvas.create_image(x0, y0, image=outer, anchor="nw", tags="d")
    canvas.create_image(x0 + 1, y0 + 1, image=inner, anchor="nw", tags="d")
    canvas.create_text(x0 + w / 2.0, y0 + (h - 1) / 2.0, text=text, font=font, fill=fg, tags="d")
    return x0, x0 + w


class KeyCap(_Drawn):
    """Ô phím đứng riêng (dùng trong khung sửa combo)."""

    def __init__(self, master, app, text, bg=None, height=None, min_w=None, font=None):
        S = app.px
        self.app, self.text = app, text
        self.kfont = font or app.fonts["key"]
        self.kh = height or S(24)
        self.min_w = min_w or S(26)
        self.colors = (None, None, None)
        _Drawn.__init__(self, master, app, self._width(), self.kh, bg)
        self.redraw()

    def _width(self):
        return max(self.min_w, self.kfont.measure(self.text) + self.app.px(16))

    def set(self, text, fill=None, line=None, fg=None):
        if (text, (fill, line, fg)) != (self.text, self.colors):
            self.text, self.colors = text, (fill, line, fg)
            self.configure(width=self._width())
            self.redraw()

    def redraw(self):
        self._keycaps = []
        self.delete("all")
        w = self._width()
        draw_keycap(self, self.app, w / 2.0, self.kh / 2.0, self.text, "center", *self.colors,
                    font=self.kfont, height=self.kh, min_w=w)


class Slider(_Drawn):
    """Thanh trượt vẽ mịn (gắn với 1 biến số). Kéo / bấm -> đặt giá trị rồi gọi command()."""

    def __init__(self, master, app, variable, from_, to, command=None, bg=None):
        S = app.px
        self.var, self.lo, self.hi, self.command = variable, from_, to, command
        _Drawn.__init__(self, master, app, S(120), S(22), bg, "hand2")
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<ButtonPress-1>", self._set_from_x)
        self.bind("<B1-Motion>", self._set_from_x)
        self._trace = variable.trace_add("write", lambda *a: self.redraw())
        self.bind("<Destroy>", lambda e: e.widget is self and self._untrace(), add="+")

    def _untrace(self):
        try:
            self.var.trace_remove("write", self._trace)
        except (tk.TclError, ValueError):
            pass

    def _span(self):
        k = self.app.px(16)
        return k / 2.0, max(k, self.winfo_width()) - k / 2.0

    def _set_from_x(self, e):
        x0, x1 = self._span()
        t = max(0.0, min(1.0, (e.x - x0) / max(1.0, x1 - x0)))
        v = int(round(self.lo + t * (self.hi - self.lo)))
        if v != self.var.get():
            self.var.set(v)
            if self.command:
                self.command()

    def redraw(self):
        S = self.app.px
        try:
            v = float(self.var.get())
        except (tk.TclError, ValueError):
            return
        w, h = self.size()
        bg = self.cget("bg")
        x0, x1 = self._span()
        t = max(0.0, min(1.0, (v - self.lo) / float(self.hi - self.lo)))
        th, kd = S(4), S(16)
        xk = x0 + t * (x1 - x0)
        track = self.app.img.rrect(max(2, x1 - x0), th, th / 2.0, UI["off_track"], bg)
        part = self.app.img.rrect(max(th, xk - x0), th, th / 2.0, UI["accent"], bg)
        knob = self.app.img.disc(kd, "#ffffff", bg, UI["accent"], S(2))
        self._imgs = (track, part, knob)
        self.delete("all")
        self.create_image(x0, (h - th) / 2.0, image=track, anchor="nw")
        self.create_image(x0, (h - th) / 2.0, image=part, anchor="nw")
        self.create_image(xk - kd / 2.0, (h - kd) / 2.0, image=knob, anchor="nw")


class Field(_Drawn):
    """Ô nhập bo tròn. kind="text" (gõ chữ) hoặc "number" (gõ số; phím ↑ ↓ tăng / giảm).
    Ô nhập thật (tk.Entry) là .entry; KeyClick dựa vào kind để biết đang gõ chữ hay số.
    Ô số: chỉ gõ được chữ số, tối đa bằng số chữ số của `hi`; rời ô (hoặc Enter) thì số
    được đưa về trong khoảng lo..hi (ô trống / sai = số đúng gần nhất) -> ô không bao giờ
    chứa số dài tràn khung."""

    def __init__(self, master, app, variable, width, height=None, kind="text", font=None,
                 bg=None, justify="left", lo=0, hi=999999, step=1):
        S = app.px
        self.kind, self.lo, self.hi, self.step = kind, lo, hi, step
        self.focused = False
        self.disabled = False
        self.var = variable
        h = height or S(32)
        _Drawn.__init__(self, master, app, width, h, bg, "xterm")
        self.entry = tk.Entry(self, textvariable=variable, bd=0, relief="flat", highlightthickness=0,
                              bg=UI["field"], fg=UI["text"], insertbackground=UI["text"],
                              disabledbackground=UI["field"], disabledforeground=UI["faint"],
                              readonlybackground=UI["field"], selectbackground=UI["accent"],
                              selectforeground="#ffffff", font=font or app.fonts["body"],
                              justify=justify, width=1, insertwidth=max(1, S(1)))
        self.entry.kc_kind = kind
        self.pad = S(8)
        self._win = self.create_window(self.pad, h / 2.0, window=self.entry, anchor="w")
        self.entry.bind("<FocusIn>", lambda e: self._focus(True), add="+")
        self.entry.bind("<FocusOut>", self._on_focus_out, add="+")
        self.bind("<ButtonPress-1>", lambda e: self.disabled or self.entry.focus_set())
        self.bind("<Configure>", lambda e: self.redraw())
        if kind == "number":
            self.maxlen = len(str(hi))
            self.last_valid = lo
            self._remember()
            self.entry.configure(validate="key",
                                 validatecommand=(self.register(self._valid_number), "%P"))
            variable.trace_add("write", self._remember)
            self.entry.bind("<Up>", lambda e: self._bump(1))
            self.entry.bind("<Down>", lambda e: self._bump(-1))
        self.redraw()

    def _valid_number(self, new):
        return new == "" or (len(new) <= self.maxlen and all("0" <= ch <= "9" for ch in new))

    def _remember(self, *a):
        try:
            v = int(str(self.var.get()).strip())
        except (ValueError, tk.TclError):
            return
        if self.lo <= v <= self.hi:
            self.last_valid = v

    def normalize(self):
        """Ô số: đưa số về trong khoảng lo..hi (ô trống / sai = số đúng gần nhất)."""
        if self.kind != "number":
            return
        try:
            v = int(str(self.var.get()).strip())
        except (ValueError, tk.TclError):
            v = self.last_valid
        v = max(self.lo, min(self.hi, v))
        if str(self.var.get()) != str(v):
            self.var.set(str(v))

    def _focus(self, on):
        self.focused = on
        self.redraw()

    def _on_focus_out(self, e=None):
        try:
            self.entry.selection_clear()     # bỏ bôi đen khi rời ô nhập
            if self.winfo_exists():
                self.normalize()
        except tk.TclError:
            pass
        self._focus(False)

    def _bump(self, sign):
        try:
            v = int(str(self.var.get()).strip())
        except ValueError:
            v = self.lo
        self.var.set(str(max(self.lo, min(self.hi, v + sign * self.step))))
        self.entry.icursor("end")
        return "break"

    def state(self, spec=None):
        r = _set_disabled(self, spec)
        if spec is not None:
            self.entry.configure(state="disabled" if self.disabled else "normal")
            self.configure(cursor="" if self.disabled else "xterm")
        return r

    def redraw(self):
        S = self.app.px
        w, h = self.size()
        bg = self.cget("bg")
        line = UI["accent"] if (self.focused and not self.disabled) else (
            UI["line"] if self.disabled else UI["field_line"])
        self._img = self.app.img.rrect(w, h, S(7), UI["field"], bg, line, 1.0)
        self.delete("bgimg")
        self.create_image(0, 0, image=self._img, anchor="nw", tags="bgimg")
        self.tag_lower("bgimg")
        self.itemconfigure(self._win, width=max(1, w - 2 * self.pad))
        self.coords(self._win, self.pad, h / 2.0)


class MessageBar(_Drawn):
    """Dòng thông báo cố định ở cuối cửa sổ (2 dòng chữ). Không có thông báo thì hiện gợi ý
    của tab đang mở. Thông báo tự tắt sau `ms` (None = giữ tới khi có thông báo khác)."""

    KINDS = {   # nền, viền, màu chữ, màu biểu tượng, biểu tượng
        "tip": ("tip", None, "muted", "muted", "info"),
        "info": ("card", "line", "dim", "accent_text", "info"),
        "ok": ("on_card", "on_line", "on_sub", "on_text", "check"),
        "warn": ("warn_card", "warn_line", "warn_sub", "warn_text", "warn"),
        "error": ("err_card", "err_line", "err_sub", "err_text", "error"),
    }

    def __init__(self, master, app, lines=2):
        S = app.px
        self.lines = lines
        f = app.fonts["tiny"]
        self.line_h = f.metrics("linespace")
        h = self.line_h * lines + S(18)
        _Drawn.__init__(self, master, app, 10, h)
        self.tip = ""
        self.msg = None                  # (chữ, kiểu, nhãn)
        self._job = None
        self.bind("<Configure>", lambda e: self.redraw())

    @property
    def text(self):
        return self.msg[0] if self.msg else self.tip

    @property
    def kind(self):
        return self.msg[1] if self.msg else "tip"

    @property
    def tag(self):
        return self.msg[2] if self.msg else None

    def set_tip(self, text):
        if text != self.tip:
            self.tip = text
            if self.msg is None:
                self.redraw()

    def show(self, text, kind="info", ms=5000, tag=None):
        if not text:
            self.clear(tag)
            return
        self._cancel()
        self.msg = (text, kind, tag)
        if ms:
            self._job = self.after(ms, self.clear)
        self.redraw()

    def clear(self, tag=None):
        """Xoá thông báo (tag: chỉ xoá nếu thông báo đang hiện có nhãn này)."""
        if self.msg is None or (tag is not None and self.msg[2] != tag):
            return
        self._cancel()
        self.msg = None
        self.redraw()

    def _cancel(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None

    def redraw(self):
        S = self.app.px
        w, h = self.size()
        if w <= 10:
            return
        bg = self.cget("bg")
        fill, line, fg, ic, icon = (_ui(c) if i < 4 else c
                                    for i, c in enumerate(self.KINDS.get(self.kind, self.KINDS["tip"])))
        self.delete("all")
        self._img = self.app.img.rrect(w, h, S(10), fill, bg, line, 1.0 if line else 0)
        self.create_image(0, 0, image=self._img, anchor="nw")
        f = self.app.fonts["tiny"]
        x = S(12)
        self.create_text(x + S(7), S(9) + self.line_h / 2.0, text=self.app.icon(icon),
                         font=self.app.fonts["icon_xs"], fill=ic)
        x += S(14) + S(8)
        body = wrap_text(f, self.text, w - x - S(12), self.lines)
        self.create_text(x, S(9), text=body, font=f, fill=fg, anchor="nw")


class StatusCard(_Drawn):
    """Thẻ trạng thái to ở đầu cửa sổ: công tắc bật/tắt + chữ ĐANG BẬT / ĐANG TẮT…"""

    STYLES = {   # nền, viền, chữ to, chữ nhỏ, ô phím, viền ô phím
        "on": ("on_card", "on_line", "on_text", "on_sub", "on_key", "on_key_line"),
        "off": ("card", "off_line", "text", "text2", "key_bg", "key_line"),
        "warn": ("warn_card", "warn_line", "warn_text", "warn_sub", "warn_key", "warn_key_line"),
        "err": ("err_card", "err_line", "err_text", "err_sub", "key_bg", "key_line"),
    }

    def __init__(self, master, app, command, key_text):
        S = app.px
        self.command, self.key_text = command, key_text
        self.style, self.title, self.sub, self.on, self.disabled = "off", "", "", False, False
        _Drawn.__init__(self, master, app, 10, S(58))
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<ButtonRelease-1>", self._on_click)
        self.bind("<Motion>", self._on_motion)

    def _switch_box(self):
        S = self.app.px
        h = self.size()[1]
        return S(16), (h - S(30)) / 2.0, S(16) + S(52), (h + S(30)) / 2.0

    def _in_switch(self, e):
        x0, y0, x1, y1 = self._switch_box()
        m = self.app.px(4)
        return x0 - m <= e.x <= x1 + m and y0 - m <= e.y <= y1 + m

    def _on_motion(self, e):
        self.configure(cursor="hand2" if self._in_switch(e) and not self.disabled else "")

    def _on_click(self, e):
        if self._in_switch(e) and not self.disabled and self.command:
            self.command()

    def set(self, style, title, sub, on, disabled=False):
        state = (style, title, sub, bool(on), bool(disabled))
        if state != (self.style, self.title, self.sub, self.on, self.disabled):
            self.style, self.title, self.sub, self.on, self.disabled = state
            self.redraw()

    def redraw(self):
        S = self.app.px
        w, h = self.size()
        if w <= 10:
            return
        bg = self.cget("bg")
        fill, line, tcol, scol, kfill, kline = (_ui(c) for c in self.STYLES[self.style])
        self.delete("all")
        imgs = [self.app.img.rrect(w, h, S(12), fill, bg, line, 1.0)]
        self.create_image(0, 0, image=imgs[0], anchor="nw")
        x0, y0, x1, y1 = self._switch_box()
        track = UI["on"] if self.on else UI["off_track"]
        knob = "#ffffff" if self.on else UI["off_knob"]
        if self.disabled:
            track, knob = _blend(track, fill, 0.55), _blend(knob, fill, 0.55)
        kd = S(24)
        imgs.append(self.app.img.rrect(S(52), S(30), S(15), track, fill))
        imgs.append(self.app.img.disc(kd, knob, track))
        self.create_image(x0, y0, image=imgs[1], anchor="nw")
        self.create_image(x1 - S(3) - kd if self.on else x0 + S(3), y0 + S(3), image=imgs[2],
                          anchor="nw")
        self._imgs = imgs
        self._keycaps = []
        # bên phải: [F8] bật/tắt
        fs = self.app.fonts["small"]
        xr = w - S(16)
        label = "bật/tắt"
        self.create_text(xr, h / 2.0, text=label, font=fs, fill=scol, anchor="e")
        kx0, kx1 = draw_keycap(self, self.app, xr - fs.measure(label) - S(6), h / 2.0,
                               self.key_text, "e", kfill, kline, bg=fill)
        tx = x1 + S(14)
        room = kx0 - S(12) - tx
        ft = self.app.fonts["title"]
        self.create_text(tx, h / 2.0 - S(9), text=fit_text(ft, self.title, room), font=ft,
                         fill=tcol, anchor="w")
        self.create_text(tx, h / 2.0 + S(11), text=fit_text(fs, self.sub, room), font=fs,
                         fill=scol, anchor="w")


def _section_label(master, app, text, bg=None):
    return tk.Label(master, text=text, font=app.fonts["label"], fg=UI["muted"],
                    bg=bg or _bg_of(master), bd=0, padx=0, pady=0)


def _label(master, app, text="", font="body", fg="text", bg=None, **kw):
    return tk.Label(master, text=text, font=app.fonts[font], fg=_ui(fg), bg=bg or _bg_of(master),
                    bd=0, padx=0, pady=0, **kw)


class _Row(_Drawn):
    """1 dòng trong danh sách (vẽ tay): rê chuột thì sáng lên, bấm vào dòng -> on_click()."""

    def __init__(self, master, app, height, base_bg):
        self.base_bg = base_bg
        self.hover = False
        self.data = None
        self.buttons = []
        _Drawn.__init__(self, master, app, 1, height, base_bg)
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _set_hover(self, on):
        if on != self.hover:
            self.hover = on
            self.redraw()

    def _on_leave(self, e):
        # đi vào nút con bên trong dòng cũng sinh <Leave>: kiểm tra con trỏ còn trong dòng không
        try:
            x, y = self.winfo_pointerxy()
            w = self.winfo_containing(x, y)
        except (tk.TclError, KeyError):
            w = None
        inside = w is not None and (w is self or str(w).startswith(str(self) + "."))
        self._set_hover(inside)

    def _on_release(self, e):
        if 0 <= e.x < self.winfo_width() and 0 <= e.y < self.winfo_height():
            self.on_click()

    def on_click(self):
        pass

    def update_data(self, data):
        if data != self.data:
            self.data = data
            self.redraw()

    def _paint_bg(self, bg):
        if bg != self.cget("bg"):
            self.configure(bg=bg)
        for b in self.buttons:
            b.set_bg(bg)


class CircleRow(_Row):
    """1 nút tròn trong tab "Nút bấm": phím, kiểu click, nút đổi phím (bút chì) và nút ⋯.
    Bấm vào dòng: nút tròn tương ứng nháy sáng trên màn hình (để biết nút nào)."""

    def __init__(self, master, app, cid):
        S = app.px
        self.cid = cid
        _Row.__init__(self, master, app, S(48), UI["card"])
        self.btn_more = RButton(self, app, icon="more", kind="icon", height=S(34), bg=UI["card"],
                                command=self._more)
        self.btn_edit = RButton(self, app, icon="edit", kind="icon", height=S(34), bg=UI["card"],
                                command=lambda: app.edit_circle(cid))
        self.buttons = [self.btn_more, self.btn_edit]
        self._w_more = self.create_window(0, 0, window=self.btn_more, anchor="e")
        self._w_edit = self.create_window(0, 0, window=self.btn_edit, anchor="e")

    def _more(self):
        b = self.btn_more
        self.app.circle_menu_from_list(self.cid, b.winfo_rootx(), b.winfo_rooty() + b.winfo_height())

    def on_click(self):
        self.app.locate_circle(self.cid)

    def redraw(self):
        if self.data is None:
            return
        S, app = self.app.px, self.app
        w, h = self.size()
        first, state, key_text, key_color, title, sub, badge = self.data
        bg = UI["warn_card"] if state == "edit" else (UI["row_hi"] if self.hover else self.base_bg)
        self._paint_bg(bg)
        self.delete("d")
        imgs = []
        if not first:
            self.create_line(0, 0, w, 0, fill=UI["sep"], tags="d")
        d, x, cy, col = S(32), S(12), h / 2.0, S(44)
        imgs.append(app.key_chip(self, x, cy, key_text, key_color, bg, d, col, state))
        xr = w - S(8)
        self.coords(self._w_more, xr, cy)
        xr -= S(36)
        self.coords(self._w_edit, xr, cy)
        xr -= S(34) + S(8)
        if badge:
            text, bfill, bfg = BADGES[badge]
            f = app.fonts["badge"]
            bw, bh = f.measure(text) + S(14), S(19)
            imgs.append(app.img.rrect(bw, bh, S(6), bfill, bg))
            self.create_image(xr, cy, image=imgs[-1], anchor="e", tags="d")
            self.create_text(xr - bw / 2.0, cy, text=text, font=f, fill=bfg, tags="d")
            xr -= bw + S(10)
        tx = x + col + S(10)
        room = xr - tx
        ft, fs = app.fonts["body_s"], app.fonts["tiny"]
        tcol = UI["warn_text"] if state == "edit" else (UI["dim"] if state == "unset" else UI["text"])
        self.create_text(tx, cy - S(8), text=fit_text(ft, title, room), font=ft, anchor="w",
                         fill=tcol, tags="d")
        self.create_text(tx, cy + S(9), text=fit_text(fs, sub, room), font=fs, anchor="w",
                         fill=UI["warn_sub"] if state == "edit" else UI["muted"], tags="d")
        self._imgs = imgs


class ComboRow(_Row):
    """1 combo trong tab "Combo": tên, tóm tắt (số bước, thời gian, số vòng), phím chạy, F9,
    nút chạy/dừng. Bấm vào dòng: chọn combo để sửa ở khung bên dưới."""

    def __init__(self, master, app, sid):
        S = app.px
        self.sid = sid
        _Row.__init__(self, master, app, S(52), UI["card"])
        self.btn = RButton(self, app, icon="play", kind="play", height=S(34), bg=UI["card"],
                           icon_font=app.fonts["icon_s"], command=lambda: app.toggle_combo(sid))
        self.buttons = [self.btn]
        self._w_btn = self.create_window(0, 0, window=self.btn, anchor="e")

    def on_click(self):
        self.app.select_script(self.sid)

    def redraw(self):
        if self.data is None:
            return
        S, app = self.app.px, self.app
        w, h = self.size()
        first, selected, running, name, state_text, state_kind, summary, key, f9 = self.data
        bg = UI["sel"] if selected else (UI["row_hi"] if self.hover else self.base_bg)
        self._paint_bg(bg)
        self.btn.set_icon("stop" if running else "play", "stop" if running else "play")
        self.delete("d")
        self._keycaps = []
        imgs = []
        if selected:
            self.create_rectangle(0, 0, w - 1, h - 1, outline=UI["sel_line"], tags="d")
        elif not first:
            self.create_line(0, 0, w, 0, fill=UI["sep"], tags="d")
        cy = h / 2.0
        dx = S(16)
        if running:                                  # chấm xanh có quầng = đang chạy
            halo = _blend(bg, UI["on"], 0.25)
            imgs.append(app.img.disc(S(14), halo, bg))
            imgs.append(app.img.disc(S(8), UI["on"], halo))
        else:
            imgs.append(app.img.disc(S(8), bg, bg, UI["hollow"], max(1.0, S(1.5))))
        for im in imgs:
            self.create_image(dx, cy, image=im, tags="d")
        xr = w - S(8)
        self.coords(self._w_btn, xr, cy)
        xr -= S(34) + S(10)
        if f9:
            f = app.fonts["badge"]
            label = app.f9_label
            bw, bh = f.measure(label) + S(12), S(19)
            imgs.append(app.img.rrect(bw, bh, S(6), UI["f9_bg"], bg))
            self.create_image(xr, cy, image=imgs[-1], anchor="e", tags="d")
            self.create_text(xr - bw / 2.0, cy, text=label, font=f, fill=UI["f9_text"], tags="d")
            xr -= bw + S(8)
        if key:
            kx0, _ = draw_keycap(self, app, xr, cy, key, "e", bg=bg)
            xr = kx0 - S(10)
        tx = S(30)
        ft, fs = app.fonts["body_s"], app.fonts["tiny"]
        ty = cy - S(10)
        name_t = fit_text(ft, name, (xr - tx) * (0.62 if state_text else 1.0))
        self.create_text(tx, ty, text=name_t, font=ft, anchor="w", tags="d",
                         fill=UI["bright"] if selected else UI["text"])
        if state_text:
            sx = tx + ft.measure(name_t) + S(8)
            col = {"on": UI["on_text"], "warn": UI["warn_text"]}.get(state_kind, UI["muted"])
            self.create_text(sx, ty + S(1), text=fit_text(fs, state_text, xr - sx), font=fs,
                             fill=col, anchor="w", tags="d")
        self.create_text(tx, cy + S(10), text=fit_text(fs, summary or "chưa có điểm nào", xr - tx),
                         font=fs, fill=UI["muted"] if summary else UI["faint"], anchor="w",
                         tags="d")
        self._imgs = imgs


class StepRow(_Drawn):
    """1 bước trong khung sửa combo: điểm (số thứ tự trong hình tròn xanh, giống điểm trên màn
    hình), việc làm, thời gian chờ, ▲ ▼ ✕. Bấm vào dòng (trái hay phải): điểm đó nháy trên
    màn hình và mở menu đổi việc làm."""

    def __init__(self, master, app, index, first, last, st, desc, on_delay):
        S = app.px
        bg = UI["card2"]
        _Drawn.__init__(self, master, app, 1, S(38), bg, "hand2")
        self.index, self.num, self.first, self.last, self.desc = index, index + 1, first, last, desc
        self._blink_job = None
        self.var = tk.StringVar(master=app.root, value=str(st["delay"]))
        self.field = Field(self, app, self.var, S(78), S(28), "number", font=app.fonts["small"],
                           bg=bg, lo=0, hi=MAX_DELAY_MS, step=50)
        trace = self.var.trace_add("write", lambda *a: on_delay(st, self.var))
        self.bind("<Destroy>", lambda e: e.widget is self and self._on_destroy(trace), add="+")
        mk = lambda icon, cmd: RButton(self, app, icon=icon, kind="icon", height=S(28), bg=bg,
                                       icon_font=app.fonts["icon_xs"], command=cmd)
        self.btn_up = mk("up", lambda: app.move_step(index, -1))
        self.btn_down = mk("down", lambda: app.move_step(index, +1))
        self.btn_rm = mk("close", lambda: app.remove_step(index))
        self._items = [self.create_window(0, 0, window=b, anchor="e")
                       for b in (self.field, self.btn_up, self.btn_down, self.btn_rm)]
        if first:
            self.itemconfigure(self._items[1], state="hidden")
        if last:
            self.itemconfigure(self._items[2], state="hidden")
        self.bind("<Configure>", lambda e: self.redraw())
        for seq in ("<ButtonRelease-1>", "<ButtonRelease-3>"):
            self.bind(seq, self._on_click)

    def _on_destroy(self, trace):
        self.var.trace_remove("write", trace)
        if self._blink_job:
            self.after_cancel(self._blink_job)
            self._blink_job = None

    def _on_click(self, e):
        if 0 <= e.x < self.winfo_width() and 0 <= e.y < self.winfo_height():
            self.app.step_clicked(self.index, e.x_root, e.y_root)

    def blink(self):
        """Viền vàng một lúc: "đây là bước của điểm bạn vừa bấm"."""
        w, h = self.size()
        self.delete("hl")
        self.create_rectangle(1, 1, w - 2, h - 2, outline=UI["capture_line"],
                              width=max(1, self.app.px(2)), tags="hl")
        if self._blink_job:
            self.after_cancel(self._blink_job)
        self._blink_job = self.after(900, self._end_blink)

    def _end_blink(self):
        self._blink_job = None
        self.delete("hl")

    def redraw(self):
        S, app = self.app.px, self.app
        w, h = self.size()
        bg = self.cget("bg")
        cy = h / 2.0
        self.delete("d")
        if not self.first:
            self.create_line(0, 0, w, 0, fill=UI["line"], tags="d")
        fs = app.fonts["small"]
        xr = w - S(6)
        up, down, rm = self._items[1], self._items[2], self._items[3]
        self.coords(rm, xr, cy)
        xr -= S(30)
        if self.first or self.last:          # chỉ có 1 mũi tên: đặt cùng 1 cột cho thẳng hàng
            self.coords(down if self.first else up, xr, cy)
        else:
            self.coords(down, xr, cy)
            self.coords(up, xr - S(30), cy)
        xr -= S(60)
        xr -= S(6)
        self.create_text(xr, cy, text="ms", font=fs, fill=UI["muted"], anchor="e", tags="d")
        xr -= fs.measure("ms") + S(6)
        self.coords(self._items[0], xr, cy)
        xr -= S(78) + S(6)
        self.create_text(xr, cy, text="chờ", font=fs, fill=UI["muted"], anchor="e", tags="d")
        xr -= fs.measure("chờ") + S(10)
        x, d = S(10), S(26)
        num = str(self.num)
        self._img = app.img.disc(d, POINT_FILL, bg, POINT_RING, max(1.0, S(1.2)))
        self.create_image(x, cy, image=self._img, anchor="w", tags="d")
        self.create_text(x + d / 2.0, cy, text=num, font=app.chip_font(num, d), fill=POINT_TEXT,
                         tags="d")
        x += d + S(10)
        self.create_text(x, cy, text=fit_text(fs, self.desc, xr - x), font=fs, fill=UI["soft"],
                         anchor="w", tags="d")
        self.tag_raise("hl")


class _Dialog(object):
    """Khung chung của các hộp thoại tối màu (Nhập chữ, Nút phím): mở ra giữa cửa sổ chính,
    chặn cửa sổ chính tới khi bấm Xong / Huỷ. Lớp con viết ok() / cancel()."""

    def _make_top(self, app, title):
        S = app.px
        self.app, self.result = app, None
        top = self.top = tk.Toplevel(app.root)
        top.withdraw()
        top.title(title)
        top.configure(bg=UI["bg"])
        top.resizable(False, False)
        top.transient(app.root)
        top.protocol("WM_DELETE_WINDOW", self.cancel)
        body = tk.Frame(top, bg=UI["bg"], padx=S(18), pady=S(16))
        body.pack(fill="both", expand=True)
        return body

    def _make_buttons(self, body):
        """Hàng cuối: dòng báo lỗi (trái), Huỷ và Xong (phải)."""
        S, app = self.app.px, self.app
        btns = tk.Frame(body, bg=UI["bg"])
        btns.pack(fill="x", pady=(S(16), 0))
        self.btn_ok = RButton(btns, app, "Xong", kind="primary", height=S(38), width=S(104),
                              font=app.fonts["btn"], command=self.ok)
        self.btn_ok.pack(side="right")
        self.btn_cancel = RButton(btns, app, "Huỷ", kind="ghost", height=S(38), width=S(84),
                                  font=app.fonts["btn_s"], command=self.cancel)
        self.btn_cancel.pack(side="right", padx=(0, S(8)))
        self.lbl_err = _label(btns, app, "", "small", "err_text")
        self.lbl_err.pack(side="left")

    def _clear_err(self, *a):
        if self.lbl_err.winfo_exists():
            self.lbl_err.configure(text="")

    def _close(self):
        try:
            self.top.grab_release()
        except tk.TclError:
            pass
        if self.top.winfo_exists():
            self.top.destroy()

    def _present(self):
        """Hiện hộp giữa cửa sổ chính (thanh tiêu đề tối), giữ chuột / phím trong hộp."""
        app, top = self.app, self.top
        top.update_idletasks()
        w = top.winfo_reqwidth()
        x = app.root.winfo_rootx() + (app.root.winfo_width() - w) // 2
        y = app.root.winfo_rooty() + app.px(90)
        top.geometry("+%d+%d" % (max(0, x), max(0, y)))
        top.deiconify()
        try:
            app.api.dark_title_bar(app.api.toplevel_hwnd(top), UI["title"])
        except Exception:
            pass
        try:
            top.grab_set()
        except tk.TclError:
            pass
        top.lift()
        top.focus_force()                        # gõ / nhấn phím được ngay, không cần bấm vào

    def _wait(self, wait):
        if wait:
            self.app.root.wait_window(self.top)
        return self.result


class TextDialog(_Dialog):
    """Hộp "Nhập chữ": chữ cần nhập + tuỳ chọn (click trước, Enter sau, dán hay gõ).
    show() trả về {"text", "click", "enter", "method"} hoặc None nếu bấm Huỷ."""

    METHOD_NOTES = (
        "Dán (Ctrl+V): nhanh, giữ đúng chữ có dấu. Chữ cũ trong clipboard được trả lại sau đó.",
        "Gõ từng chữ: như gõ bàn phím – dùng khi game không cho dán. Nên tắt Unikey (chữ E).")

    def __init__(self, app, title, settings=None, for_point=False):
        S = app.px
        st = {"text": "", "enter": False, "click": False, "method": "paste"}
        st.update(settings or {})
        body = self._make_top(app, title)
        _label(body, app, "Chữ cần nhập", "body_s").pack(anchor="w")
        _label(body, app, ("Tới bước này thì chữ được dán vào ô đang gõ (vd ô chat)." if for_point
                           else "Nhấn phím của nút thì chữ này được dán vào ô đang gõ (vd ô chat)."),
               "small", "muted", wraplength=S(390), justify="left").pack(anchor="w",
                                                                         pady=(S(2), S(8)))
        self.var_text = tk.StringVar(master=app.root, value=st["text"])
        self.fld = Field(body, app, self.var_text, S(396), S(36), "text")
        self.fld.pack(fill="x")
        for seq in ("<Return>", "<KP_Enter>"):        # Enter trong ô = Xong (không lan ra ngoài)
            self.fld.entry.bind(seq, lambda e: self.ok() or "break")
        self.fld.entry.bind("<Escape>", lambda e: self.cancel() or "break")
        card = Card(body, app, "card", "line", radius=12, pad=12)
        card.pack(fill="x", pady=(S(14), 0))
        cb = card.body
        self.var_click = tk.BooleanVar(master=app.root, value=bool(st["click"]))
        self.var_enter = tk.BooleanVar(master=app.root, value=bool(st["enter"]))
        self.switches = []
        for var, text in ((self.var_click, "Click vào %s trước khi nhập" % (
                               "điểm này" if for_point else "chỗ đặt nút")),
                          (self.var_enter, "Nhấn Enter sau khi nhập (vd gửi tin nhắn)")):
            r = tk.Frame(cb, bg=UI["card"])
            r.pack(fill="x", pady=(0, S(10)))
            sw = Switch(r, app, var)
            sw.pack(side="left")
            self.switches.append(sw)
            _label(r, app, text).pack(side="left", padx=(S(10), 0))
        _label(cb, app, "Cách nhập", "small", "text2").pack(anchor="w")
        self.method = TabBar(cb, app, ("Dán (Ctrl+V)", "Gõ từng chữ"), self._on_method)
        self.method.pack(fill="x", pady=(S(6), 0))
        self.lbl_note = _label(cb, app, "", "tiny", "muted", wraplength=S(370), justify="left",
                               anchor="nw", height=2)
        self.lbl_note.pack(fill="x", pady=(S(6), 0))
        self._on_method(0 if st["method"] == "paste" else 1)
        self._make_buttons(body)
        for var in (self.var_text, self.var_enter):          # gõ lại / bật Enter = bỏ báo lỗi
            var.trace_add("write", self._clear_err)
        self.top.bind("<Escape>", lambda e: self.cancel())

    def _on_method(self, i):
        self.method.select(i)
        self.lbl_note.configure(text=self.METHOD_NOTES[i])

    def settings(self):
        return {"text": self.var_text.get()[:MAX_TEXT_LEN], "click": bool(self.var_click.get()),
                "enter": bool(self.var_enter.get()),
                "method": "paste" if self.method.index == 0 else "type"}

    def ok(self):
        st = self.settings()
        if not st["text"].strip() and not st["enter"]:
            self.lbl_err.configure(text="Hãy gõ chữ cần nhập.")
            self.fld.entry.focus_set()
            return
        self.result = st
        self._close()

    def cancel(self):
        self.result = None
        self._close()

    def show(self, wait=True):
        self._present()
        self.fld.entry.focus_set()
        self.fld.entry.icursor("end")
        return self._wait(wait)


class KeyBox(_Drawn):
    """Ô lớn trong hộp "Nút phím": phím đã chọn (vd Backspace) như 1 phím bàn phím, hoặc
    nền vàng "Nhấn phím muốn bấm…" khi đang chờ. Bấm vào ô -> command() (chờ phím khác)."""

    def __init__(self, master, app, width, command):
        S = app.px
        self.vk, self.waiting, self.command = None, False, command
        _Drawn.__init__(self, master, app, width, S(88), None, "hand2")
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<ButtonRelease-1>", lambda e: self.command())
        self.redraw()

    def set(self, vk, waiting):
        if (vk, waiting) != (self.vk, self.waiting):
            self.vk, self.waiting = vk, waiting
            self.redraw()

    def redraw(self):
        app = self.app
        S = app.px
        w, h = self.size()
        bg = self.cget("bg")
        if self.waiting:
            fill, line, lw = UI["warn_card"], UI["capture_line"], max(1.0, S(1.5))
        else:
            fill, line, lw = UI["field"], UI["field_line"], 1.0
        self.delete("all")
        self._keycaps = []
        self._img = app.img.rrect(w, h, S(12), fill, bg, line, lw)
        self.create_image(0, 0, image=self._img, anchor="nw")
        cy = h / 2.0 - S(9)
        if self.waiting:
            self.create_text(w / 2.0, cy, text="Nhấn phím muốn bấm…", font=app.fonts["btn"],
                             fill=UI["warn_text"])
            hint = ("Esc: thôi chờ" if self.vk is None else
                    "Esc: giữ phím cũ (%s)" % vk_long_name(self.vk, app.api))
            hcol = UI["warn_sub"]
        elif self.vk is not None:
            name = vk_long_name(self.vk, app.api)
            font = app.fit_font(name, w - S(70), app._font(17, "bold"))
            draw_keycap(self, app, w / 2.0, cy, name, "center", font=font, height=S(38),
                        min_w=S(60), bg=fill)
            hint, hcol = "Bấm vào đây rồi nhấn phím khác để đổi", UI["muted"]
        else:
            self.create_text(w / 2.0, cy, text="Chưa chọn phím", font=app.fonts["btn"],
                             fill=UI["muted"])
            hint, hcol = "Bấm vào đây rồi nhấn phím muốn bấm", UI["muted"]
        self.create_text(w / 2.0, h - S(15), text=hint, font=app.fonts["tiny"], fill=hcol)


class KeyDialog(_Dialog):
    """Hộp "Nút phím": chọn phím KeyClick sẽ bấm khi nhấn phím của nút (vd A -> Backspace).
    Chọn bằng cách nhấn phím đó (bắt qua hook bàn phím nên phím nào cũng được, kể cả Win,
    Alt, PrtSc) hoặc bấm 1 nút chọn nhanh. show() trả về mã phím, hoặc None nếu bấm Huỷ."""

    QUICK = ((0x08, "Backspace"), (0x0D, "Enter"), (0x1B, "Esc"), (0x20, "Space"),
             (0x09, "Tab"), (0x2E, "Delete"), (0x26, "↑"), (0x28, "↓"), (0x25, "←"),
             (0x27, "→"), (0xA0, "Shift"), (0xA2, "Ctrl"), (0xA4, "Alt"))

    def __init__(self, app, title, current=None, for_point=False):
        S = app.px
        self.vk, self.waiting = valid_vk(current), False
        self.token = ("outkey", id(self))
        body = self._make_top(app, title)
        width = S(396)
        _label(body, app, "Phím sẽ được bấm", "body_s").pack(anchor="w")
        _label(body, app, ("Tới bước này thì KeyClick bấm phím này (vd Backspace)." if for_point
                           else "Nhấn phím của nút (vd A) thì KeyClick bấm phím này (vd Backspace)."),
               "small", "muted", wraplength=width, justify="left").pack(anchor="w",
                                                                         pady=(S(2), S(8)))
        self.box = KeyBox(body, app, width, self.start_wait)
        self.box.pack(fill="x")
        _label(body, app, "Chọn nhanh", "small", "text2").pack(anchor="w", pady=(S(12), S(6)))
        self.chips = {}
        self._make_chips(body, width)
        note = Card(body, app, "card", "line", radius=10, pad=10)
        note.pack(fill="x", pady=(S(14), 0))
        _label(note.body, app, ("Bước này nhấn rồi thả phím (như gõ 1 lần). " if for_point else
                                "Giữ phím của nút = giữ phím này, thả ra là thả – như bàn phím "
                                "thật. ") + "Phím do KeyClick bấm không kích hoạt các nút khác.",
               "tiny", "muted",
               wraplength=width - S(24), justify="left").pack(anchor="w")
        self._make_buttons(body)
        for seq in ("<Return>", "<KP_Enter>"):        # khi KHÔNG chờ phím: Enter = Xong
            self.top.bind(seq, lambda e: self.ok())
        self.top.bind("<Escape>", lambda e: self.cancel())
        self._update()

    def _make_chips(self, parent, width):
        """Các nút chọn nhanh, tự xuống hàng cho vừa bề rộng."""
        S, app = self.app.px, self.app
        font = app.fonts["btn_xs"]
        row, used = None, 0
        for vk, text in self.QUICK:
            w = int(font.measure(text) + S(20))
            if row is None or used + S(6) + w > width:
                first = row is None
                row = tk.Frame(parent, bg=UI["bg"])
                row.pack(fill="x", pady=(0 if first else S(6), 0))
                used = 0
            b = RButton(row, app, text, kind="secondary", height=S(30), width=w, font=font,
                        command=lambda v=vk: self.pick(v))
            b.pack(side="left", padx=(S(6) if used else 0, 0))
            used += w + (S(6) if used else 0)
            self.chips[vk] = b

    def _update(self):
        self.box.set(self.vk, self.waiting)
        for vk, b in self.chips.items():
            b.set_icon(None, "primary" if vk == self.vk and not self.waiting else "secondary")

    def start_wait(self):
        """Chờ người dùng nhấn phím (KeyClick bắt qua hook: Enter, Tab, Win… đều được)."""
        self.waiting = True
        self.app.engine.capture_id = self.token
        self._clear_err()
        self._update()

    def stop_wait(self):
        if self.app.engine.capture_id == self.token:
            self.app.engine.capture_id = None
        if self.waiting:
            self.waiting = False
            if self.top.winfo_exists():
                self._update()

    def on_captured(self, vk):
        """Phím vừa nhấn trong lúc chờ (Esc = thôi chờ, giữ phím cũ)."""
        if not self.waiting or not self.top.winfo_exists():
            return
        self.waiting = False
        if vk != VK_ESCAPE:
            self.vk = vk
        self._update()

    def pick(self, vk):
        self.stop_wait()
        self.vk = vk
        self._clear_err()
        self._update()

    def ok(self):
        self.stop_wait()
        if self.vk is None:
            self.lbl_err.configure(text="Hãy chọn phím sẽ được bấm.")
            return
        self.result = self.vk
        self._close()

    def cancel(self):
        self.stop_wait()
        self.result = None
        self._close()

    def _close(self):
        if self.app._key_dialog is self:
            self.app._key_dialog = None
        _Dialog._close(self)

    def show(self, wait=True):
        self.app._key_dialog = self
        self._present()
        if self.vk is None:                      # nút mới: chờ phím luôn, khỏi phải bấm ô
            self.start_wait()
        return self._wait(wait)


UI_FAMILIES = ("Segoe UI", "Inter", "DejaVu Sans")      # font chữ: Windows / máy thử
SEMIBOLD_FAMILIES = ("Segoe UI Semibold", "Inter SemiBold")
TAB_NAMES = ("Nút bấm", "Combo", "Cài đặt")
SIDE_NAMES = {"left": "trái", "right": "phải", "middle": "giữa"}


class App(object):
    """Cửa sổ điều khiển chính: thẻ trạng thái + 3 tab (Nút bấm, Combo, Cài đặt)."""

    def __init__(self, api, config_path):
        self.api = api
        self.config_path = config_path
        self.cfg = dict(DEFAULT_CFG)
        self.profile_dir = ""
        self._start_buttons = []
        self._start_scripts = None      # danh sách combo đọc từ file (None = file kiểu cũ)
        self._start_script_sel = 0
        self._legacy_loops, self._legacy_forever = 1, False
        self._window_pos = None
        self._read_config()

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title(WINDOW_TITLE if api.is_windows else WINDOW_TITLE + " (chế độ thử)")
        self.root.report_callback_exception = self._tk_error
        # tỉ lệ phóng to của Windows (100%, 125%, 150%…); làm tròn để cỡ cửa sổ không lẻ 1 pixel
        self.scale = max(1.0, round(self.root.winfo_fpixels("1i") / 96.0, 2))
        self._setup_fonts()
        self.img = _ImageCache(self.root)

        self.ui_q = queue.Queue()
        self.engine = ClickEngine(api, self.ui_q, self.cfg)
        self.f9_label = vk_label(self.engine.script_vk)
        self.circles = {}               # id -> Circle (giữ thứ tự tạo)
        self.editing = None             # nút đang chờ gán phím
        self.enabled = False            # luôn khởi động ở trạng thái TẮT cho an toàn
        self.hook = None
        self.hook_error = None
        self._save_job = None
        self._edit_job = None
        self._blink_job = None
        self._poll_job = None
        self._top_job = None
        self._fg_job = None
        self._menu_refs = None
        self._is_admin = bool(api.is_windows and api.is_admin())
        self._last_fg_pid = None        # tiến trình của cửa sổ đang được chọn (lần xem trước)
        self._elev_warned = set()       # đã cảnh báo "cửa sổ chạy quyền Admin" cho các pid này
        # các combo: {id, name, key, loops, forever, steps, f9}; mỗi bước là 1
        # ĐIỂM của riêng combo đó: {id, x, y, mouse, mode, x2, y2, swipe_ms, text, enter,
        # click_first, method, out, delay} – không có phím, đánh số 1..n theo thứ tự bước.
        self.scripts = []
        self.sel_sid = None             # combo đang chọn (đang sửa) trong tab Combo
        self.points = {}                # id điểm -> ComboPoint đang hiện (sửa / đang chạy)
        self._picking = None            # PickLayer khi đang chọn điểm trên màn hình
        self._linger = {}               # combo vừa chạy xong: id -> hẹn giờ ẩn điểm (để kịp
        #                                 thấy cú bấm cuối)
        self._lit = {}                  # combo đang chạy: id -> id điểm của bước đang làm
        self._lit_dirty = False         # _lit vừa đổi, chưa vẽ lại các điểm
        self._point_sid = {}            # id điểm đang hiện -> id combo của nó
        self._hold_points = False       # đang bắt đầu chạy combo: chưa tạo điểm mới
        self.running = {}               # các combo đang chạy (cùng lúc được): id -> số vòng
        self.progress = {}              # id -> đang chạy vòng thứ mấy
        self._quiet_start = set()       # combo vừa chạy theo nhóm F9: không báo từng cái
        self._script_capture = None     # combo đang chờ gán phím chạy
        self._key_dialog = None         # hộp Nút phím đang mở (chờ phím sẽ bấm)
        self._sid_seq = 0
        self._steps_sig = None
        self._script_vars = []          # ô "chờ … ms" của các bước (để thử nghiệm)
        self._loading_script_ui = False
        self._turbo_ui = False
        self.tab = 0
        self.circle_rows = {}           # id nút -> dòng trong tab Nút bấm
        self.combo_rows = {}            # id combo -> dòng trong tab Combo
        self.step_rows = []

        self.var_return = tk.BooleanVar(master=self.root, value=bool(self.cfg["return_cursor"]))
        self.var_show_play = tk.BooleanVar(master=self.root, value=bool(self.cfg["show_play"]))
        self._build_ui()
        # Biết lúc nào con trỏ đang ở 1 ô nhập của KeyClick để không click khi gõ chữ/số.
        self.root.bind_all("<FocusIn>", self._on_focus_change, add="+")
        self.root.bind_all("<FocusOut>", self._on_focus_change, add="+")
        self.root.bind_all("<ButtonPress-1>", self._on_any_click, add="+")
        for seq in ("<Return>", "<KP_Enter>", "<Escape>"):   # Enter / Esc trong ô nhập = gõ xong
            self.root.bind_class("Entry", seq, self._on_typing_done, add="+")
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
        self._dark_title_bar()
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

    def icon(self, name):
        glyph, fallback = ICONS[name]
        return glyph if self.icon_font_ok else fallback

    def _font(self, size, weight="normal"):
        key = (size, weight)
        f = self._fcache.get(key)
        if f is None:
            f = tkfont.Font(root=self.root, family=self.ui_family, size=-max(1, self.px(size)),
                            weight=weight)
            self._fcache[key] = f
        return f

    def chip_font(self, text, d, grow=False):
        """Chữ đậm to nhất vừa trong hình tròn đường kính d (grow: hình kéo dài theo chữ)."""
        top = max(6, int(round((d / self.scale) * 0.31 + 4.2)))
        if grow:
            return self._font(top, "bold")
        for size in range(top, 5, -1):
            f = self._font(size, "bold")
            if f.measure(text) <= d - self.px(5):
                return f
        return self._font(6, "bold")

    def key_chip(self, cv, x0, cy, label, color, bg, d, col_w, state="key"):
        """Vẽ ô tên phím lên canvas cv, giữa cột rộng col_w bắt đầu ở x0: hình tròn trắng
        (tên 1–2 ký tự), viên thuốc (tên dài: Space, Num9, F12…), nét đứt "?" (chưa gán phím)
        hoặc vàng (đang chờ phím). Trả về ảnh nền (để giữ tham chiếu)."""
        S = self.px
        ring_w = max(1.0, S(1.5) if d >= S(30) else S(1.2))
        cx = x0 + col_w / 2.0
        if state == "unset":
            img, tcol, font = self.img.dashed(d, UI["hollow"], bg, ring_w), UI["text2"], None
        elif state == "edit":
            img = self.img.disc(d, UI["edit_chip"], bg, UI["edit_ring"], ring_w)
            tcol, font = UI["capture_text"], None
        elif len(label) <= 2:
            img, tcol, font = self.img.disc(d, UI["chip"], bg, UI["chip_ring"], ring_w), color, None
        else:
            h = d - S(4)
            img = self.img.rrect(col_w, h, h / 2.0, UI["chip"], bg, UI["chip_ring"], ring_w)
            tcol = color
            font = self.fit_font(label, col_w - S(8), self.chip_font(label, d, grow=True))
        cv.create_image(cx, cy, image=img, tags="d")
        cv.create_text(cx, cy, text=label, fill=tcol, font=font or self.chip_font(label, d),
                       tags="d")
        return img

    def fit_font(self, text, width, start):
        """Font đậm to nhất (không to hơn `start`) để chữ vừa `width` pixel."""
        size = int(round(-start.cget("size") / self.scale))
        for sz in range(size, 5, -1):
            f = self._font(sz, "bold")
            if f.measure(text) <= width:
                return f
        return self._font(6, "bold")

    @staticmethod
    def _typing_mode(w):
        """Ô nhập của KeyClick: "text" (ô Tên), "number" (ô ms, ô Lặp, ô turbo) hoặc None.
        Ô bị khoá không tính là ô nhập."""
        if isinstance(w, Field):
            w = w.entry
        if not isinstance(w, tk.Entry):
            return None
        try:
            if str(w.cget("state")) != "normal":
                return None
        except tk.TclError:
            return None
        return getattr(w, "kc_kind", "text")

    def _focus_widget(self):
        try:
            return self.root.focus_get()
        except Exception:
            return None

    def _on_focus_change(self, e=None):
        """Con trỏ đang ở ô nhập chữ/số của KeyClick? (ô Tên, ô ms, ô Lặp…)"""
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
            try:
                w.selection_clear()
            except (tk.TclError, AttributeError):
                pass
            self.root.focus_set()
        self.engine.typing = None

    def _on_typing_done(self, e=None):
        if self.engine.typing is not None:
            self._stop_typing()
            self._update_status()

    def _on_any_click(self, e):
        """Bấm vào chỗ khác trong KeyClick (nút, công tắc, tab, nút tròn…) = thôi gõ chữ."""
        w = e.widget
        if not isinstance(w, tk.Misc):
            return
        if self._typing_mode(w) is None and self.engine.typing is not None:
            self._stop_typing()
            self._update_status()

    # ------------------------------------------------------------------ giao diện
    def _setup_fonts(self):
        fams = set(tkfont.families(self.root))
        self.ui_family = next((f for f in UI_FAMILIES if f in fams), "Helvetica")
        semi = next((f for f in SEMIBOLD_FAMILIES if f in fams), None)
        self._fcache = {}

        def F(size, weight="normal", family=None):
            return tkfont.Font(root=self.root, family=family or self.ui_family,
                               size=-max(1, self.px(size)), weight=weight)

        def SEMI(size):
            return F(size, family=semi) if semi else F(size, "bold")

        self.fonts = {
            "title": F(15, "bold"), "body": F(13), "body_s": SEMI(13), "small": F(12.5),
            "tiny": F(11.5), "label": F(11, "bold"), "btn": SEMI(14), "btn_s": F(13),
            "btn_xs": SEMI(12.5), "key": F(11, "bold"), "badge": F(10.5, "bold"),
        }
        icon_family = next((f for f in ICON_FAMILIES if f in fams), None)
        self.icon_font_ok = icon_family is not None
        if icon_family:
            self.fonts.update(icon=F(15, family=icon_family), icon_s=F(13, family=icon_family),
                              icon_xs=F(11, family=icon_family))
        else:
            self.fonts.update(icon=F(15, "bold"), icon_s=F(13, "bold"), icon_xs=F(11, "bold"))
        self.f_toast = tkfont.Font(root=self.root, family=self.ui_family, size=13, weight="bold")
        self.f_hint = tkfont.Font(root=self.root, family=self.ui_family, size=10, weight="bold")
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont"):
            try:
                tkfont.nametofont(name).configure(family=self.ui_family, size=-self.px(13))
            except tk.TclError:
                pass

    def _menu(self):
        return tk.Menu(self.root, tearoff=0, bg=UI["btn"], fg=UI["text"], bd=0, relief="flat",
                       activebackground=UI["accent"], activeforeground="#ffffff",
                       disabledforeground=UI["faint"], selectcolor=UI["text"],
                       activeborderwidth=0, font=self.fonts["body"])

    def _build_ui(self):
        S = self.px
        root = self.root
        root.configure(bg=UI["bg"])
        root.resizable(False, False)
        body = tk.Frame(root, bg=UI["bg"], padx=S(16), pady=S(14))
        body.pack(fill="both", expand=True)
        self.status = StatusCard(body, self, self._on_status_switch, vk_label(self.engine.toggle_vk))
        self.status.pack(fill="x")
        self.tabbar = TabBar(body, self, TAB_NAMES, self.show_tab)
        self.tabbar.pack(fill="x", pady=(S(12), 0))
        self.msgbar = MessageBar(body, self)
        self.msgbar.pack(side="bottom", fill="x", pady=(S(12), 0))
        content = tk.Frame(body, bg=UI["bg"])
        content.pack(fill="both", expand=True, pady=(S(12), 0))
        # màn hình thấp (cửa sổ phải thấp hơn cỡ chuẩn): danh sách combo chỉ cao 2 dòng
        self._short = self._window_size()[1] < S(WIN_H) - S(60)
        self._cards = []
        self.tab_areas = []
        for build in (self._build_buttons_tab, self._build_combo_tab, self._build_settings_tab):
            area = ScrollArea(content, self, UI["bg"], fit=True)
            build(area.inner)
            self.tab_areas.append(area)
        self._settle_layout()
        self.show_tab(0)
        wheel = lambda e: ScrollArea.wheel(self.root, e)
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.root.bind_all(seq, wheel, add="+")

    def _settle_layout(self):
        """Tính cỡ tối thiểu của các thẻ (thẻ trong trước, thẻ ngoài sau) để biết tab nào
        cần cuộn khi màn hình thấp."""
        self.root.update_idletasks()
        for card in reversed(self._cards):
            card.fit()
            self.root.update_idletasks()
        for area in self.tab_areas:
            area.layout()

    def show_tab(self, i):
        for j, area in enumerate(self.tab_areas):
            if j != i:
                area.pack_forget()
        self.tab_areas[i].pack(fill="both", expand=True)
        self.tab = i
        self.tabbar.select(i)
        self.msgbar.set_tip(self._tab_tip(i))
        if i == 1 and self.sel_sid in self.combo_rows:    # thấy được combo đang chọn
            row = self.combo_rows[self.sel_sid]
            self.root.after_idle(lambda: row.winfo_exists() and self.combo_area.see(row))
        self._sync_points()

    def _tab_tip(self, i):
        if i == 0:
            return ("Kéo nút để di chuyển · kéo mép hoặc lăn chuột để đổi cỡ · Ctrl + kéo để "
                    "nhân bản · chuột phải vào nút để chọn kiểu click")
        if i == 1:
            return ("%s: chạy cùng lúc các combo có nhãn %s · phím riêng: chạy / dừng riêng combo "
                    "đó · Esc: dừng hết" % (self.f9_label, self.f9_label))
        return "KeyClick %s · Hướng dẫn chi tiết trong file HUONG_DAN.txt" % APP_VERSION

    def _grid_buttons(self, parent, specs, weights, height, font, icon_font=None, gap=8):
        """Các nút nằm ngang, chia bề rộng theo tỉ lệ `weights` (khe giữa các nút là cột riêng,
        nên các nút cùng tỉ lệ rộng đúng bằng nhau)."""
        S = self.px
        out = []
        for i, wgt in enumerate(weights):
            parent.columnconfigure(2 * i, weight=wgt, uniform="g%d" % id(parent))
            if i:
                parent.columnconfigure(2 * i - 1, weight=0, minsize=S(gap))
        for i, (text, icon, kind, cmd) in enumerate(specs):
            b = RButton(parent, self, text, icon=icon, kind=kind, height=height, width=S(10),
                        font=font, icon_font=icon_font, command=cmd)
            b.grid(row=0, column=2 * i, sticky="ew")
            out.append(b)
        return out

    def _fit_label(self, label, text):
        """Nhãn 1 dòng: chữ dài quá thì cắt bằng "…" (nhãn không đòi rộng thêm)."""
        label._full = text
        font = tkfont.nametofont(str(label.cget("font")))
        w = label.winfo_width()
        label.configure(text=fit_text(font, text, w if w > 1 else self.px(200)))
        if not getattr(label, "_fit_bound", False):
            label._fit_bound = True
            label.bind("<Configure>", lambda e: label.configure(
                text=fit_text(font, label._full, e.width)), add="+")

    # ---- tab Nút bấm ----
    def _build_buttons_tab(self, tab):
        S = self.px
        bg = UI["bg"]
        row = tk.Frame(tab, bg=bg)
        row.pack(fill="x")
        self.btn_add, self.btn_add_swipe, self.btn_add_text, self.btn_add_key = self._grid_buttons(
            row, (("Thêm nút", "add", "primary", self.add_circle),
                  ("Nút vuốt", "swipe", "secondary", lambda: self.add_circle(mode="swipe")),
                  ("Nhập chữ", "keyboard", "secondary", self.add_text_circle),
                  ("Nút phím", "remap", "secondary", self.add_key_circle)),
            (1, 1, 1, 1), S(44), self.fonts["body_s"], self.fonts["icon_s"], gap=6)

        hdr = tk.Frame(tab, bg=bg)
        hdr.pack(fill="x", pady=(S(14), S(8)))
        _section_label(hdr, self, "NÚT TRÊN MÀN HÌNH").pack(side="left")
        self.lbl_count = _label(hdr, self, "", "small", "muted")
        self.lbl_count.pack(side="right")

        prof = tk.Frame(tab, bg=bg)
        prof.pack(side="bottom", fill="x", pady=(S(14), 0))
        _section_label(prof, self, "BỘ PHÍM (MỖI GAME 1 BỘ)").pack(anchor="w", pady=(0, S(8)))
        btns = tk.Frame(prof, bg=bg)
        btns.pack(fill="x")
        self.btn_open, self.btn_save, self.btn_clear = self._grid_buttons(
            btns, (("Mở bộ phím…", "folder", "ghost", self.open_profile),
                   ("Lưu…", "save", "ghost", self.save_profile),
                   ("Xoá hết", "delete", "danger", self.clear_all)),
            (13, 10, 10), S(38), self.fonts["btn_s"], self.fonts["icon_s"])

        card = Card(tab, self, "card", "line", radius=12, pad=0, fill_mode=True)
        card.pack(fill="both", expand=True)
        self.btn_area = ScrollArea(card.body, self, UI["card"], min_height=S(48) * 3)
        self.btn_area.pack(fill="both", expand=True)
        self.lbl_empty = _label(self.btn_area.inner, self,
                                "Chưa có nút nào.\nBấm “Thêm nút” để tạo nút tròn đầu tiên.",
                                "small", "muted", justify="center")
        card.after_idle(card.fit)

    # ---- tab Combo ----
    def _build_combo_tab(self, tab):
        S = self.px
        bg, cbg = UI["bg"], UI["card"]
        hdr = tk.Frame(tab, bg=bg)
        hdr.pack(fill="x", pady=(0, S(8)))
        self.lbl_combo_count = _section_label(hdr, self, "COMBO")
        self.lbl_combo_count.pack(side="left")
        self.btn_new_script = RButton(hdr, self, "Combo mới", icon="add", kind="secondary",
                                      height=S(30), font=self.fonts["btn_xs"],
                                      icon_font=self.fonts["icon_xs"], command=self.new_script)
        self.btn_new_script.pack(side="right")

        card = Card(tab, self, "card", "line", radius=12, pad=0, fill_mode=True)
        card.pack(fill="x")
        self.combo_area = ScrollArea(card.body, self, cbg, min_height=S(52) * (2 if self._short else 3))
        self.combo_area.pack(fill="both", expand=True)
        card.after_idle(card.fit)

        hdr2 = tk.Frame(tab, bg=bg)
        hdr2.pack(fill="x", pady=(S(14), S(8)))
        _section_label(hdr2, self, "SỬA COMBO ĐANG CHỌN").pack(side="left")
        self.btn_del_script = RButton(hdr2, self, "Xoá combo", icon="delete", kind="link_danger",
                                      height=S(22), font=self.fonts["small"],
                                      icon_font=self.fonts["icon_xs"], command=self.delete_script)
        self.btn_del_script.pack(side="right")

        run = tk.Frame(tab, bg=bg)
        run.pack(side="bottom", fill="x", pady=(S(12), 0))
        self.btn_run, self.btn_stop = self._grid_buttons(
            run, (("Chạy các combo %s" % self.f9_label, "play", "primary", self.run_script),
                  ("Dừng hết", "stop", "danger_fill", self.stop_script)),
            (15, 10), S(42), self.fonts["btn"], self.fonts["icon_s"], gap=10)

        ed = Card(tab, self, "card", "line", radius=12, pad=12, fill_mode=True)
        ed.pack(fill="both", expand=True)
        b = ed.body
        r1 = tk.Frame(b, bg=cbg)
        r1.pack(fill="x")
        _label(r1, self, "Tên", "small", "text2").pack(side="left")
        self.btn_skey_clear = RButton(r1, self, "Bỏ", kind="outline", height=S(32), width=S(44),
                                      font=self.fonts["small"], command=self.clear_script_key)
        self.btn_skey_clear.pack(side="right")
        self.btn_skey = RButton(r1, self, "Gán", kind="outline", height=S(32), width=S(48),
                                font=self.fonts["small"], command=self.begin_script_key)
        self.btn_skey.pack(side="right", padx=(0, S(6)))
        self.key_cap = KeyCap(r1, self, "–", height=S(26), min_w=S(50))
        self.key_cap.pack(side="right", padx=(0, S(8)))
        _label(r1, self, "Phím", "small", "text2").pack(side="right", padx=(S(10), S(6)))
        self.var_sname = tk.StringVar(master=self.root)
        self.fld_sname = Field(r1, self, self.var_sname, S(80), S(32), "text")
        self.fld_sname.pack(side="left", fill="x", expand=True, padx=(S(8), 0))
        self.ent_sname = self.fld_sname.entry
        self.var_sname.trace_add("write", lambda *a: self._on_script_name())

        r4 = tk.Frame(b, bg=cbg)
        r4.pack(side="bottom", fill="x", pady=(S(10), 0))
        self.var_f9 = tk.BooleanVar(master=self.root, value=True)
        self.sw_f9 = Switch(r4, self, self.var_f9, command=self._on_f9)
        self.sw_f9.pack(side="left")
        _label(r4, self, "Chạy khi nhấn %s" % self.f9_label, "small", "soft").pack(
            side="left", padx=(S(8), S(16)))

        r3 = tk.Frame(b, bg=cbg)
        r3.pack(side="bottom", fill="x", pady=(S(10), 0))
        _label(r3, self, "Lặp", "small", "text2").pack(side="left")
        self.var_loops = tk.StringVar(master=self.root, value="1")
        self.fld_loops = Field(r3, self, self.var_loops, S(72), S(30), "number",
                               font=self.fonts["small"], lo=1, hi=999999)
        self.fld_loops.pack(side="left", padx=(S(8), S(6)))
        _label(r3, self, "lần", "small", "text2").pack(side="left")
        self.var_forever = tk.BooleanVar(master=self.root, value=False)
        self.sw_forever = Switch(r3, self, self.var_forever, command=self._on_forever)
        self.sw_forever.pack(side="left", padx=(S(18), S(8)))
        _label(r3, self, "Lặp mãi", "small", "soft").pack(side="left")
        self.var_loops.trace_add("write", lambda *a: self._on_loops())

        box = Card(b, self, "card2", "line", radius=10, pad=0, fill_mode=True)
        box.pack(fill="both", expand=True, pady=(S(10), 0))
        foot = tk.Frame(box.body, bg=UI["card2"])
        foot.pack(side="bottom", fill="x")
        tk.Frame(foot, bg=UI["line"], height=1).pack(fill="x")
        # "Thêm điểm": click lên màn hình vào các chỗ cần bấm, mỗi click là 1 bước
        self.btn_add_point = RButton(foot, self, "Thêm điểm", icon="add", kind="link",
                                     height=S(30), font=self.fonts["btn_xs"],
                                     icon_font=self.fonts["icon_xs"], command=self.begin_pick,
                                     bg=UI["card2"])
        self.btn_add_point.pack(side="left", padx=(S(4), 0), pady=S(3))
        tip = _label(foot, self, "", "tiny", "muted", anchor="e", width=1)
        tip.pack(side="right", fill="x", expand=True, padx=(S(8), S(10)))
        self._fit_label(tip, "bấm vào 1 bước để đổi việc làm")
        self.step_area = ScrollArea(box.body, self, UI["card2"], min_height=S(38) * 2)
        self.step_area.pack(fill="both", expand=True)
        self.lbl_no_steps = _label(self.step_area.inner, self,
                                   "Chưa có điểm nào. Bấm “Thêm điểm” rồi click lên màn hình\n"
                                   "vào các chỗ cần bấm (theo thứ tự).", "small", "muted",
                                   justify="center")
        box.after_idle(box.fit)
        ed.after_idle(ed.fit)

    # ---- tab Cài đặt ----
    def _build_settings_tab(self, tab):
        S = self.px
        cbg = UI["card"]

        def section(title, fill="card", border="line", first=False):
            _section_label(tab, self, title).pack(anchor="w", pady=(0 if first else S(14), S(8)))
            card = Card(tab, self, fill, border, radius=12, pad=14)
            card.pack(fill="x")
            return card.body

        b = section("NÚT & ĐIỂM TRÊN MÀN HÌNH", first=True)
        r1 = tk.Frame(b, bg=cbg)
        r1.pack(fill="x")
        self.preview = tk.Canvas(r1, width=S(64), height=S(52), bg=cbg, highlightthickness=0, bd=0)
        self.preview.pack(side="right", padx=(S(12), 0))
        left = tk.Frame(r1, bg=cbg)
        left.pack(side="left", fill="x", expand=True)
        top = tk.Frame(left, bg=cbg)
        top.pack(fill="x")
        _label(top, self, "Độ đậm nền nút").pack(side="left")
        pct = int(round(self.cfg["bg_alpha"] * 100))
        self.lbl_bg = _label(top, self, "%d%%" % pct, "body_s", "text2")
        self.lbl_bg.pack(side="right")
        self.var_bg = tk.IntVar(master=self.root, value=pct)
        self.slider_bg = Slider(left, self, self.var_bg, 5, 100, command=self._on_bg_alpha)
        self.slider_bg.pack(fill="x", pady=(S(6), 0))
        r2 = tk.Frame(b, bg=cbg)
        r2.pack(fill="x", pady=(S(12), 0))
        # "Hiện nút & điểm khi F8 bật": tắt = đang chơi thì ẩn hết (phím vẫn click, combo vẫn chạy)
        self.sw_show_play = Switch(r2, self, self.var_show_play, command=self._on_cb_show_play)
        self.sw_show_play.pack(side="left")
        _label(r2, self, "Hiện nút & điểm khi F8 bật").pack(side="left", padx=(S(10), 0))
        _label(r2, self, "tắt = F8 bật thì ẩn hết", "tiny", "muted").pack(side="right")
        self._draw_preview()

        b = section("KHI CLICK")
        r = tk.Frame(b, bg=cbg)
        r.pack(fill="x")
        self.sw_return = Switch(r, self, self.var_return, command=self._on_cb_return)
        self.sw_return.pack(side="left")
        _label(r, self, "Trả chuột về vị trí cũ sau khi click").pack(side="left", padx=(S(10), 0))
        r = tk.Frame(b, bg=cbg)
        r.pack(fill="x", pady=(S(12), 0))
        # ô ghi chú rộng cố định (đủ cho "ms = 33 lần/giây") -> chữ đổi mà hàng không xô lệch
        fs = self.fonts["small"]
        note = tk.Frame(r, bg=cbg, width=fs.measure("ms = 33,3 lần/giây") + S(2), height=S(30))
        note.pack(side="right")
        note.pack_propagate(False)
        self.lbl_turbo_note = _label(note, self, "", "small", "muted", anchor="w")
        self.lbl_turbo_note.pack(fill="both", expand=True)
        self.var_turbo = tk.StringVar(master=self.root, value=str(int(self.cfg["turbo_interval_ms"])))
        self.fld_turbo = Field(r, self, self.var_turbo, S(64), S(30), "number", lo=30, hi=5000,
                               step=10)
        self.fld_turbo.pack(side="right", padx=(S(8), S(8)))
        _label(r, self, "Tốc độ turbo").pack(side="left")
        lbl = _label(r, self, "", "small", "muted", anchor="w", width=1)
        lbl.pack(side="left", fill="x", expand=True, padx=(S(6), 0))
        self._fit_label(lbl, "(giữ phím = click liên tục)")
        self.var_turbo.trace_add("write", lambda *a: self._on_turbo_field())
        self._update_turbo_note()

        b = section("PHÍM TẮT")
        hk = tk.Canvas(b, height=S(24), width=1, bg=cbg, highlightthickness=0, bd=0)
        hk.pack(fill="x")
        x = 0
        f = self.fonts["small"]
        for key, text in ((vk_label(self.engine.toggle_vk), "bật / tắt"),
                          (self.f9_label, "chạy combo"), ("Esc", "dừng combo")):
            x0, x1 = draw_keycap(hk, self, x, S(12), key, "w", bg=cbg)
            hk.create_text(x1 + S(6), S(12), text=text, font=f, fill=UI["dim"], anchor="w")
            x = x1 + S(6) + f.measure(text) + S(18)

        if self.api.is_windows:
            self._build_admin(section("QUYỀN ADMIN", "admin_card", "admin_line"))

    def _build_admin(self, b):
        S = self.px
        abg = UI["admin_card"]
        r = tk.Frame(b, bg=abg)
        r.pack(fill="x")
        tk.Label(r, text=self.icon("check" if self._is_admin else "shield"), font=self.fonts["icon"],
                 fg=UI["on_text"] if self._is_admin else UI["admin_icon"], bg=abg, bd=0).pack(
            side="left", anchor="n", padx=(0, S(10)))
        text = ("KeyClick đang chạy với quyền Admin: dùng được cả với game / giả lập chạy Admin."
                if self._is_admin else
                "Game hoặc giả lập chạy bằng quyền Admin thì KeyClick cũng phải chạy Admin, nếu "
                "không Windows sẽ chặn phím và click.")
        self.lbl_admin = _label(r, self, text, "small", "admin_text", wraplength=S(370),
                                justify="left")
        self.lbl_admin.pack(side="left", fill="x", expand=True, anchor="w")
        r2 = tk.Frame(b, bg=abg)
        r2.pack(fill="x", pady=(S(12), 0))
        self.btn_admin = None
        if not self._is_admin:
            self.btn_admin = RButton(r2, self, "Chạy lại bằng quyền Admin", kind="admin",
                                     height=S(36), font=self.fonts["btn_xs"],
                                     command=self.relaunch_admin)
            self.btn_admin.pack(side="left", padx=(0, S(12)))
        self.var_admin = tk.BooleanVar(master=self.root, value=bool(self.cfg["run_as_admin"]))
        self.sw_admin = Switch(r2, self, self.var_admin, command=self._on_cb_admin,
                               on_color="#ca8a04", off_color="admin_track", knob_off="admin_knob")
        self.sw_admin.pack(side="left")
        _label(r2, self, "Luôn chạy Admin", "body", "admin_text").pack(side="left", padx=(S(10), 0))

    def _draw_preview(self):
        """Ô xem trước bên cạnh thanh "Độ đậm nền nút": 1 nút trên nền game giả."""
        S = self.px
        cv = self.preview
        w, h, d = S(64), S(52), S(34)
        a = self.cfg["bg_alpha"]
        game = UI["sample"]
        fill = _blend(game, THEME["fill"], a)
        ring = _blend(game, THEME["ring"], min(1.0, 0.1 + 0.45 * a))
        self._pv = (self.img.rrect(w, h, S(9), game, UI["card"]),
                    self.img.disc(d, fill, game, ring, max(1.0, S(1.5))))
        cv.delete("all")
        cv.create_image(0, 0, image=self._pv[0], anchor="nw")
        cv.create_image(w / 2.0, h / 2.0, image=self._pv[1])
        cv.create_text(w / 2.0, h / 2.0, text="A", font=self.chip_font("A", d),
                       fill=THEME["text_left"])

    # ------------------------------------------------------------------ trạng thái
    def _update_status(self):
        if self.hook_error:
            style, title, sub = "err", "KHÔNG BẮT ĐƯỢC PHÍM", self.hook_error
        elif self.editing is not None:
            style, title, sub = "warn", "ĐANG CHỜ PHÍM", "Nhấn 1 phím để gán cho nút · Esc: huỷ"
        elif self._script_capture is not None:
            style, title, sub = ("warn", "ĐANG CHỜ PHÍM",
                                 "Nhấn 1 phím làm phím chạy combo · Esc: huỷ")
        elif self.enabled and self.engine.typing == "text":
            style, title, sub = ("warn", "ĐANG GÕ CHỮ",
                                 "Phím tạm không click · bấm ra ngoài ô để tiếp tục")
        elif self.enabled and self.engine.typing == "number":
            style, title, sub = "warn", "ĐANG SỬA SỐ", "Phím số để gõ, phím khác vẫn click"
        elif self.enabled and len(self.running) > 1:
            style, title = "on", "ĐANG BẬT"
            sub = "%d combo đang chạy · Esc để dừng hết" % len(self.running)
        elif self.enabled and self.running:
            style, title = "on", "ĐANG BẬT"
            sub = "“%s” đang chạy · Esc để dừng" % self._script_name(next(iter(self.running)))
        elif self.enabled:
            style, title, sub = "on", "ĐANG BẬT", "Nhấn phím để click · chuột đi xuyên qua nút"
        else:
            style, title, sub = "off", "ĐANG TẮT", "Kéo / sửa nút tròn trên màn hình"
        self.status.set(style, title, sub, self.enabled, disabled=bool(self.hook_error))

    def notify(self, text, ms=5000, kind="warn"):
        self.msgbar.show(text, kind, ms, tag="notice")

    def _script_msg(self, text, kind="info", ms=6000):
        if text:
            self.msgbar.show(text, kind, ms, tag="script")
        else:
            self.msgbar.clear("script")

    # ------------------------------------------------------------------ tab Nút bấm
    def _circle_texts(self, c):
        """(dòng chính, dòng phụ) mô tả 1 nút tròn trong danh sách."""
        if self.editing is c:
            return "Đang chờ phím…", "Nhấn 1 phím để gán · Esc: huỷ"
        if c.mode == "text":
            return self._text_texts(c)
        if c.mode == "key":
            return self._key_texts(c)
        if c.key is None:
            return "Chưa gán phím", "Bấm bút chì rồi nhấn 1 phím"
        k = vk_label(c.key, self.api)
        side = SIDE_NAMES.get(c.button, "trái")
        extra = "" if c.button == "left" else " " + side
        if c.mode == "hold":
            return "Giữ chuột" + extra, "Giữ %s = giữ chuột (kéo, ngắm skill)" % k
        if c.mode == "turbo":
            cps = int(round(1000.0 / max(30, self.cfg["turbo_interval_ms"])))
            return "Click%s liên tục" % extra, "Giữ %s = %d click mỗi giây" % (k, cps)
        if c.mode == "swipe":
            title = "Vuốt " + self._swipe_dir(c) + ("" if c.button == "left" else " (chuột %s)" % side)
            return title, "Nhấn %s = vuốt %d ms tới chấm vàng" % (k, c.swipe_ms)
        return "Click chuột " + side, "Nhấn %s = click%s 1 lần" % (k, extra)

    def _text_texts(self, c):
        """Nút Nhập chữ: "Nhập “huy”" + "Nhấn T = click vào nút → dán chữ → Enter"."""
        title = ("Nhập “%s”" % " ⏎ ".join(c.text.splitlines())) if c.text else "Nhấn Enter"
        if c.key is None:
            return title, "Chưa gán phím · bấm bút chì rồi nhấn 1 phím"
        steps = []
        if c.text_click:
            steps.append("click vào nút")
        if c.text:
            steps.append("dán chữ" if c.text_method == "paste" else "gõ chữ")
        if c.text_enter:
            steps.append("Enter")
        return title, "Nhấn %s = %s" % (vk_label(c.key, self.api), " → ".join(steps))

    def _key_texts(self, c):
        """Nút Phím: "Bấm phím Backspace" + "Nhấn A = bấm Backspace"."""
        name = vk_long_name(c.out, self.api) if c.out is not None else "?"
        title = "Bấm phím %s" % name
        if c.key is None:
            return title, "Chưa gán phím · bấm bút chì rồi nhấn 1 phím"
        return title, "Nhấn / giữ %s = nhấn / giữ %s" % (vk_label(c.key, self.api), name)

    @staticmethod
    def _swipe_dir(c):
        if c.x2 is None or c.y2 is None or (c.x2, c.y2) == (c.cx, c.cy):
            return "tới chấm vàng"
        ang = math.degrees(math.atan2(c.cy - c.y2, c.x2 - c.cx)) % 360
        names = ("sang phải", "chéo lên phải", "lên", "chéo lên trái", "sang trái",
                 "chéo xuống trái", "xuống", "chéo xuống phải")
        return names[int((ang + 22.5) // 45) % 8]

    def _circle_row_data(self, c, first):
        if self.editing is c:
            state, key_text = "edit", "…"
        elif c.key is None:
            state, key_text = "unset", "?"
        else:
            state, key_text = "key", vk_label(c.key, self.api)
        title, sub = self._circle_texts(c)
        badge = c.mode if c.mode in BADGES else None
        return (first, state, key_text, _label_color(c), title,
                sub, badge)

    def _refresh_buttons_tab(self):
        n = len(self.circles)
        keyed = sum(1 for c in self.circles.values() if c.key is not None)
        self.lbl_count.configure(text=("%d nút · %d đã gán phím" % (n, keyed)) if n else "")
        for cid in list(self.circle_rows):
            if cid not in self.circles:
                self.circle_rows.pop(cid).destroy()
        new = None
        for cid in self.circles:
            if cid not in self.circle_rows:
                new = self.circle_rows[cid] = CircleRow(self.btn_area.inner, self, cid)
                new.pack(fill="x")
        if n and self.lbl_empty.winfo_manager():
            self.lbl_empty.pack_forget()
        elif not n and not self.lbl_empty.winfo_manager():
            self.lbl_empty.pack(fill="x", pady=self.px(30))
        for i, c in enumerate(self.circles.values()):
            self.circle_rows[c.id].update_data(self._circle_row_data(c, i == 0))
        if new is not None:
            self.root.after_idle(lambda r=new: r.winfo_exists() and self.btn_area.see(r))

    def edit_circle(self, cid):
        """Nút bút chì: gán phím cho nút (bấm lần nữa = huỷ)."""
        c = self.circles.get(cid)
        if c is None:
            return
        if self.editing is c:
            self.end_edit()
        else:
            self.begin_edit(c)

    def locate_circle(self, cid):
        """Bấm vào 1 dòng: nút tròn tương ứng nháy sáng 2 lần trên màn hình."""
        c = self.circles.get(cid)
        if c is None:
            return
        if not c._visible():
            self.msgbar.show("F8 đang bật nên các nút đang ẩn – bật lại ở tab Cài đặt › “Hiện nút "
                             "& điểm khi F8 bật”.", "info", 5000, tag="hidden")
            return
        self._raise_circle(c)
        c.flash(UI["accent"], 260)
        if self._blink_job:
            self.root.after_cancel(self._blink_job)
        self._blink_job = self.root.after(420, lambda: self._blink_again(c))

    def _blink_again(self, c):
        self._blink_job = None
        if c.id in self.circles:
            c.flash(UI["accent"], 260)

    def circle_menu_from_list(self, cid, x, y):
        c = self.circles.get(cid)
        if c is not None:
            self.show_circle_menu(c, x, y, from_list=True)

    # ------------------------------------------------------------------ tab Combo
    #  Nhiều combo, mỗi combo có: tên, phím chạy (không bắt buộc), các bước, số lần lặp,
    #  "Chạy khi nhấn F9". Các combo chạy CÙNG LÚC được.
    #  Mỗi bước là 1 ĐIỂM của riêng combo đó – không có phím, không nằm ở tab Nút bấm: bấm
    #  "Thêm điểm" rồi click lên màn hình. Điểm đánh số 1..n theo thứ tự bước. Bấm vào dòng
    #  bước (hoặc chuột phải vào điểm) để đổi việc làm: click / giữ / turbo / vuốt / nhập chữ /
    #  bấm phím.
    @staticmethod
    def _step_short(p):
        """Việc làm của 1 bước, ngắn gọn (dòng bước trong khung sửa combo)."""
        side = SIDE_NAMES.get(p["mouse"], "trái")
        mode = p["mode"]
        if mode == "hold":
            return "Giữ chuột %s" % side
        if mode == "turbo":
            return "Click %s liên tục" % side
        if mode == "swipe":
            return "Vuốt %d ms" % p["swipe_ms"] + ("" if p["mouse"] == "left" else " (%s)" % side)
        if mode == "text":
            return ("Nhập “%s”" % " ⏎ ".join(p["text"].splitlines())) if p["text"] else "Nhấn Enter"
        if mode == "key":
            return "Bấm %s" % vk_long_name(p["out"])
        return "Click %s" % side

    # ---- dữ liệu combo ----
    def _new_script(self, name=None, key=None, steps=None, loops=1, forever=False, f9=True):
        """f9: chạy khi nhấn F9 — F9 chạy CÙNG LÚC mọi combo bật công tắc này (mặc định bật)."""
        self._sid_seq += 1
        if not name:
            used = set(sc["name"] for sc in self.scripts)
            n = 1
            while "Combo %d" % n in used:
                n += 1
            name = "Combo %d" % n
        return {"id": self._sid_seq, "name": name, "key": key,
                "loops": int(loops), "forever": bool(forever), "steps": list(steps or []),
                "f9": bool(f9)}

    def _new_point(self, x, y, delay=DEFAULT_STEP_DELAY_MS, **props):
        """1 điểm (1 bước) mới: mặc định click chuột trái rồi chờ 200 ms sang bước sau."""
        p = {"id": next(Circle._ids), "x": int(x), "y": int(y), "mouse": "left", "mode": "click",
             "x2": None, "y2": None, "swipe_ms": DEFAULT_SWIPE_MS, "text": "", "enter": False,
             "click_first": False, "method": "paste", "out": None, "delay": int(delay)}
        p.update(props)
        return self._fix_point(p)

    def default_swipe_target(self, x, y):
        """Điểm đích mặc định của nút / điểm vuốt: bên phải (sát mép phải thì bên trái)."""
        vx, vy, vw, vh = self.vscreen()
        d = self.px(160)
        return self.clamp_point(x + d if x + d < vx + vw - self.px(20) else x - d, y)

    def _fix_point(self, p):
        """Điểm phải nằm trong màn hình; điểm vuốt chưa có đích thì đặt đích bên phải."""
        p["x"], p["y"] = self.clamp_point(p["x"], p["y"])
        if p["x2"] is not None and p["y2"] is not None:
            p["x2"], p["y2"] = self.clamp_point(p["x2"], p["y2"])
        elif p["mode"] == "swipe":
            p["x2"], p["y2"] = self.default_swipe_target(p["x"], p["y"])
        return p

    @staticmethod
    def _blank_script(sc):
        """Combo trống: chưa có bước nào, chưa có phím chạy."""
        return not sc["steps"] and sc["key"] is None

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

    @staticmethod
    def _script_targets(sc):
        return [(action_target(p), p["delay"]) for p in sc["steps"]]

    def _sync_scripts(self):
        """Báo cho engine phím nào chạy combo nào (gọi lại mỗi khi combo thay đổi)."""
        m = {}
        for sc in self.scripts:
            if sc["key"] is not None and sc["steps"]:
                m[sc["key"]] = (sc["id"], self._script_targets(sc), self._script_loops(sc))
        self.engine.set_script_keys(m)

    def _scripts_data(self):
        """Combo để lưu vào file: mỗi bước là 1 điểm (vị trí + việc làm + thời gian chờ)."""
        out = []
        for sc in self.scripts:
            steps = []
            for p in sc["steps"]:
                d = action_to_dict(p)
                d["delay"] = p["delay"]
                steps.append(d)
            out.append({"name": sc["name"], "key": sc["key"], "loops": sc["loops"],
                        "forever": sc["forever"], "f9": sc["f9"], "steps": steps})
        return out

    def _install_scripts(self, raw, created, buttons, sel=0, legacy_loops=1, legacy_forever=False):
        """Dựng lại danh sách combo sau khi đã tạo các nút (created: theo thứ tự trong file).
        Bước của file cũ trỏ tới nút tròn -> thành điểm riêng, đúng vị trí và việc làm của nút."""
        self.scripts = []
        self.progress = {}
        actions = [c.action() for c in created]
        parsed = parse_scripts(raw, actions)
        if parsed is None:
            parsed = []
            if created:                # file của bản cũ (≤ 1.3): 1 combo gồm các nút có phím
                steps = [dict(a, delay=b.get("delay", DEFAULT_DELAY_MS))
                         for a, b, c in zip(actions, buttons, created)
                         if c.key is not None and b.get("in_script", True)]
                parsed.append({"name": "Combo 1", "key": None, "loops": legacy_loops,
                               "forever": legacy_forever, "steps": steps, "f9": True})
        used = (set(c.key for c in created if c.key is not None)
                | {self.engine.toggle_vk, self.engine.script_vk, VK_ESCAPE})
        for p in parsed:
            key = p["key"] if p["key"] not in used else None
            if key is not None:
                used.add(key)
            steps = [self._fix_point(dict(st, id=next(Circle._ids))) for st in p["steps"]]
            self.scripts.append(self._new_script(p["name"] or None, key, steps, p["loops"],
                                                 p["forever"], p["f9"]))
        if not self.scripts:
            self.scripts.append(self._new_script())
        if not (isinstance(sel, int) and not isinstance(sel, bool) and 0 <= sel < len(self.scripts)):
            sel = 0
        self.sel_sid = self.scripts[sel]["id"]
        self._steps_sig = None

    def _script_changed(self):
        self._sync_scripts()
        self._refresh_combo_tab()
        self._schedule_save()

    # ---- hiển thị tab Combo ----
    def _refresh_combo_tab(self, force=False):
        if self._sel_script() is None and self.scripts:
            self.sel_sid = self.scripts[0]["id"]
        n = len(self.scripts)
        self.tabbar.set_badge(1, str(n))
        self.lbl_combo_count.configure(text="COMBO · %d" % n)
        self._refresh_combo_rows()
        sc = self._sel_script()
        sig = None
        if sc is not None:
            sig = (sc["id"], tuple(self._step_sig(p) for p in sc["steps"]))
        if force or sig != self._steps_sig:
            self._steps_sig = sig
            self._load_script_fields(sc)
            self._rebuild_step_rows(sc)
        self._update_skey_label()
        self._update_script_buttons()
        self._sync_points()

    @staticmethod
    def _step_sig(p):
        """Phần hiện ở dòng bước: đổi thì vẽ lại các dòng (dời điểm / sửa ms thì không cần)."""
        return (p["id"], p["mouse"], p["mode"], p["swipe_ms"], p["text"], p["out"])

    def _combo_row_data(self, sc, first):
        steps = sc["steps"]
        looping = sc["forever"] or sc["loops"] != 1
        summary = ""
        if steps:
            delays = [p["delay"] for p in steps]
            per_loop = sum(delays if looping else delays[:-1])
            parts = ["%d bước" % len(steps)]
            if per_loop:
                parts.append(fmt_ms(per_loop) + ("/vòng" if looping else ""))
            if looping:
                parts.append("lặp mãi" if sc["forever"] else "×%d" % sc["loops"])
            summary = " · ".join(parts)
        if sc["id"] in self.running:
            loops = self.running[sc["id"]]
            if loops == 1:
                state = ("đang chạy", "on")
            else:
                state = ("vòng %d / %s" % (self.progress.get(sc["id"], 1),
                                           "∞" if loops is None else loops), "on")
        elif not steps:
            state = ("", "muted")
        elif not sc["f9"] and sc["key"] is None:
            state = ("chỉ chạy bằng nút ▶", "warn")
        elif not sc["f9"]:
            state = ("không chạy theo %s" % self.f9_label, "muted")
        else:
            state = ("", "muted")
        key = vk_label(sc["key"], self.api) if sc["key"] is not None else None
        return (first, sc["id"] == self.sel_sid, sc["id"] in self.running,
                sc["name"] or "(không tên)", state[0], state[1], summary, key, sc["f9"])

    def _refresh_combo_rows(self):
        for sid in list(self.combo_rows):
            if self._script(sid) is None:
                self.combo_rows.pop(sid).destroy()
        new = None
        for sc in self.scripts:
            if sc["id"] not in self.combo_rows:
                new = self.combo_rows[sc["id"]] = ComboRow(self.combo_area.inner, self, sc["id"])
                new.pack(fill="x")
        for i, sc in enumerate(self.scripts):
            self.combo_rows[sc["id"]].update_data(self._combo_row_data(sc, i == 0))
        if new is not None:
            self.root.after_idle(lambda r=new: r.winfo_exists() and self.combo_area.see(r))

    def _update_combo_row(self, sid):
        sc, row = self._script(sid), self.combo_rows.get(sid)
        if sc is not None and row is not None:
            row.update_data(self._combo_row_data(sc, self.scripts.index(sc) == 0))

    def _load_script_fields(self, sc):
        self._loading_script_ui = True
        try:
            if sc is None:
                return
            if self.var_sname.get().strip()[:40].rstrip() != sc["name"]:
                self.var_sname.set(sc["name"])
            if self._loops_value() != sc["loops"]:
                self.var_loops.set(str(sc["loops"]))
            self.var_forever.set(bool(sc["forever"]))
            self.fld_loops.state(["disabled"] if sc["forever"] else ["!disabled"])
            self.var_f9.set(bool(sc["f9"]))
        finally:
            self._loading_script_ui = False

    def _update_skey_label(self):
        sc = self._sel_script()
        has_key = sc is not None and sc["key"] is not None
        if self._script_capture is not None:
            self.key_cap.set("?", UI["capture"], UI["capture_line"], UI["capture_text"])
            self.btn_skey.set_text("Huỷ")
        elif has_key:
            self.key_cap.set(vk_label(sc["key"], self.api))
            self.btn_skey.set_text("Đổi")
        else:
            self.key_cap.set("–", fg=UI["muted"])
            self.btn_skey.set_text("Gán")
        self.btn_skey_clear.state(["!disabled"] if (has_key and self._script_capture is None)
                                  else ["disabled"])

    def _rebuild_step_rows(self, sc):
        for r in self.step_rows:
            r.destroy()
        self.step_rows = []
        self._script_vars = []
        steps = sc["steps"] if sc else []
        if not steps:
            if not self.lbl_no_steps.winfo_manager():
                self.lbl_no_steps.pack(fill="x", pady=self.px(16))
            return
        if self.lbl_no_steps.winfo_manager():
            self.lbl_no_steps.pack_forget()
        for i, p in enumerate(steps):
            row = StepRow(self.step_area.inner, self, i, i == 0, i == len(steps) - 1, p,
                          self._step_short(p), self._on_delay)
            row.pack(fill="x")
            self.step_rows.append(row)
        self._script_vars = [r.var for r in self.step_rows]

    # ---- điểm của combo trên màn hình ----
    def point_size(self):
        return max(28, int(round(self.default_size() * 0.75)))

    def _point_scripts(self):
        """Các combo cần hiện điểm trên màn hình lúc này:
          - F8 tắt (đang sửa): combo đang chọn – ở tab nào cũng hiện;
          - F8 bật: công tắc "Hiện nút & điểm khi F8 bật" (tab Cài đặt) bật thì hiện combo đang
            chọn + các combo đang chạy (hoặc vừa chạy xong); tắt thì ẩn hết."""
        sel = self._sel_script()
        if not self.enabled:
            return [sel] if sel is not None else []
        if not self.cfg["show_play"]:
            return []
        return [sc for sc in self.scripts
                if sc is sel or sc["id"] in self.running or sc["id"] in self._linger]

    def _sync_points(self):
        """Cho các điểm trên màn hình khớp với các combo cần hiện (thêm / bớt / đánh số lại;
        vừa bật / tắt phím tắt thì đổi kiểu hiện: sửa = rõ, kéo được; chạy = nhạt, chuột đi
        xuyên qua, điểm của bước đang làm sáng xanh lá)."""
        if not self.enabled:
            self._lit.clear()                   # đang sửa: không điểm nào "đang chạy"
        scripts = self._point_scripts()
        self._point_sid = dict((p["id"], sc["id"]) for sc in scripts for p in sc["steps"])
        shown = [(n, p) for sc in scripts for n, p in enumerate(sc["steps"], 1)]
        keep = set(p["id"] for n, p in shown)
        for pid in list(self.points):
            if pid not in keep:
                self.points.pop(pid).destroy()
        lit = set(self._lit.values())
        self._lit_dirty = False
        for n, p in shown:
            cp = self.points.get(p["id"])
            if cp is None:
                if self._hold_points:           # combo sắp chạy: tạo sau khi nó bắt đầu bấm
                    continue
                cp = self.points[p["id"]] = ComboPoint(self, p, n)
            else:
                cp.sync(p, n)
                if cp.play != self.enabled:
                    cp.apply_mode()
            cp.set_lit(p["id"] in lit)

    def _light_point(self, pid):
        """Combo vừa bắt đầu 1 bước (engine báo): điểm của bước đó sẽ sáng xanh lá, điểm của
        bước trước trong cùng combo thôi sáng. Vẽ gom 1 lần sau mỗi đợt sự kiện (_apply_lit):
        combo rất nhanh / nhiều combo cùng chạy cũng không làm giật."""
        sid = self._point_sid.get(pid)
        if sid is None or not self.enabled:
            return
        self._lit[sid] = pid
        self._lit_dirty = True

    def _apply_lit(self):
        self._lit_dirty = False
        lit = set(self._lit.values())
        for pid, cp in self.points.items():
            cp.set_lit(pid in lit)

    def _linger_points(self, sid, ms=700):
        """Combo vừa chạy xong: giữ các điểm thêm một chút (cho kịp thấy cú bấm cuối) rồi ẩn."""
        self._cancel_linger(sid)
        self._linger[sid] = self.root.after(ms, lambda: self._end_linger(sid))

    def _cancel_linger(self, sid):
        job = self._linger.pop(sid, None)
        if job:
            try:
                self.root.after_cancel(job)
            except Exception:
                pass

    def _end_linger(self, sid):
        self._linger.pop(sid, None)
        if sid not in self.running:
            self._lit.pop(sid, None)
        self._sync_points()

    def _find_step(self, p):
        """(combo, vị trí trong combo) của điểm p, hoặc (None, -1) nếu điểm đã bị xoá."""
        for sc in self.scripts:
            for i, q in enumerate(sc["steps"]):
                if q is p:
                    return sc, i
        return None, -1

    def add_point(self, x, y, **props):
        """Thêm 1 điểm (1 bước) vào cuối combo đang chọn, ở vị trí màn hình (x, y)."""
        sc = self._sel_script()
        if sc is None:
            return None
        p = self._new_point(x, y, **props)
        sc["steps"].append(p)
        self._script_changed()
        if self.step_rows:
            self.root.after_idle(lambda r=self.step_rows[-1]: r.winfo_exists()
                                 and self.step_area.see(r))
        return p

    def remove_point(self, p):
        sc, i = self._find_step(p)
        if sc is not None:
            self.remove_step(i, sc)

    def point_moved(self, p):
        """Điểm vừa được kéo sang chỗ khác (hoặc kéo chấm vàng của điểm vuốt)."""
        if self._find_step(p)[0] is not None:
            self._sync_scripts()
            self._schedule_save()

    def point_clicked(self, p):
        """Bấm (không kéo) vào 1 điểm trên màn hình: dòng bước của nó sáng lên."""
        sc, i = self._find_step(p)
        if sc is not None and sc["id"] == self.sel_sid and i < len(self.step_rows):
            row = self.step_rows[i]
            row.blink()
            self.step_area.see(row)

    def step_clicked(self, i, x, y):
        """Bấm vào 1 dòng bước: điểm đó nháy trên màn hình + mở menu đổi việc làm."""
        sc = self._sel_script()
        if sc is None or not 0 <= i < len(sc["steps"]):
            return
        p = sc["steps"][i]
        cp = self.points.get(p["id"])
        if cp is not None:
            self._raise_circle(cp)
            cp.flash(THEME["caret"], 450)
        self.show_point_menu(p, x, y, from_list=True)

    def set_point_prop(self, p, prop, value):
        """Đổi 1 thông số của điểm (chuột, việc làm, thời gian vuốt)."""
        if self._find_step(p)[0] is None:
            return
        if prop == "mode" and value != p["mode"]:
            if value == "text":
                self.edit_point_text(p)        # hỏi chữ cần nhập trước (Huỷ = giữ như cũ)
                return
            if value == "key":
                self.edit_point_key(p)         # hỏi phím sẽ bấm trước (Huỷ = giữ như cũ)
                return
        p[prop] = value
        if prop == "mode":
            self._fix_point(p)                 # vuốt: đặt sẵn chấm vàng ở bên phải
        self._script_changed()

    def edit_point_text(self, p):
        """Điểm này nhập chữ (hoặc sửa chữ). False = Huỷ."""
        if self._find_step(p)[0] is None:
            return False
        settings = None
        if p["mode"] == "text" or p["text"]:
            settings = {"text": p["text"], "enter": p["enter"], "click": p["click_first"],
                        "method": p["method"]}
        st = self.ask_text("Sửa chữ cần nhập" if p["mode"] == "text" else "Điểm này: nhập chữ",
                           settings, for_point=True)
        if st is None or self._find_step(p)[0] is None:
            return False
        p.update(mode="text", text=st["text"], enter=st["enter"], click_first=st["click"],
                 method=st["method"])
        self._script_changed()
        return True

    def edit_point_key(self, p):
        """Điểm này bấm 1 phím (hoặc đổi phím). False = Huỷ."""
        if self._find_step(p)[0] is None:
            return False
        vk = self.ask_key("Đổi phím sẽ bấm" if p["mode"] == "key" else "Điểm này: bấm phím",
                          p["out"], for_point=True)
        if vk is None or self._find_step(p)[0] is None:
            return False
        p.update(mode="key", out=vk)
        self._script_changed()
        return True

    def _speed_menus(self, m, later, swipe_ms, swipe_cmd, swipe_on):
        """2 menu con dùng chung cho nút tròn và điểm combo: tốc độ turbo, thời gian vuốt."""
        vt = tk.IntVar(master=self.root, value=int(self.cfg["turbo_interval_ms"]))
        sub = tk.Menu(m, tearoff=0, bg=UI["btn"], fg=UI["text"], activebackground=UI["accent"],
                      activeforeground="#ffffff", selectcolor=UI["text"], font=self.fonts["body"])
        for cps in (5, 10, 15, 20, 30):
            ms = int(round(1000.0 / cps))
            sub.add_radiobutton(label="%d lần/giây" % cps, value=ms, variable=vt,
                                command=later(self.set_turbo_interval, ms))
        m.add_cascade(label="Tốc độ turbo", menu=sub)
        vs = tk.IntVar(master=self.root, value=swipe_ms)
        sub2 = tk.Menu(m, tearoff=0, bg=UI["btn"], fg=UI["text"], activebackground=UI["accent"],
                       activeforeground="#ffffff", selectcolor=UI["text"], font=self.fonts["body"])
        for ms in (100, 200, 300, 500, 800, 1200):
            sub2.add_radiobutton(label="%d ms%s" % (ms, "  (nhanh)" if ms == 100 else ""),
                                 value=ms, variable=vs, command=later(swipe_cmd, ms))
        m.add_cascade(label="Thời gian vuốt", menu=sub2, state="normal" if swipe_on else "disabled")
        return (sub, sub2, vt, vs)

    def show_point_menu(self, p, x, y, from_list=False):
        """Menu của 1 điểm combo: chuột phải vào điểm trên màn hình, hoặc bấm vào dòng bước."""
        sc, i = self._find_step(p)
        if sc is None:
            return
        m = self._menu()
        vb = tk.StringVar(master=self.root, value=p["mouse"])
        vm = tk.StringVar(master=self.root, value=p["mode"])
        later = lambda fn, *a: (lambda: self.root.after_idle(fn, *a))   # sau khi menu đóng
        m.add_command(label="Điểm %d  ·  %s" % (i + 1, fit_chars(self._step_short(p), 34)),
                      state="disabled")
        m.add_separator()
        for val, text in (("left", "Chuột trái"), ("right", "Chuột phải"), ("middle", "Chuột giữa")):
            m.add_radiobutton(label=text, value=val, variable=vb,
                              command=later(self.set_point_prop, p, "mouse", val),
                              state="disabled" if p["mode"] == "key" else "normal")
        m.add_separator()
        for val, text in (("click", "Click 1 lần"),
                          ("hold", "Giữ chuột suốt thời gian chờ"),
                          ("turbo", "Click liên tục suốt thời gian chờ (turbo)"),
                          ("swipe", "Vuốt (từ điểm tới chấm vàng)"),
                          ("text", "Nhập chữ (dán chữ có sẵn)…"),
                          ("key", "Bấm phím (vd Backspace)…")):
            m.add_radiobutton(label=text, value=val, variable=vm,
                              command=later(self.set_point_prop, p, "mode", val))
        subs = self._speed_menus(m, later, p["swipe_ms"],
                                 lambda ms: self.set_point_prop(p, "swipe_ms", ms),
                                 p["mode"] == "swipe")
        m.add_command(label="Sửa chữ cần nhập…", command=later(self.edit_point_text, p),
                      state="normal" if p["mode"] == "text" else "disabled")
        m.add_command(label="Đổi phím sẽ bấm…   (đang là: %s)" % (
                          vk_long_name(p["out"], self.api) if p["out"] is not None else "chưa có"),
                      command=later(self.edit_point_key, p),
                      state="normal" if p["mode"] == "key" else "disabled")
        m.add_separator()
        m.add_command(label="Xoá điểm này", command=later(self.remove_point, p))
        self._menu_refs = (m, vb, vm) + subs
        cp = self.points.get(p["id"])
        if not from_list and cp is not None:
            try:
                self.api.force_foreground(cp.hwnd)    # để menu tự đóng khi bấm ra ngoài
            except Exception:
                pass
        try:
            m.tk_popup(x, y)
        finally:
            m.grab_release()
            if cp is not None and p["id"] in self.points:
                self._raise_circle(cp)

    # ---- chọn điểm bằng cách click lên màn hình ----
    def begin_pick(self):
        """Nút "Thêm điểm": phủ màn hình 1 lớp mờ; click vào đâu thì thêm 1 điểm (1 bước) ở
        đó. Cửa sổ KeyClick tạm ẩn để click được cả chỗ nó đang che."""
        sc = self._sel_script()
        if sc is None or self._picking is not None:
            return
        if self.enabled:
            self.set_enabled(False)
        if self.editing is not None:
            self.end_edit()
        self._end_script_capture()
        self._stop_typing()
        if self.tab != 1:
            self.show_tab(1)
        self._picking = PickLayer(self, sc["id"])
        self.engine.capture_id = ("pick", id(self._picking))     # Esc / Enter: xong
        self._sync_points()
        self.root.withdraw()
        self._picking.show()

    def pick_at(self, x, y):
        """Click trên lớp chọn điểm: thêm 1 điểm vào cuối combo đang sửa."""
        pk = self._picking
        if pk is None:
            return None
        if self.sel_sid != pk.sid or self._script(pk.sid) is None:
            self.end_pick()
            return None
        p = self.add_point(x, y)
        pk.added.append(p)
        pk.after_change()
        return p

    def pick_undo(self):
        """Chuột phải trên lớp chọn điểm: bỏ điểm vừa thêm (lần lượt từng điểm)."""
        pk = self._picking
        while pk is not None and pk.added:
            p = pk.added.pop()
            if self._find_step(p)[0] is not None:
                self.remove_point(p)
                break
        if pk is not None:
            pk.after_change()

    def end_pick(self):
        pk, self._picking = self._picking, None
        if pk is None:
            return
        cap = self.engine.capture_id
        if isinstance(cap, tuple) and cap[0] == "pick":
            self.engine.capture_id = None
        pk.destroy()
        self.root.deiconify()
        try:
            self.root.lift()
            self.root.focus_force()
        except tk.TclError:
            pass
        sc = self._script(pk.sid)
        n = sum(1 for p in pk.added if self._find_step(p)[0] is not None)
        if n and sc is not None:
            self._script_msg("Đã thêm %d điểm vào “%s”. Bấm vào 1 bước (hoặc chuột phải vào "
                             "điểm) để đổi việc làm." % (n, sc["name"] or "combo"), "ok", 9000)
        if self.step_rows:
            self.root.after_idle(lambda r=self.step_rows[-1]: r.winfo_exists()
                                 and self.step_area.see(r))
        self._sync_points()

    # ---- sửa combo ----
    def select_script(self, sid):
        """Bấm vào 1 combo trong danh sách: chọn để sửa ở khung bên dưới."""
        if sid == self.sel_sid or self._script(sid) is None:
            return
        self._end_script_capture()
        self._stop_typing()
        self.sel_sid = sid
        self._refresh_combo_tab(force=True)
        self._schedule_save()
        row = self.combo_rows.get(sid)
        if row is not None:
            self.combo_area.see(row)

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
                APP_NAME, "Xoá combo “%s” (cả %d điểm của nó)?" % (sc["name"] or "(không tên)",
                                                              len(sc["steps"])),
                parent=self.root):
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
        self._script_msg("Đã xoá combo “%s”." % (sc["name"] or "(không tên)"))

    def _on_script_name(self):
        if self._loading_script_ui:
            return
        sc = self._sel_script()
        if sc is None:
            return
        name = self.var_sname.get().strip()[:40].rstrip()
        if name != sc["name"]:
            sc["name"] = name
            self._update_combo_row(sc["id"])
            self._schedule_save()

    def remove_step(self, i, sc=None):
        sc = sc or self._sel_script()
        if sc is not None and 0 <= i < len(sc["steps"]):
            del sc["steps"][i]
            self._script_changed()

    def move_step(self, i, direction):
        """▲ ▼: đổi thứ tự bước – số của các điểm trên màn hình đổi theo."""
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
            self._sync_scripts()
            if self.sel_sid is not None:
                self._update_combo_row(self.sel_sid)
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
        self.fld_loops.state(["disabled"] if sc["forever"] else ["!disabled"])
        self._script_changed()

    def _on_f9(self):
        """Công tắc "Chạy khi nhấn F9": F9 chạy cùng lúc mọi combo có bật công tắc này."""
        if self._loading_script_ui:
            return
        sc = self._sel_script()
        if sc is None:
            return
        sc["f9"] = bool(self.var_f9.get())
        self._script_changed()
        key = self.f9_label
        group = [x["name"] or "combo" for x in self.scripts if x["f9"]]
        if len(group) > 1:
            self._script_msg("%s chạy cùng lúc %d combo: %s." % (key, len(group), ", ".join(group)))
        elif group:
            self._script_msg("%s chạy combo: %s." % (key, group[0]))
        else:
            self._script_msg("Chưa có combo nào chạy bằng %s." % key, "warn")

    # ---- phím chạy combo ----
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
                         % (sc["name"] or "combo"), "warn", None)
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
                             "Nhấn phím khác – Esc: huỷ." % name, "warn", None)
            return
        self._end_script_capture()
        moved = self._claim_key(vk, ("script", sid))
        sc["key"] = vk
        text = "Phím chạy của “%s”: %s." % (sc["name"] or "combo", name)
        self._script_msg(text + (" " + moved if moved else ""), "warn" if moved else "ok",
                         9000 if moved else 5000)
        self.layout_changed()

    def clear_script_key(self):
        """Bỏ phím chạy của combo đang chọn: không cần phím riêng. Các phím của nút vẫn
        click bình thường; muốn chạy combo thì nhấn F9 hoặc nút ▶ ở dòng combo."""
        sc = self._sel_script()
        self._end_script_capture()
        if sc is None or sc["key"] is None:
            return
        sc["key"] = None
        self._script_changed()
        key = self.f9_label
        if sc["f9"]:
            how = "combo này chạy bằng %s." % key
        else:
            how = "bật “Chạy khi nhấn %s” để chạy combo bằng %s." % (key, key)
        self._script_msg("Đã bỏ phím chạy. Phím các nút vẫn click như thường; " + how)

    def _claim_key(self, vk, owner):
        """1 phím chỉ làm 1 việc: lấy phím vk khỏi nút / combo khác đang dùng nó.
        Trả về câu báo (hoặc "" nếu phím chưa ai dùng)."""
        name = vk_label(vk, self.api)
        msgs = []
        for c in self.circles.values():
            if c.key == vk and owner != ("circle", c.id):
                c.key = None
                c.flash(THEME["warn"], 700)
                c.redraw()
                msgs.append("Phím %s đã chuyển từ nút cũ sang chỗ mới." % name)
        for sc in self.scripts:
            if sc["key"] == vk and owner != ("script", sc["id"]):
                sc["key"] = None
                msg = "Phím %s chuyển từ combo “%s” sang chỗ mới." % (name, sc["name"] or "combo")
                if sc["f9"]:
                    msg += " Combo đó vẫn chạy bằng %s." % self.f9_label
                msgs.append(msg)
        return " ".join(msgs)

    # ---- chạy / dừng ----
    #  Nhiều combo chạy CÙNG LÚC được:
    #   - F9 (hoặc nút "Chạy các combo F9"): chạy cùng lúc mọi combo có bật "Chạy khi nhấn F9";
    #     đang có combo chạy thì F9 = dừng hết.
    #   - Phím chạy riêng / nút ▶ ở dòng combo: chạy / dừng riêng combo đó.
    #   - Esc / nút "Dừng hết": dừng hết.
    def _update_script_buttons(self):
        self.btn_run.state(["disabled"] if self.running else ["!disabled"])
        self.btn_stop.state(["!disabled"] if self.running else ["disabled"])

    def _script_name(self, sid):
        sc = self._script(sid)
        return (sc["name"] or "combo") if sc else "combo"

    def _f9_scripts(self):
        """Các combo có bật "Chạy khi nhấn F9" và có ít nhất 1 bước."""
        return [sc for sc in self.scripts if sc["f9"] and self._script_targets(sc)]

    def _can_run(self):
        if self.hook_error:
            self._script_msg("Không chạy được: KeyClick không bắt được phím nên không dừng "
                             "combo bằng Esc được.", "error")
            return False
        if self.editing is not None:
            self.end_edit()
        self._end_script_capture()
        if not self.enabled:
            self.set_enabled(True)          # chế độ chơi: nút tròn để chuột đi xuyên qua
        return True

    def _launch(self, group):
        """Chạy các combo trong group (F9 / nút ▶). False = không chạy được.
        Điểm đang hiện (combo đang chọn) giữ nguyên, chỉ đổi sang kiểu "đang chạy"; điểm chưa
        có thì tạo SAU khi combo bắt đầu bấm (tạo cửa sổ mất chút thời gian – combo không phải
        đợi; điểm mới xuyên chuột ngay từ đầu)."""
        for sc in group:
            self.running[sc["id"]] = self._script_loops(sc)
            self.progress[sc["id"]] = 1
            self._cancel_linger(sc["id"])
            self._lit.pop(sc["id"], None)
        self._hold_points = True
        try:
            ok = self._can_run()
        finally:
            self._hold_points = False
        if not ok:
            for sc in group:
                self.running.pop(sc["id"], None)
                self.progress.pop(sc["id"], None)
            self._sync_points()
            return False
        for sc in group:
            self.engine.start_script(sc["id"], self._script_targets(sc), self.running[sc["id"]])
        self._sync_points()
        return True

    def _after_run_change(self):
        self._update_status()
        self._update_script_buttons()
        self._refresh_combo_rows()
        self._sync_points()                 # điểm của combo đang chạy: hiện / ẩn

    def run_script(self):
        """Phím F9 / nút "Chạy các combo F9": chạy CÙNG LÚC các combo có bật "Chạy khi nhấn F9"."""
        if self.running:
            return
        group = self._f9_scripts()
        if not group:
            sc = self._sel_script()
            if sc is not None and sc["f9"] and not self._script_targets(sc):
                text = "Combo “%s” chưa có điểm nào: bấm “Thêm điểm”." % sc["name"]
            else:
                text = "Chưa có combo nào bật “Chạy khi nhấn %s”." % self.f9_label
            self._script_msg(text, "warn")
            self.toast.show("Chưa có combo nào để chạy", self.root.winfo_screenwidth() // 2,
                            self.px(28), "n", "#334155", "#ffffff", ms=1500)
            return
        self._quiet_start = set(sc["id"] for sc in group)
        if not self._launch(group):
            self._quiet_start = set()
            return
        names = ", ".join("“%s”" % (sc["name"] or "combo") for sc in group)
        if len(group) == 1:
            self._script_msg("Đang chạy %s…   (Esc để dừng)" % names, ms=4000)
            toast = "Combo %s: CHẠY  –  Esc để dừng" % names
        else:
            self._script_msg("Đang chạy cùng lúc %d combo: %s   (Esc: dừng hết)"
                             % (len(group), names), ms=4000)
            toast = "Chạy cùng lúc %d combo  –  Esc để dừng" % len(group)
        self.toast.show(toast, self.root.winfo_screenwidth() // 2, self.px(28), "n", "#6d28d9",
                        "#ffffff", ms=1500)
        self._after_run_change()

    def test_script(self, sid=None):
        """Nút ▶ ở dòng combo: chạy riêng combo đó (sid; None = combo đang chọn)."""
        sc = self._script(sid) if sid is not None else self._sel_script()
        if sc is None or sc["id"] in self.running:
            return
        if not self._script_targets(sc):
            self._script_msg("Combo “%s” chưa có điểm nào: bấm “Thêm điểm”." % sc["name"], "warn")
            return
        if not self._launch([sc]):
            return
        self._script_msg("Đang chạy “%s”…   (Esc để dừng)" % (sc["name"] or "combo"), ms=4000)
        self._after_run_change()

    def toggle_combo(self, sid):
        if sid in self.running:
            self.stop_script(sid)
        else:
            self.test_script(sid)

    def stop_script(self, sid=None):
        """Dừng 1 combo (sid) hoặc tất cả combo đang chạy."""
        if sid is None:
            if self.running:
                self.engine.stop_script()
        elif sid in self.running:
            self.engine.stop_script(sid)

    def _on_script_started(self, sid, loops):
        self.running[sid] = loops
        self.progress.setdefault(sid, 1)
        self._cancel_linger(sid)
        self._lit.pop(sid, None)                    # bước 1 sẽ sáng khi engine bắt đầu bấm
        self._after_run_change()
        if sid in self._quiet_start:                # chạy theo nhóm F9: đã báo 1 lần rồi
            self._quiet_start.discard(sid)
        elif loops != 1:                            # combo 1 lần bấm bằng phím: không báo
            self.toast.show("Combo “%s”: CHẠY  –  Esc để dừng" % self._script_name(sid),
                            self.root.winfo_screenwidth() // 2, self.px(28), "n", "#6d28d9",
                            "#ffffff", ms=1500)

    def _on_script_progress(self, sid, n, loops):
        self.progress[sid] = n
        self._update_combo_row(sid)

    def _on_script_done(self, sid, reason, done):
        ended = list(self.running) if sid is None else [sid]
        if sid is None:
            loops = None
            self.running.clear()
            self.progress.clear()
        else:
            loops = self.running.pop(sid, 1)
            self.progress.pop(sid, None)
        for x in ended:
            if reason == "done" and self.enabled:
                self._linger_points(x)              # chạy xong: điểm ở lại thêm chút rồi ẩn
            else:
                self._cancel_linger(x)              # bị dừng: ẩn điểm ngay
                self._lit.pop(x, None)
        self._quiet_start.discard(sid)
        looping = loops != 1
        self._after_run_change()
        if sid is not None and self._script(sid) is None:
            return                          # combo vừa bị xoá (Xoá combo / Xoá hết / Mở bộ phím)
        name = self._script_name(sid)
        kind = "info"
        if reason == "error":
            msg, kind = "Combo dừng vì có lỗi (xem keyclick.log).", "error"
        elif reason == "empty":
            msg, kind = "Combo “%s” chưa có điểm nào." % name, "warn"
        elif sid is None:
            msg = "Đã dừng."
        elif reason == "done":
            msg, kind = "“%s”: xong%s." % (name, " %d vòng" % done if looping else ""), "ok"
        else:
            msg = "“%s”: đã dừng%s." % (name, " sau %d vòng" % done if looping else "")
        if self.running:                            # còn combo khác đang chạy
            msg += "  Còn %d combo đang chạy." % len(self.running)
        self._script_msg(msg, kind)
        if looping or reason == "error":
            toast = {"done": "XONG", "error": "LỖI"}.get(reason, "DỪNG")
            text = ("Combo “%s”: %s" % (name, toast)) if self.running or sid is not None \
                else "Combo: %s" % toast
            if not self.running and reason == "stopped":
                text = "Đã dừng hết combo"
            self.toast.show(text, self.root.winfo_screenwidth() // 2, self.px(28), "n",
                            "#334155", "#ffffff", ms=1300)

    # ------------------------------------------------------------------ cửa sổ
    def _set_icon(self):
        try:
            self._icon = tk.PhotoImage(master=self.root, data=ICON_PNG_B64)
            self.root.iconphoto(True, self._icon)
        except Exception:
            pass

    def _work_area(self):
        """(x, y, rộng, cao) vùng màn hình không bị thanh taskbar che."""
        try:
            wa = self.api.work_area()
        except Exception:
            wa = None
        if wa:
            return wa
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        return 0, 0, sw, sh - self.px(48)

    def _window_size(self):
        """Cỡ cố định của cửa sổ (không đổi theo nội dung). Màn hình thấp thì thấp lại;
        khi đó tab nào dài quá sẽ cuộn được."""
        S = self.px
        avail = self._work_area()[3] - S(42)         # chừa thanh tiêu đề + viền cửa sổ
        return S(WIN_W), max(S(400), min(S(WIN_H), avail))

    def _place_main_window(self):
        w, h = self._window_size()
        wx, wy, ww, wh = self._work_area()
        vx, vy, vw, vh = self.vscreen()
        pos = self._window_pos
        if not (pos and vx <= pos[0] <= vx + vw - 120 and vy <= pos[1] <= vy + vh - 80):
            pos = (wx + max(0, (ww - w) // 2), wy + max(0, (wh - h - self.px(42)) // 3))
        elif pos[1] + h + self.px(42) > wy + wh:          # cửa sổ cao hơn bản cũ: kéo lên
            pos = (pos[0], max(wy, wy + wh - h - self.px(42)))
        self.root.geometry("%dx%d+%d+%d" % (w, h, pos[0], pos[1]))

    def _window_position(self):
        m = re.match(r"^\d+x\d+\+(-?\d+)\+(-?\d+)$", self.root.geometry())
        return [int(m.group(1)), int(m.group(2))] if m else None

    def _dark_title_bar(self):
        """Windows 10/11: thanh tiêu đề màu tối cho hợp với cửa sổ."""
        try:
            self.root.update_idletasks()
            self.api.dark_title_bar(self.api.toplevel_hwnd(self.root), UI["title"])
        except Exception:
            log_exc("dark title bar")

    # ------------------------------------------------------------------ công tắc & cài đặt
    def _on_status_switch(self):
        self.set_enabled(not self.enabled)

    def _on_cb_return(self):
        on = bool(self.var_return.get())
        self.engine.return_cursor = on
        self.cfg["return_cursor"] = on
        self._schedule_save()

    def _on_cb_show_play(self):
        self.set_show_play(self.var_show_play.get())

    def _on_cb_admin(self):
        """Công tắc "Luôn chạy Admin": lần sau mở KeyClick sẽ tự xin quyền Admin."""
        on = bool(self.var_admin.get())
        self.cfg["run_as_admin"] = on
        self.save_config()
        if not on:
            self.notify("Lần sau mở, KeyClick sẽ chạy bình thường (không xin quyền Admin).",
                        kind="info")
        elif self._is_admin:
            self.notify("Lần sau mở, KeyClick sẽ tự chạy bằng quyền Admin.", kind="info")
        elif messagebox.askyesno(
                APP_NAME, "Chạy lại KeyClick bằng quyền Admin ngay bây giờ?\n\n"
                "Từ giờ mỗi lần mở, KeyClick sẽ tự xin quyền Admin (Windows hỏi Yes/No).",
                parent=self.root):
            self.relaunch_admin()
        else:
            self.notify("Lần sau mở, KeyClick sẽ tự xin quyền Admin.", kind="info")

    def _on_bg_alpha(self, value=None):
        """Thanh trượt "Độ đậm nền nút": chỉ đổi độ mờ của NỀN, chữ vẫn rõ."""
        pct = max(5, min(100, int(round(float(self.var_bg.get())))))
        self.lbl_bg.configure(text="%d%%" % pct)
        alpha = pct / 100.0
        if alpha == self.cfg["bg_alpha"]:
            return
        self.cfg["bg_alpha"] = alpha
        self._draw_preview()
        for c in self.circles.values():
            c.apply_alpha()
        self._schedule_save()

    def _update_turbo_note(self):
        cps = 1000.0 / max(30, self.cfg["turbo_interval_ms"])
        self.lbl_turbo_note.configure(text="ms = %s lần/giây" % (
            "%d" % round(cps) if cps >= 9.95 else ("%.1f" % cps).replace(".", ",")))

    def _on_turbo_field(self):
        if self._turbo_ui:
            return
        try:
            ms = int(str(self.var_turbo.get()).strip())
        except ValueError:
            return
        lo, hi = CFG_LIMITS["turbo_interval_ms"]
        if lo <= ms <= hi and ms != self.cfg["turbo_interval_ms"]:
            self.set_turbo_interval(ms)

    def set_turbo_interval(self, ms):
        ms = int(ms)
        self.cfg["turbo_interval_ms"] = ms
        self.engine.set_timing(turbo_interval_ms=ms)
        try:
            same = int(str(self.var_turbo.get()).strip()) == ms
        except ValueError:
            same = False
        if not same:
            self._turbo_ui = True
            try:
                self.var_turbo.set(str(ms))
            finally:
                self._turbo_ui = False
        self._update_turbo_note()
        self._refresh_buttons_tab()                  # "Giữ F = 10 click mỗi giây"
        self._schedule_save()

    def set_enabled(self, on, from_hotkey=False):
        on = bool(on)
        if on and self.hook_error:
            self.notify("Không bật được: " + self.hook_error, kind="error")
            return
        if on and self.editing is not None:
            self.end_edit()
        if on:
            self.end_pick()                 # đang chọn điểm combo: xong luôn
            self._end_script_capture()
            self._stop_typing()             # đang gõ dở trong ô Tên/ô số: thôi gõ, phím click
        changed = on != self.enabled
        self.enabled = on
        self.engine.enabled = on
        if not on:
            self.stop_script()              # tắt phím tắt = dừng luôn combo
            self.engine.release_all()
            for sid in list(self._linger):
                self._cancel_linger(sid)
        for c in self.circles.values():
            c.apply_mode()
        self._sync_points()                 # đang chơi: chỉ điểm combo đang chạy; tắt: để sửa
        self._update_status()
        if from_hotkey:
            self.show_toast(on)
        if (on and changed and not any(c.key is not None for c in self.circles.values())
                and not any(sc["key"] is not None for sc in self.scripts)
                and not self._f9_scripts()):
            self.notify("Chưa có nút nào được gán phím. Bấm “Thêm nút” để tạo.")

    def set_show_play(self, on):
        """Công tắc "Hiện nút & điểm khi F8 bật" (tab Cài đặt, mặc định bật). Tắt: lúc F8 bật thì
        ẩn hết nút tròn và điểm combo (phím vẫn click, combo vẫn chạy); F8 tắt thì vẫn hiện để
        sửa như thường."""
        on = bool(on)
        self.cfg["show_play"] = on
        self.var_show_play.set(on)
        for c in self.circles.values():
            c.apply_mode()
        self._sync_points()
        self._schedule_save()
        if on:
            self.msgbar.clear("hidden")
            self.msgbar.show("F8 bật vẫn hiện nút tròn và điểm combo (mờ hơn, chuột đi xuyên qua).",
                             "info", 5000, tag="hidden")
        else:
            self.msgbar.show("F8 bật thì ẩn hết nút tròn và điểm combo – phím vẫn click, combo vẫn "
                             "chạy. F8 tắt thì hiện lại để sửa.", "info", 7000, tag="hidden")

    def show_toast(self, on):
        if on:
            text, bg = "KeyClick: BẬT  –  nhấn phím để click", "#15803d"
        else:
            text, bg = "KeyClick: TẮT  –  có thể chỉnh nút", "#334155"
        self.toast.show(text, self.root.winfo_screenwidth() // 2, self.px(28), "n", bg,
                        "#ffffff", ms=1300)

    # ------------------------------------------------------------------ nút tròn
    def _create_circle(self, cx, cy, size, key=None, button="left", mode="click",
                       x2=None, y2=None, swipe_ms=DEFAULT_SWIPE_MS, text=None, out=None):
        """text: {"text", "enter", "click", "method"} của nút Nhập chữ (hoặc None);
        out: phím sẽ được bấm của nút Phím."""
        cx, cy = self.clamp_point(cx, cy)
        if x2 is not None and y2 is not None:
            x2, y2 = self.clamp_point(x2, y2)
        t = text or {}
        c = Circle(self, cx, cy, size, key, button, mode, x2, y2, swipe_ms, t.get("text", ""),
                   t.get("enter", False), t.get("click", False), t.get("method", "paste"), out)
        self.circles[c.id] = c
        return c

    def _create_from_dict(self, b):
        return self._create_circle(b["x"], b["y"], b["size"] or self.default_size(),
                                   b["key"], b["mouse"], b["mode"],
                                   b.get("x2"), b.get("y2"), b.get("swipe_ms", DEFAULT_SWIPE_MS),
                                   {"text": b.get("text", ""), "enter": b.get("enter", False),
                                    "click": b.get("click_first", False),
                                    "method": b.get("method", "paste")}, b.get("out"))

    def _create_buttons(self, buttons):
        """Tạo các nút từ file; trả về danh sách nút theo đúng thứ tự trong file."""
        created, used = [], set()
        for b in buttons:
            if b["key"] is not None and b["key"] in used:   # trùng phím -> bỏ phím
                b["key"] = None
            used.add(b["key"])
            created.append(self._create_from_dict(b))
        return created

    def ask_text(self, title, settings=None, for_point=False):
        """Hộp Nhập chữ (tắt phím tắt trong lúc gõ). Trả về cài đặt, hoặc None = Huỷ.
        for_point: cho 1 điểm combo (chữ trong hộp nói "điểm" thay cho "nút")."""
        if self.enabled:
            self.set_enabled(False)
        if self.editing is not None:
            self.end_edit()
        self._end_script_capture()
        return TextDialog(self, title, settings, for_point).show()

    def add_text_circle(self):
        """Nút "Nhập chữ": gõ chữ cần nhập trước, rồi mới tạo nút tròn để gán phím."""
        st = self.ask_text("Thêm nút nhập chữ")
        if st is None:
            return None
        return self.add_circle(mode="text", text=st)

    def edit_circle_text(self, c):
        """Sửa chữ cần nhập (chuyển nút sang kiểu Nhập chữ nếu chưa phải). False = Huỷ."""
        if c.id not in self.circles:
            return False
        st = self.ask_text("Sửa chữ cần nhập" if c.mode == "text" else "Đổi thành nút nhập chữ",
                           c.text_settings() if (c.mode == "text" or c.text) else None)
        if st is None or c.id not in self.circles:
            return False
        c.text, c.text_enter, c.text_click, c.text_method = (st["text"], st["enter"], st["click"],
                                                             st["method"])
        if c.mode != "text":
            c.set_mode("text")
        c.redraw()
        self.layout_changed()
        return True

    def ask_key(self, title, current=None, for_point=False):
        """Hộp Nút phím: chọn phím sẽ được bấm. Trả về mã phím, hoặc None = Huỷ.
        for_point: cho 1 điểm combo (bước đó nhấn rồi thả phím)."""
        if self.enabled:
            self.set_enabled(False)
        if self.editing is not None:
            self.end_edit()
        self._end_script_capture()
        return KeyDialog(self, title, current, for_point).show()

    def add_key_circle(self):
        """Nút "Nút phím": chọn phím sẽ bấm (vd Backspace), rồi tạo nút tròn để gán phím (vd A).
        Nhấn A = KeyClick bấm Backspace."""
        vk = self.ask_key("Thêm nút phím")
        if vk is None:
            return None
        return self.add_circle(mode="key", out=vk)

    def edit_circle_key(self, c):
        """Đổi phím sẽ bấm (chuyển nút sang kiểu Phím nếu chưa phải). False = Huỷ."""
        if c.id not in self.circles:
            return False
        vk = self.ask_key("Đổi phím sẽ bấm" if c.mode == "key" else "Đổi thành nút phím", c.out)
        if vk is None or c.id not in self.circles:
            return False
        c.out = vk
        if c.mode != "key":
            c.set_mode("key")
        c.redraw()
        self.layout_changed()
        return True

    def add_circle(self, mode="click", text=None, out=None):
        if self.enabled:
            self.set_enabled(False)
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
        c = self._create_circle(x, y, self.default_size(), mode=mode, text=text, out=out)
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
        c = self._create_circle(x, y, src.size, None, src.button, src.mode, x2, y2, src.swipe_ms,
                                src.text_settings(), src.out)
        if start_edit:
            c.start_edit()
        self.layout_changed()
        return c

    def delete_circle(self, c):
        if c.id not in self.circles:
            return
        if self.editing is c:
            self.end_edit()
        self.circles.pop(c.id, None)
        c.destroy()
        self.layout_changed()

    def clear_all(self):
        """Nút "Xoá hết": xoá mọi nút tròn VÀ mọi combo (chỉ còn 1 combo trống)."""
        n_btn, n_combo = len(self.circles), len(self.scripts)
        if not n_btn and n_combo <= 1 and all(self._blank_script(sc) for sc in self.scripts):
            self.notify("Chưa có nút hay combo nào để xoá.", kind="info")
            return
        what = " và ".join(x for x in ("%d nút" % n_btn if n_btn else "",
                                       "%d combo" % n_combo if n_combo else "") if x)
        if not messagebox.askyesno(
                APP_NAME, "Xoá tất cả %s?\n\nMuốn giữ lại để dùng sau thì bấm “Lưu…” trước "
                "(file bộ phím lưu cả nút lẫn combo)." % what, parent=self.root):
            return
        self.load_buttons([])                # tắt phím tắt, dừng combo, xoá nút + combo
        self.notify("Đã xoá hết %s." % what, kind="ok")

    def set_circle_prop(self, c, prop, value):
        if prop == "mode" and value == "text" and c.mode != "text":
            self.edit_circle_text(c)     # hỏi chữ cần nhập trước (Huỷ = giữ kiểu cũ)
            return
        if prop == "mode" and value == "key" and c.mode != "key":
            self.edit_circle_key(c)      # hỏi phím sẽ bấm trước (Huỷ = giữ kiểu cũ)
            return
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

    def show_circle_menu(self, c, x, y, from_list=False):
        """Menu của 1 nút: chuột phải vào nút tròn, hoặc nút ⋯ trong tab Nút bấm."""
        m = self._menu()
        vb = tk.StringVar(master=self.root, value=c.button)
        vm = tk.StringVar(master=self.root, value=c.mode)
        current = vk_label(c.key, self.api) if c.key is not None else "chưa có"
        later = lambda fn, *a: (lambda: self.root.after_idle(fn, *a))   # sau khi menu đóng
        m.add_command(label="Gán phím…   (đang là: %s)" % current, command=later(self.begin_edit, c))
        m.add_command(label="Nhân bản", command=later(self.duplicate, c))
        m.add_separator()
        for val, text in (("left", "Click chuột trái"), ("right", "Click chuột phải"),
                          ("middle", "Click chuột giữa")):
            m.add_radiobutton(label=text, value=val, variable=vb,
                              command=later(self.set_circle_prop, c, "button", val),
                              state="disabled" if c.mode == "key" else "normal")
        m.add_separator()
        for val, text in (("click", "Nhấn phím = click 1 lần"),
                          ("hold", "Giữ phím = giữ chuột (kéo / ngắm skill)"),
                          ("turbo", "Giữ phím = click liên tục (turbo)"),
                          ("swipe", "Nhấn phím = vuốt (từ nút tới chấm vàng)"),
                          ("text", "Nhấn phím = nhập chữ (dán chữ có sẵn)"),
                          ("key", "Nhấn phím = bấm phím khác (vd Backspace)")):
            m.add_radiobutton(label=text, value=val, variable=vm,
                              command=later(self.set_circle_prop, c, "mode", val))
        subs = self._speed_menus(m, later, c.swipe_ms,
                                 lambda ms: self.set_circle_prop(c, "swipe_ms", ms),
                                 c.mode == "swipe")
        m.add_command(label="Sửa chữ cần nhập…", command=later(self.edit_circle_text, c),
                      state="normal" if c.mode == "text" else "disabled")
        m.add_command(label="Đổi phím sẽ bấm…   (đang là: %s)" % (vk_long_name(c.out, self.api)
                                                                if c.out is not None else "chưa có"),
                      command=later(self.edit_circle_key, c),
                      state="normal" if c.mode == "key" else "disabled")
        m.add_separator()
        m.add_command(label="To hơn", command=later(c.resize, +6))
        m.add_command(label="Nhỏ hơn", command=later(c.resize, -6))
        m.add_separator()
        m.add_command(label="Bỏ gán phím", command=later(self.clear_key, c),
                      state="normal" if c.key is not None else "disabled")
        m.add_command(label="Xoá nút này", command=later(self.delete_circle, c))
        self._menu_refs = (m, vb, vm) + subs
        if not from_list:
            try:
                self.api.force_foreground(c.hwnd)   # để menu tự đóng khi bấm ra ngoài
            except Exception:
                pass
        try:
            m.tk_popup(x, y)
        finally:
            m.grab_release()
            if c.id in self.circles:
                self._raise_circle(c)

    def _raise_circle(self, c):
        """Đưa nút lên trên cùng: lớp nền trước, lớp chữ sau (chữ luôn nằm trên nền)."""
        try:
            self.api.set_topmost(c.hwnd)
            self.api.set_topmost(c.fhwnd)
        except Exception:
            log_exc("raise")
        c._fix_stack()

    # ------------------------------------------------------------------ gán phím
    def begin_edit(self, c):
        if c.id not in self.circles:
            return
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
        self._refresh_buttons_tab()
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
        self._refresh_buttons_tab()

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
        if token[0] == "pick":                  # đang chọn điểm combo: Esc / Enter = xong
            pk = self._picking
            if pk is not None and id(pk) == token[1]:
                if vk in (VK_ESCAPE, VK_RETURN):
                    self.end_pick()
                else:
                    self.engine.capture_id = token      # phím khác: vẫn đang chọn điểm
            return
        if token[0] == "outkey":                # hộp Nút phím đang chờ phím sẽ bấm
            d = self._key_dialog
            if d is not None and d.token == token:
                d.on_captured(vk)
            return
        c = self.circles.get(token[1])
        if c is None or self.editing is not c:
            return
        if vk == VK_ESCAPE:
            self.end_edit()
            return
        moved = self._claim_key(vk, ("circle", c.id))   # 1 phím chỉ dùng cho 1 nút / 1 combo
        if moved:
            self.notify(moved, ms=8000)
        c.key = vk
        self.end_edit()
        self.layout_changed()

    def layout_changed(self, save=True):
        if self.running:                  # nút thay đổi giữa chừng -> dừng combo cho an toàn
            self.stop_script()
        mapping = {}
        for c in self.circles.values():
            if c.key is not None:
                mapping[c.key] = c.target()
        self.engine.set_mappings(mapping)
        self._sync_scripts()
        self._refresh_buttons_tab()
        self._refresh_combo_tab()
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
        try:
            if self._lit_dirty:             # combo đang chạy vừa sang bước khác
                self._apply_lit()
        except Exception:
            log_exc("poll")
        self._reschedule("_poll_job", 15, self._poll)

    def _reschedule(self, attr, ms, fn):
        """Hẹn chạy lại fn sau ms (huỷ lần hẹn cũ nếu fn bị gọi thẳng, không qua after)."""
        old = getattr(self, attr)
        if old:
            try:
                self.root.after_cancel(old)
            except Exception:
                pass
        setattr(self, attr, self.root.after(ms, fn))

    def _handle(self, ev):
        kind = ev[0]
        if kind == "toggle":
            self.set_enabled(not self.enabled, from_hotkey=True)
        elif kind == "captured":
            self.on_captured(ev[1], ev[2])
        elif kind == "flash":               # nút tròn vừa chạy / combo vừa sang 1 bước
            c = self.circles.get(ev[1])
            if c is not None:
                c.flash()
            else:
                self._light_point(ev[1])    # điểm của bước đó sáng xanh lá (nếu đang hiện)
        elif kind == "script_toggle":       # F9: chạy cùng lúc các combo có bật F9 / dừng hết
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
            if self.enabled and self.api.is_windows:
                if self.cfg["show_play"]:
                    for c in self.circles.values():
                        self._raise_circle(c)
                for cp in self.points.values():     # điểm đang hiện lúc F8 bật
                    self._raise_circle(cp)
            elif self.api.is_windows:               # đang chỉnh: chữ / số luôn nằm trên nền
                for c in list(self.circles.values()) + list(self.points.values()):
                    c._fix_stack()
        except Exception:
            log_exc("topmost")
        self._reschedule("_top_job", 2000, self._keep_on_top)

    def _watch_foreground(self):
        try:
            self._check_foreground()
        except Exception:
            log_exc("foreground")
        self._reschedule("_fg_job", 700, self._watch_foreground)

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
        if not self.enabled or self.cfg["show_play"]:
            for c in self.circles.values():
                self._raise_circle(c)
        for cp in self.points.values():         # điểm combo đang hiện: nằm trên game
            self._raise_circle(cp)
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
        self.notify("Cửa sổ đó chạy quyền Admin nên Windows chặn KeyClick. Vào tab Cài đặt, bấm "
                    "“Chạy lại bằng quyền Admin”.", ms=20000, kind="error")

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
            self._update_status()

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
        if isinstance(data, dict) and data.get("button_style") != BUTTON_STYLE:
            # nút kiểu mới (trắng dịu): độ đậm mặc định cũ 40% quá nhạt -> dùng mặc định mới
            if data.get("bg_alpha") in (None, 0.4):
                self.cfg["bg_alpha"] = DEFAULT_CFG["bg_alpha"]
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
        d = {"app": APP_NAME, "version": 1, "button_style": BUTTON_STYLE}
        d.update(self.cfg)
        d["return_cursor"] = bool(self.var_return.get())
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
        if self._save_job:                  # lưu ngay: huỷ lần lưu đã hẹn
            try:
                self.root.after_cancel(self._save_job)
            except Exception:
                pass
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
        if not self.circles and not any(sc["steps"] for sc in self.scripts):
            self.notify("Chưa có nút hay combo nào để lưu.", kind="warn")
            return
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Lưu bộ phím (cả nút lẫn combo)", defaultextension=".json",
            initialdir=self._profile_initialdir(), initialfile="bo_phim.json",
            filetypes=[("Bộ phím KeyClick", "*.json"), ("Tất cả", "*.*")])
        if not path:
            return
        data = self.profile_data()
        try:
            write_json(path, data)
        except Exception as e:
            messagebox.showerror(APP_NAME, "Không lưu được:\n%s" % e, parent=self.root)
            return
        self.profile_dir = os.path.dirname(path)
        self._schedule_save()
        self.notify("Đã lưu %s: %d nút, %d combo." % (os.path.basename(path), len(data["buttons"]),
                                                     len(data["scripts"])), kind="ok")

    def profile_data(self):
        """Nội dung file bộ phím: các nút tròn + các combo (mỗi bước là 1 điểm riêng)."""
        return {"app": APP_NAME, "type": "profile", "version": 3,
                "buttons": [c.to_dict() for c in self.circles.values()],
                "scripts": self._scripts_data(), "script_sel": self._sel_index()}

    def open_profile(self):
        path = filedialog.askopenfilename(
            parent=self.root, title="Mở bộ phím (cả nút lẫn combo)",
            initialdir=self._profile_initialdir(),
            filetypes=[("Bộ phím KeyClick", "*.json"), ("Tất cả", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror(APP_NAME, "Không đọc được file:\n%s" % e, parent=self.root)
            return
        data = data if isinstance(data, dict) else {}
        buttons = parse_buttons(data.get("buttons"))
        scripts = parse_scripts(data.get("scripts"), [dict(b, id=0) for b in buttons]) or []
        if not buttons and not any(sc["steps"] for sc in scripts):
            messagebox.showwarning(APP_NAME, "File này không có nút hay combo nào.",
                                   parent=self.root)
            return
        loops, forever = _legacy_loop_settings(data)
        self.load_buttons(buttons, data.get("scripts"), data.get("script_sel", 0), loops, forever)
        self.profile_dir = os.path.dirname(path)
        self.notify("Đã mở %s: %d nút, %d combo." % (os.path.basename(path), len(buttons),
                                                    len(self.scripts)), kind="ok")

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
        self.msgbar._cancel()
        for bubble in (self.toast, self.hint):
            bubble._cancel()
        for job in (self._poll_job, self._top_job, self._fg_job, self._save_job, self._edit_job,
                    self._blink_job):
            if job:
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass
        if self.editing is not None:
            self.editing.stop_caret()
        if self._picking is not None:
            self._picking.destroy()
            self._picking = None
        for sid in list(self._linger):
            self._cancel_linger(sid)
        for cp in list(self.points.values()):
            try:
                cp.destroy()
            except Exception:
                pass
        self.points.clear()
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
    """Công tắc "Luôn chạy Admin" có đang bật không (đọc thẳng file cấu hình)."""
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
                and not api.is_admin()):          # đã bật "Luôn chạy Admin"
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
