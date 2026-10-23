# -*- coding: utf-8 -*-
"""
MiniKVM - giao diện kiểu Deskflow cho kvm.py. Chạy ẩn dưới khay hệ thống, không hiện cửa sổ CMD.

Cách dùng: đặt file này CÙNG THƯ MỤC với kvm.py rồi bấm đúp (đuôi .pyw = mở không có cửa sổ CMD).
  - Chọn "Máy chủ" hoặc "Máy khách" rồi bấm Bắt đầu. Máy chủ bấm "Cấu hình máy chủ" để kéo thả vị trí các máy.
  - Bấm X = ẩn xuống khay (biểu tượng cạnh đồng hồ). Bấm vào biểu tượng để mở lại, chuột phải để Bắt đầu/Dừng/Thoát.
    Màu biểu tượng: xám = dừng, xanh lá = đang chạy, xanh dương = ĐỒNG BỘ, vàng = đang chờ, đỏ = lỗi.
  - Quyền Admin: bấm "Chạy bằng Admin" 1 lần (Windows hỏi đúng 1 lần) -> từ đó mở app là tự có quyền Admin, không hỏi
    nữa (ô "Luôn mở bằng quyền Admin" = tác vụ tên MiniKVM trong Task Scheduler, bỏ tick là xóa tác vụ).
  - "Khởi động cùng Windows": đăng nhập Windows là app tự chạy dưới khay (bằng quyền Admin nếu đã bật ô trên).
  - Cấu hình sửa ngay trong app, app tự lưu ở %APPDATA%\\MiniKVM\\config.json (kvm.py đọc file này).
  - Mọi máy phải chạy CÙNG một file kvm.py (máy chạy bản khác: máy chủ không điều khiển được, bảng báo "khác bản").
  - Lỗi của app: %APPDATA%\\MiniKVM\\loi.txt ; nhật ký: %APPDATA%\\MiniKVM\\nhat_ky.txt

Cần: Python 3.8+ có tkinter (bản cài từ python.org có sẵn).
Biểu tượng dưới khay: pip install pystray pillow  (hoặc bấm "Cài ngay" trong app; không có thì bấm X chỉ thu nhỏ).
Tham số: --tray  mở sẵn dưới khay và tự bật kvm (dùng cho "Khởi động cùng Windows").
         --task  (tác vụ Task Scheduler gọi) bản quyền Admin mở không cần hỏi.
"""
import ast
import ctypes
import json
import os
import queue
import re
import socket
import subprocess
import sys
import threading
import time
import types

try:
    import tkinter as tk
    import tkinter.font as tkfont
    from tkinter import messagebox, ttk
except ImportError:   # .pyw không có cửa sổ CMD: phải báo bằng hộp thoại, không thì bấm đúp "không thấy gì"
    _m = ("Python trên máy này thiếu tkinter (phần giao diện).\n\n"
          "Cài lại Python từ python.org, ở bước cài nhớ tick \"tcl/tk and IDLE\".")
    if sys.platform == "win32":
        ctypes.windll.user32.MessageBoxW(None, _m, "MiniKVM", 0x10)
    else:
        print(_m)
    sys.exit(1)

APP = "MiniKVM"
IS_WIN = sys.platform == "win32"
HERE = os.path.dirname(os.path.abspath(__file__))
KVM_PATH = os.environ.get("MINIKVM_KVM") or os.path.join(HERE, "kvm.py")   # kvm.py nằm cạnh app
DATA_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), APP)   # dữ liệu của app
SETTINGS_FILE = os.path.join(DATA_DIR, "gui.json")    # cài đặt cửa sổ (vai trò, ẩn xuống khay...)
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")   # cấu hình kvm: vị trí các máy, IP, cổng... (kvm.py đọc)
CONTROL_PORT = int(os.environ.get("MINIKVM_CONTROL_PORT", "24899"))   # 127.0.0.1: mở app lần 2 -> hiện app cũ
CREATE_NO_WINDOW = 0x08000000 if IS_WIN else 0
TASK_NAME = "MiniKVM"   # tác vụ Task Scheduler: "Luôn mở bằng quyền Admin" (+ tự chạy khi đăng nhập)
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_FILE = os.path.abspath(__file__)   # file app đang chạy (kvm_gui.pyw)
HANDOFF_FILE = os.path.join(DATA_DIR, "handoff.json")   # bản quyền thường gửi tùy chọn sang bản Admin

# ------------------------------- màu (tối, giống Deskflow) -------------------------------
BG, PANEL, CELL, GRID, FIELD, BORDER = "#2b2b2b", "#353535", "#232323", "#161616", "#1e1e1e", "#4a4a4a"
FG, MUTED, ACCENT, ACCENT_HI = "#e8e8e8", "#9d9d9d", "#3d8fd1", "#57a3e0"
OK_C, WARN_C, ERR_C, SYNC_C, SEL = "#5cb85c", "#e0a030", "#e05555", "#4fb3e8", "#2f5f8a"
GREY = "#8a8a8a"
ROLE_NAME = {"master": "máy chủ", "client": "máy khách"}

# ------------------------------- cấu hình kvm (%APPDATA%\MiniKVM\config.json) -------------------------------
CFG_KEYS = ("ipTable", "MASTER_IP", "SYNC_IPS", "PORT", "CLICK_SETTLE", "RAW_MOUSE", "MOUSE_LIKE_MASTER")
BASE_CFG = {"ipTable": [[None, "MASTER", None]], "MASTER_IP": None, "SYNC_IPS": None, "PORT": 24900,
            "CLICK_SETTLE": 0.008, "RAW_MOUSE": False, "MOUSE_LIKE_MASTER": True}


def parse_assigns(text, keys):
    """Đọc các dòng `TÊN = giá trị` ở đầu kvm.py: chỉ ĐỌC giá trị, không chạy code nào trong file."""
    vals = {}
    for node in ast.parse(text).body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in keys):
            vals[node.targets[0].id] = ast.literal_eval(node.value)
    return vals


def kvm_defaults():
    """Giá trị mặc định đang ghi trong kvm.py (dùng khi chưa lưu cấu hình)."""
    try:
        with open(KVM_PATH, encoding="utf-8") as f:
            return parse_assigns(f.read(), CFG_KEYS)
    except (OSError, SyntaxError, ValueError):
        return {}


def validate(c):
    """Kiểm tra giống kvm.py -> trả câu báo lỗi hoặc None."""
    t = c.get("ipTable")
    if not (isinstance(t, list) and t and all(isinstance(r, list) for r in t)
            and all(v is None or isinstance(v, str) for r in t for v in r)
            and sum(v == "MASTER" for r in t for v in r) == 1):
        return 'ipTable phải là danh sách các dòng, có đúng 1 ô "MASTER"'
    ips = [v for r in t for v in r if v and v != "MASTER"]
    if len(ips) != len(set(ips)):
        return "Có máy bị trùng IP trong bố cục"
    if not (c.get("MASTER_IP") is None or isinstance(c.get("MASTER_IP"), str)):
        return 'MASTER_IP phải là None hoặc "IP"'
    s = c.get("SYNC_IPS")
    if not (s is None or isinstance(s, list) and all(isinstance(v, str) for v in s)):
        return 'SYNC_IPS phải là None hoặc ["IP", ...]'
    p = c.get("PORT")
    if type(p) is not int or not 1 <= p <= 65535:
        return "Cổng phải là số từ 1 đến 65535"
    cs = c.get("CLICK_SETTLE")
    if type(cs) not in (int, float) or not 0 <= cs <= 0.1:
        return "Thời gian chờ trước khi click phải từ 0 đến 100 ms"
    for k in ("RAW_MOUSE", "MOUSE_LIKE_MASTER"):
        if type(c.get(k)) is not bool:
            return f"{k} phải là True hoặc False"
    return None


def load_config():
    """-> (cấu hình, tên hiển thị {ip: tên}, lỗi hoặc None). Chưa lưu lần nào thì là giá trị ghi trong kvm.py."""
    cfg = dict(BASE_CFG)
    cfg.update(kvm_defaults())
    names, err = {}, None
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8-sig") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("nội dung không đúng dạng")
            test = dict(cfg)
            test.update({k: v for k, v in data.items() if k in CFG_KEYS})
            err = validate(test)
            if not err:
                cfg = test
                n = data.get("PC_NAMES")
                if isinstance(n, dict):
                    names = {str(k): str(v) for k, v in n.items()}
                keep = data.get("MASTER_IP_SAVED")
                if isinstance(keep, str) and cfg["MASTER_IP"] is None:
                    cfg["MASTER_IP_SAVED"] = keep
        except (OSError, ValueError) as e:
            err = str(e)
    return cfg, names, err


def save_config(cfg, names):
    """Lưu cấu hình (kvm.py đọc file này khi chạy). Ghi ra file tạm rồi mới thay -> tắt máy ngang cũng không hỏng."""
    data = {k: cfg[k] for k in CFG_KEYS}
    err = validate(data)
    if err:
        raise ValueError(err)
    data["PC_NAMES"] = {ip: n for ip, n in sorted(names.items()) if n and n != ip}   # tên hiển thị (chỉ app dùng)
    if data["MASTER_IP"] is None and cfg.get("MASTER_IP_SAVED"):   # máy khách tick "nhận mọi máy chủ": IP vẫn
        data["MASTER_IP_SAVED"] = cfg["MASTER_IP_SAVED"]            # để trong ô (chỉ app dùng, kvm.py bỏ qua)
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = CONFIG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, CONFIG_FILE)
    return CONFIG_FILE


def directions(table):
    """{ip: "TRÊN"/"DƯỚI"/"TRÁI"/"PHẢI"/"ô[r][c]"} so với ô MASTER (giống kvm.py)."""
    home = next(((r, c) for r, row in enumerate(table) for c, v in enumerate(row) if v == "MASTER"), (0, 0))
    out = {}
    for r, row in enumerate(table):
        for c, v in enumerate(row):
            if v and v != "MASTER":
                d = {(0, -1): "TRÁI", (0, 1): "PHẢI", (-1, 0): "TRÊN", (1, 0): "DƯỚI"}.get((r - home[0], c - home[1]))
                out[v] = d or f"ô[{r}][{c}]"
    return out


def peers_of(cfg):
    """Danh sách máy (theo thứ tự) + có đồng bộ không, giống cách kvm.py hiểu cấu hình."""
    table, sync = cfg["ipTable"], cfg["SYNC_IPS"]
    ips = [v for row in table for v in row if v and v != "MASTER"]
    out = [(ip, sync is None or ip in sync) for ip in ips]
    out += [(ip, True) for ip in (sync or ()) if ip and ip != "MASTER" and ip not in ips]
    return out


def host_error(ip):
    """IP (hoặc tên máy trong LAN) hợp lệ? -> câu báo lỗi hoặc None."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", ip) or ip.upper() == "MASTER":
        return "IP không hợp lệ"
    if re.fullmatch(r"[\d.]+", ip) and not (re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", ip)
                                            and all(int(x) <= 255 for x in ip.split("."))):
        return "IP không hợp lệ (dạng 192.168.1.102)"
    return None


# ------------------------------- Windows: admin, khởi động cùng Windows, ẩn CMD -------------------------------
def is_admin():
    if not IS_WIN:
        return hasattr(os, "geteuid") and os.geteuid() == 0
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def pythonw():
    """pythonw.exe (không có cửa sổ CMD) nếu có, không thì python đang chạy."""
    exe = sys.executable
    if IS_WIN:
        w = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.exists(w):
            return w
    return exe


def python_exe():
    """python.exe (bản console) cùng thư mục: chạy kvm.py / pip ẩn bằng CREATE_NO_WINDOW, đọc được output."""
    exe = sys.executable
    if IS_WIN and os.path.basename(exe).lower() == "pythonw.exe":
        p = os.path.join(os.path.dirname(exe), "python.exe")
        if os.path.exists(p):
            return p
    return exe


def run_out(args):
    """Chạy lệnh Windows ẩn (không cửa sổ CMD) -> (mã lỗi, câu báo của chương trình) để ghi vào nhật ký khi lỗi."""
    try:
        r = subprocess.run(args, capture_output=True, creationflags=CREATE_NO_WINDOW, timeout=20)
    except (OSError, subprocess.SubprocessError) as e:
        return -1, str(e)
    enc = "utf-8"
    if IS_WIN:
        try:   # chương trình console của Windows in chữ theo bảng mã OEM
            enc = f"cp{ctypes.windll.kernel32.GetOEMCP()}"
        except Exception:
            pass
    raw = (r.stderr or b"") + b" " + (r.stdout or b"")
    try:
        text = raw.decode(enc, "replace")
    except LookupError:
        text = raw.decode("utf-8", "replace")
    return r.returncode, " ".join(text.split())[:300]


def run_quiet(args):
    return run_out(args)[0]


def app_launch(extra=""):
    """Lệnh mở app (không cửa sổ CMD): (pythonw.exe, '"...kvm_gui.pyw" tham số')."""
    return pythonw(), f'"{APP_FILE}" {extra}'.strip()


def autostart_cmd():
    exe, args = app_launch("--tray")
    return f'"{exe}" {args}'


def win_user():
    """MÁY\\tên của người đang đăng nhập (tác vụ khởi động chỉ chạy cho đúng người này)."""
    try:
        n, buf = ctypes.c_ulong(256), ctypes.create_unicode_buffer(256)
        if ctypes.windll.secur32.GetUserNameExW(2, buf, ctypes.byref(n)) and buf.value:   # NameSamCompatible
            return buf.value
    except Exception:
        pass
    dom, user = os.environ.get("USERDOMAIN", ""), os.environ.get("USERNAME", "")
    return f"{dom}\\{user}" if dom else user


# Tác vụ Task Scheduler "MiniKVM" = "Luôn mở bằng quyền Admin": Windows chạy app bằng quyền Admin mà KHÔNG hỏi
# (chỉ hỏi 1 lần lúc tạo tác vụ). Bấm đúp mở app (quyền thường) -> app nhờ tác vụ mở bản Admin rồi tự thoát.
# Bật thêm "Khởi động cùng Windows" thì tác vụ có thêm lịch tự chạy khi đăng nhập.
# Tạo bằng XML để bỏ 2 cài đặt mặc định của Windows: tự TẮT app sau 3 ngày chạy liên tục, không chạy khi laptop dùng pin.
TASK_XML = '''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>MiniKVM - mở bằng quyền Admin không cần hỏi lại</Description>
  </RegistrationInfo>
  <Triggers>{triggers}</Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{user}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>false</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>4</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{cmd}</Command>
      <Arguments>{args}</Arguments>
      <WorkingDirectory>{cwd}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
'''
LOGON_XML = '''
    <LogonTrigger>
      <Enabled>true</Enabled>
      <UserId>{user}</UserId>
      <Delay>PT5S</Delay>
    </LogonTrigger>
  '''


def task_query():
    """-> None nếu chưa có tác vụ, không thì {"logon": có tự chạy khi đăng nhập, "new": tác vụ kiểu mới (--task)}"""
    if not IS_WIN:
        return None
    try:
        r = subprocess.run(["schtasks", "/Query", "/TN", TASK_NAME, "/XML"], capture_output=True,
                           creationflags=CREATE_NO_WINDOW, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    low = r.stdout.replace(b"\x00", b"").lower()   # (chỉ tìm chữ tiếng Anh: đúng cả khi Windows trả về UTF-16)
    return {"logon": b"<logontrigger" in low, "new": b"--task" in low}


def create_task(logon):
    """Tạo / ghi đè tác vụ (app phải đang có quyền Admin). -> (mã lỗi schtasks (0 = được), câu báo lỗi)"""
    import tempfile
    from xml.sax.saxutils import escape
    exe, args = app_launch("--task")
    user = escape(win_user())
    xml = TASK_XML.format(user=user, triggers=LOGON_XML.format(user=user) if logon else "", cmd=escape(exe),
                          args=escape(args), cwd=escape(HERE))
    path = os.path.join(tempfile.gettempdir(), f"minikvm_task_{os.getpid()}.xml")
    try:
        with open(path, "w", encoding="utf-16") as f:
            f.write(xml)
        rc, msg = run_out(["schtasks", "/Create", "/F", "/TN", TASK_NAME, "/XML", path])
    except OSError as e:
        rc, msg = -1, str(e)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    if rc != 0 and logon:   # dự phòng: cách đơn giản (chịu 2 cài đặt mặc định ở trên)
        if run_quiet(["schtasks", "/Create", "/F", "/TN", TASK_NAME, "/SC", "ONLOGON", "/RL", "HIGHEST",
                      "/TR", f'"{exe}" {args}']) == 0:
            return 0, ""
    return rc, msg


def run_key(value=None):
    """Mục Run (khởi động cùng Windows, quyền thường). value=None: xóa. -> True nếu ghi/xóa được"""
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if value is None:
                try:
                    winreg.DeleteValue(k, APP)
                except FileNotFoundError:
                    pass
            else:
                winreg.SetValueEx(k, APP, 0, winreg.REG_SZ, value)
        return True
    except OSError:
        return False


def run_key_value():
    """Lệnh đang ghi trong mục Run (None = không bật khởi động cùng Windows kiểu quyền thường)."""
    if not IS_WIN:
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            return winreg.QueryValueEx(k, APP)[0]
    except OSError:
        return None


def apply_startup(always_admin, autostart):
    """Áp dụng 2 ô "Luôn mở bằng quyền Admin" + "Khởi động cùng Windows". -> câu báo lỗi, hoặc None nếu được"""
    if not IS_WIN:
        return "Chỉ dùng được trên Windows"
    if always_admin:
        if not is_admin():
            return "Cần quyền Admin: bấm \"Chạy bằng Admin\" trước"
        rc, msg = create_task(autostart)
        if rc != 0:
            return f"Không tạo được tác vụ trong Task Scheduler (schtasks lỗi {rc}: {msg})"
        run_key(None)   # tác vụ đã lo phần tự chạy khi đăng nhập (bằng quyền Admin)
        return None
    if task_query() is not None and run_quiet(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]) != 0:
        return "Không xóa được tác vụ cũ (cần quyền Admin): bấm \"Chạy bằng Admin\" rồi làm lại"
    if not run_key(autostart_cmd() if autostart else None):
        return "Không ghi được registry"
    return None


def admin_task_ready(settings):
    """Đã bật "Luôn mở bằng quyền Admin" cho đúng file app này (chuyển app sang thư mục khác thì phải bật lại)."""
    return IS_WIN and settings.get("admin_task") == APP_FILE


def handoff_to_admin(opts, ctl):
    """Bấm đúp mở app (quyền thường) mà đã bật "Luôn mở bằng quyền Admin": nhờ tác vụ mở bản Admin (Windows không
    hỏi gì), bản này thoát. -> "ok" | "no_task" (tác vụ đã bị xóa) | "timeout" (bản Admin không mở lên)"""
    ctl.close()   # nhả cổng điều khiển cho bản Admin
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(HANDOFF_FILE, "w", encoding="utf-8") as f:
            json.dump({"tray": opts.tray, "start": opts.start, "t": time.time()}, f)
    except OSError:
        pass
    try:   # bản này là app người dùng vừa bấm mở -> cho phép cửa sổ bản Admin hiện lên trên cùng
        ctypes.windll.user32.AllowSetForegroundWindow(-1)
    except Exception:
        pass
    status = "no_task"
    if run_quiet(["schtasks", "/Run", "/TN", TASK_NAME]) == 0:
        status = "timeout"
        t = time.monotonic() + 12
        while time.monotonic() < t:
            if send_command("ping"):
                return "ok"
            time.sleep(0.2)
    try:
        os.remove(HANDOFF_FILE)
    except OSError:
        pass
    return status


def read_handoff():
    """(bản Admin do tác vụ mở) -> tùy chọn bản quyền thường gửi sang; None = Windows tự chạy lúc đăng nhập."""
    try:
        with open(HANDOFF_FILE, encoding="utf-8") as f:
            d = json.load(f)
        os.remove(HANDOFF_FILE)
        return d if abs(time.time() - float(d["t"])) < 60 else None
    except (OSError, ValueError, TypeError, KeyError):
        return None


def open_firewall(port):
    """Cho máy chủ kết nối vào cổng của máy khách (chỉ nhận từ mạng LAN). -> (thành công?, câu báo)"""
    if not IS_WIN:
        return False, "Chỉ dùng được trên Windows"
    if not is_admin():
        return False, "Cần quyền Admin: bấm \"Chạy bằng Admin\" trước"
    run_quiet(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={APP}"])
    rc = run_quiet(["netsh", "advfirewall", "firewall", "add", "rule", f"name={APP}", "dir=in", "action=allow",
                    "protocol=TCP", f"localport={port}", "remoteip=localsubnet", "profile=any"])
    return (True, f"Đã mở cổng {port} trên tường lửa Windows (chỉ cho máy trong mạng LAN)") if rc == 0 else \
        (False, f"Không mở được tường lửa (netsh lỗi {rc})")


def relaunch_as_admin(extra=""):
    if not IS_WIN:
        return False
    try:
        exe, args = app_launch(extra)
        r = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, args, HERE, 1)
        return r > 32
    except Exception:
        return False


def hide_own_console():
    """Lỡ mở bằng python.exe: ẩn cửa sổ CMD nếu nó là của riêng app này (không ẩn CMD bạn đang gõ lệnh)."""
    if not IS_WIN:
        return
    try:
        k32 = ctypes.windll.kernel32
        hwnd = k32.GetConsoleWindow()
        if hwnd:
            arr = (ctypes.c_uint32 * 8)()
            if k32.GetConsoleProcessList(arr, 8) <= 1:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def local_ips():
    ips = set()
    try:
        ips.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))   # không gửi gói nào, chỉ để biết IP LAN
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    return sorted(ip for ip in ips if not ip.startswith("127."))


# ------------------------------- chạy kvm.py ẩn -------------------------------
class Runner:
    """Chạy kvm.py --gui (không cửa sổ CMD), đọc log + trạng thái "@@KVM {json}" qua pipe."""

    def __init__(self, out):
        self.out, self.p, self.stopping = out, None, False

    @property
    def running(self):
        return self.p is not None and self.p.poll() is None

    def start(self, role):
        roles = [role] if role in ("master", "client") else []
        args = [python_exe(), "-u", KVM_PATH] + roles + ["--gui"]
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        self.stopping = False
        self.p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  cwd=HERE, env=env, creationflags=CREATE_NO_WINDOW)
        threading.Thread(target=self._read, args=(self.p,), daemon=True).start()

    def _read(self, p):
        for raw in iter(p.stdout.readline, b""):
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            if line.startswith("@@KVM "):
                try:
                    self.out.put(("ev", json.loads(line[6:])))
                    continue
                except ValueError:
                    pass
            if line:
                self.out.put(("log", line))
        self.out.put(("exit", (p, p.wait())))

    def stop(self):
        """Báo kvm thoát êm (client trả lại cài đặt chuột, nhả phím); 3 giây chưa thoát thì tắt hẳn."""
        p = self.p
        if p is None or p.poll() is not None:
            return
        self.stopping = True
        try:
            p.stdin.write(b"quit\n")
            p.stdin.flush()
        except OSError:
            pass

        def waiter():
            try:
                p.wait(3)
            except subprocess.TimeoutExpired:
                p.kill()

        threading.Thread(target=waiter, daemon=True).start()


# ------------------------------- hình vẽ: màn hình, thùng rác -------------------------------
def draw_monitor(cv, cx, cy, s=1.0, master=False, tags=()):
    """Biểu tượng màn hình nhiều màu giống Deskflow; master tông xanh dương."""
    w, h = 76 * s, 50 * s
    x0, y0 = cx - w / 2, cy - h / 2
    cv.create_rectangle(x0 - 4 * s, y0 - 4 * s, x0 + w + 4 * s, y0 + h + 4 * s, fill="#141414", outline="#0b0b0b",
                        tags=tags)
    c = ("#5aa0e6", "#3577c4", "#6f63d0", "#3fb4c9") if master else ("#a9c75b", "#4cb6a6", "#6c80c6", "#d8a95c")
    mid = x0 + w * 0.56
    cv.create_polygon(x0, y0, mid, y0, x0, y0 + h, fill=c[0], outline="", tags=tags)
    cv.create_polygon(mid, y0, x0 + w, y0, x0 + w, y0 + h, fill=c[2], outline="", tags=tags)
    cv.create_polygon(mid, y0, x0 + w, y0 + h, x0, y0 + h, fill=c[1], outline="", tags=tags)
    cv.create_polygon(x0, y0 + h * 0.58, x0 + w * 0.32, y0 + h, x0, y0 + h, fill=c[3], outline="", tags=tags)
    cv.create_rectangle(cx - 7 * s, y0 + h + 4 * s, cx + 7 * s, y0 + h + 11 * s, fill="#b9b9b9", outline="",
                        tags=tags)
    cv.create_rectangle(cx - 19 * s, y0 + h + 11 * s, cx + 19 * s, y0 + h + 15 * s, fill="#dcdcdc", outline="",
                        tags=tags)


def draw_trash(cv, cx, cy, s=1.0, hot=False):
    col = ERR_C if hot else "#c4c4c4"
    cv.create_rectangle(cx - 19 * s, cy - 21 * s, cx + 19 * s, cy - 16 * s, fill=col, outline="", tags="trash")
    cv.create_rectangle(cx - 6 * s, cy - 25 * s, cx + 6 * s, cy - 21 * s, fill=col, outline="", tags="trash")
    cv.create_polygon(cx - 16 * s, cy - 13 * s, cx + 16 * s, cy - 13 * s, cx + 13 * s, cy + 23 * s,
                      cx - 13 * s, cy + 23 * s, fill=col, outline="", tags="trash")
    for dx in (-8, 0, 8):
        cv.create_rectangle(cx + (dx - 2) * s, cy - 8 * s, cx + (dx + 2) * s, cy + 18 * s, fill="#3a3a3a",
                            outline="", tags="trash")


def center(win, parent=None):
    """Đặt cửa sổ giữa cửa sổ cha (hoặc giữa màn hình)."""
    win.update_idletasks()
    w, h = win.winfo_reqwidth(), win.winfo_reqheight()
    if parent is not None and parent.winfo_viewable():
        x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 3
    else:
        x, y = (win.winfo_screenwidth() - w) // 2, (win.winfo_screenheight() - h) // 3
    win.geometry(f"+{max(0, x)}+{max(0, y)}")


def safe_grab(win):
    """Chặn bấm vào cửa sổ phía sau (cửa sổ chưa hiện kịp thì thử lại)."""
    try:
        if win.winfo_exists():
            win.grab_set()
    except tk.TclError:
        win.after(60, lambda: safe_grab(win))


def dialog_buttons(win, ok, cancel, ok_text="OK"):
    bar = ttk.Frame(win, padding=(12, 8, 12, 12))
    bar.pack(side="bottom", fill="x")
    ttk.Button(bar, text="Hủy", command=cancel).pack(side="right")
    ttk.Button(bar, text=ok_text, style="Accent.TButton", command=ok).pack(side="right", padx=(0, 8))
    win.bind("<Escape>", lambda e: cancel())
    return bar


class PcDialog(tk.Toplevel):
    """Thêm / sửa 1 máy: IP (hoặc tên máy trong mạng LAN), tên hiển thị, có đồng bộ không."""

    def __init__(self, parent, title, ip="", name="", sync=True, taken=()):
        super().__init__(parent)
        self.result, self.taken = None, set(taken)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        body = ttk.Frame(self, padding=(16, 14, 16, 4))
        body.pack(fill="both", expand=True)
        self.ip, self.name, self.sync = tk.StringVar(value=ip), tk.StringVar(value=name), tk.BooleanVar(value=sync)
        ttk.Label(body, text="IP của máy (vd 192.168.1.102):").grid(row=0, column=0, sticky="w")
        e = ttk.Entry(body, textvariable=self.ip, width=32)
        e.grid(row=1, column=0, sticky="we", pady=(2, 10))
        ttk.Label(body, text="Tên hiển thị (tùy chọn):").grid(row=2, column=0, sticky="w")
        ttk.Entry(body, textvariable=self.name, width=32).grid(row=3, column=0, sticky="we", pady=(2, 10))
        ttk.Checkbutton(body, text="Làm theo khi ĐỒNG BỘ (Scroll Lock bật)", variable=self.sync).grid(
            row=4, column=0, sticky="w")
        self.err = ttk.Label(body, text="", style="Err.TLabel")
        self.err.grid(row=5, column=0, sticky="w", pady=(8, 0))
        dialog_buttons(self, self._ok, self.destroy)
        self.bind("<Return>", lambda ev: self._ok())
        center(self, parent)
        e.focus_set()
        e.icursor("end")
        safe_grab(self)
        self.wait_window()

    def _ok(self):
        ip, name = self.ip.get().strip(), self.name.get().strip()
        err = host_error(ip)
        if err:
            self.err.configure(text=err)
            return
        if ip in self.taken:
            self.err.configure(text="IP này đã có trong bố cục")
            return
        self.result = {"ip": ip, "name": name or ip, "sync": self.sync.get()}
        self.destroy()


class ServerConfig(tk.Toplevel):
    """Cấu hình máy chủ kiểu Deskflow: kéo thả các máy trên lưới + nâng cao."""

    def __init__(self, app, cfg, names):
        super().__init__(app.root)
        self.app, self.cfg, self.s = app, dict(cfg), app.scale
        self.title("Cấu hình máy chủ - MiniKVM")
        self.configure(bg=BG)
        self.transient(app.root)
        self.cw, self.ch = int(150 * self.s), int(138 * self.s)
        self.drag = self.drag_new = None
        self.hl_cell, self.trash_hot = None, False
        self._load_layout(cfg, names)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=(12, 0))
        self.nb = nb
        self._tab_computers(nb)
        self._tab_advanced(nb)
        dialog_buttons(self, self._ok, self.destroy, "OK")
        self._redraw()
        center(self, app.root)
        safe_grab(self)

    # ---------- dữ liệu ----------
    def _load_layout(self, cfg, names):
        t = cfg["ipTable"]
        rows, cols = len(t), max(len(r) for r in t)
        self.rows, self.cols = max(3, rows), max(5, cols)
        r0, c0 = (self.rows - rows) // 2, (self.cols - cols) // 2
        sync = cfg["SYNC_IPS"]
        self.cells = {}
        for r, row in enumerate(t):
            for c, v in enumerate(row):
                if v == "MASTER":
                    self.cells[(r0 + r, c0 + c)] = {"master": True, "ip": "MASTER", "name": "MASTER", "sync": True}
                elif v:
                    self.cells[(r0 + r, c0 + c)] = {"ip": v, "name": names.get(v, v),
                                                    "sync": sync is None or v in sync}
        ips = {d["ip"] for d in self.cells.values()}
        self.extra_sync = [ip for ip in (sync or ()) if ip not in ips]

    def _collect(self):
        """Trạng thái hộp thoại -> (cấu hình, tên) ; lỗi -> ValueError."""
        occ = sorted(self.cells)
        r0, r1 = min(r for r, c in occ), max(r for r, c in occ)
        c0, c1 = min(c for r, c in occ), max(c for r, c in occ)
        table = [[self.cells[(r, c)]["ip"] if (r, c) in self.cells else None for c in range(c0, c1 + 1)]
                 for r in range(r0, r1 + 1)]
        pcs = [d for d in self.cells.values() if not d.get("master")]
        extra = [x.strip() for x in self.extra_var.get().replace(";", ",").split(",") if x.strip()]
        for x in extra:
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", x):
                raise ValueError(f"IP chỉ đồng bộ không hợp lệ: {x}")
        if all(d["sync"] for d in pcs) and not extra:
            sync = None
        else:
            sync = [d["ip"] for d in pcs if d["sync"]] + [x for x in extra if x not in {d["ip"] for d in pcs}]
        try:
            port = int(self.port_var.get())
        except ValueError:
            raise ValueError("Cổng phải là số từ 1 đến 65535")
        cfg = dict(self.cfg, ipTable=table, SYNC_IPS=sync, PORT=port, RAW_MOUSE=self.raw_var.get(),
                   MOUSE_LIKE_MASTER=self.like_var.get())
        err = validate(cfg)
        if err:
            raise ValueError(err)
        names = {d["ip"]: d["name"] for d in pcs}
        return cfg, names

    def _ok(self):
        try:
            cfg, names = self._collect()
            save_config(cfg, names)
        except (ValueError, OSError) as e:
            messagebox.showerror("Cấu hình chưa đúng", str(e), parent=self)
            return
        self.destroy()
        self.app.on_config_saved(cfg, names)

    # ---------- tab Máy tính (kéo thả như Deskflow) ----------
    def _tab_computers(self, nb):
        s = self.s
        tab = ttk.Frame(nb, padding=8)
        nb.add(tab, text="Máy tính")
        head = tk.Frame(tab, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        head.pack(fill="x")
        self.trash = tk.Canvas(head, width=int(66 * s), height=int(66 * s), bg=PANEL, highlightthickness=1,
                               highlightbackground=BORDER, cursor="X_cursor")
        self.trash.pack(side="left", padx=6, pady=6)
        self.newpc = tk.Canvas(head, width=int(66 * s), height=int(66 * s), bg=PANEL, highlightthickness=1,
                               highlightbackground=BORDER, cursor="hand2")
        self.newpc.pack(side="right", padx=6, pady=6)
        draw_monitor(self.newpc, 33 * s, 27 * s, 0.62 * s)
        self.newpc.create_text(53 * s, 12 * s, text="+", fill=OK_C, font=(self.app.family, 14, "bold"))
        tk.Label(head, text="Kéo thả các máy vào đúng vị trí như màn hình đặt trên bàn.\n"
                            "Kéo máy mới (góc phải) vào ô trống để thêm · kéo vào thùng rác để xóa.",
                 bg=PANEL, fg=FG, font=self.app.f_norm, justify="center").pack(expand=True, pady=10)
        self.cv = tk.Canvas(tab, width=self.cols * self.cw + 1, height=self.rows * self.ch + 1, bg=CELL,
                            highlightthickness=0)
        self.cv.pack(pady=(8, 4))
        ttk.Label(tab, text="Bấm đúp: thêm / sửa máy   ·   Chuột phải: bật/tắt đồng bộ, xóa   ·   "
                            "Máy ghi \"không đồng bộ\" sẽ không làm theo khi bật Scroll Lock",
                  style="Muted.TLabel").pack()
        self.cv.bind("<ButtonPress-1>", self._press)
        self.cv.bind("<B1-Motion>", self._motion)
        self.cv.bind("<ButtonRelease-1>", self._release)
        self.cv.bind("<Double-Button-1>", self._double)
        self.cv.bind("<Button-3>", self._menu)
        self.newpc.bind("<ButtonPress-1>", lambda e: setattr(self, "drag_new", True))
        self.newpc.bind("<B1-Motion>", self._new_motion)
        self.newpc.bind("<ButtonRelease-1>", self._new_release)

    def _draw_trash(self, hot):
        self.trash.delete("all")
        draw_trash(self.trash, 33 * self.s, 33 * self.s, 0.95 * self.s, hot)
        self.trash_hot = hot

    def _redraw(self):
        cv, cw, ch = self.cv, self.cw, self.ch
        cv.delete("all")
        for r in range(self.rows):
            for c in range(self.cols):
                cv.create_rectangle(c * cw, r * ch, (c + 1) * cw, (r + 1) * ch, fill=CELL, outline=GRID,
                                    tags=("cell", f"cell_{r}_{c}"))
        for (r, c), d in self.cells.items():
            self._draw_tile(r, c, d)
        self._draw_trash(False)
        self.hl_cell = None

    def _draw_tile(self, r, c, d):
        cv, s = self.cv, self.s
        cx, cy = c * self.cw + self.cw / 2, r * self.ch + 44 * s
        tag = ("tile", f"tile_{r}_{c}")
        if d.get("master"):
            cv.create_rectangle(c * self.cw + 3, r * self.ch + 3, (c + 1) * self.cw - 3, (r + 1) * self.ch - 3,
                                outline=ACCENT, width=2, tags=tag)
        draw_monitor(cv, cx, cy, s, d.get("master", False), tag)
        if d.get("master"):
            lines = [("MASTER", FG, self.app.f_bold), ("(máy này)", MUTED, self.app.f_small)]
        else:
            name = d["name"] if len(d["name"]) <= 18 else d["name"][:17] + "…"
            lines = [(name, FG, self.app.f_bold)]
            if d["name"] != d["ip"]:
                lines.append((d["ip"], MUTED, self.app.f_small))
            if not d["sync"]:
                lines.append(("không đồng bộ", WARN_C, self.app.f_small))
        for (text, color, font), dy in zip(lines, (49, 65, 80)):
            cv.create_text(cx, cy + dy * s, text=text, fill=color, font=font, tags=tag)

    def _cell_at(self, x, y):
        c, r = int(x // self.cw), int(y // self.ch)
        return (r, c) if 0 <= r < self.rows and 0 <= c < self.cols and x >= 0 and y >= 0 else None

    def _highlight(self, cell):
        if cell == self.hl_cell:
            return
        self.cv.delete("hl")
        self.hl_cell = cell
        if cell:
            r, c = cell
            self.cv.create_rectangle(c * self.cw + 2, r * self.ch + 2, (c + 1) * self.cw - 2, (r + 1) * self.ch - 2,
                                     outline=ACCENT_HI, width=3, dash=(6, 4), tags="hl")

    def _over(self, w, xr, yr):
        x, y = w.winfo_rootx(), w.winfo_rooty()
        return x <= xr < x + w.winfo_width() and y <= yr < y + w.winfo_height()

    def _press(self, e):
        cell = self._cell_at(e.x, e.y)
        if cell in self.cells:
            self.drag = {"from": cell, "x": e.x, "y": e.y, "moved": False}
            self.cv.tag_raise(f"tile_{cell[0]}_{cell[1]}")

    def _motion(self, e):
        d = self.drag
        if not d:
            return
        r, c = d["from"]
        self.cv.move(f"tile_{r}_{c}", e.x - d["x"], e.y - d["y"])
        d["x"], d["y"], d["moved"] = e.x, e.y, True
        hot = self._over(self.trash, e.x_root, e.y_root) and not self.cells[d["from"]].get("master")
        if hot != self.trash_hot:
            self._draw_trash(hot)
        self._highlight(None if hot else self._cell_at(e.x, e.y))

    def _release(self, e):
        d, self.drag = self.drag, None
        if not d:
            return
        src = d["from"]
        if self._over(self.trash, e.x_root, e.y_root):
            self._delete(src)
        elif d["moved"]:
            dst = self._cell_at(e.x, e.y)
            if dst and dst != src:   # ô trống: chuyển sang; có máy: đổi chỗ 2 máy
                a, b = self.cells.pop(src), self.cells.pop(dst, None)
                self.cells[dst] = a
                if b:
                    self.cells[src] = b
        self._redraw()

    def _new_motion(self, e):
        if not self.drag_new:
            return
        x, y = e.x_root - self.cv.winfo_rootx(), e.y_root - self.cv.winfo_rooty()
        cell = self._cell_at(x, y)
        self._highlight(cell if cell and cell not in self.cells else None)
        self.cv.delete("ghost")   # máy mới đi theo con trỏ khi kéo vào lưới
        if cell:
            draw_monitor(self.cv, x, y, 0.8 * self.s, tags=("ghost",))

    def _new_release(self, e):
        if not self.drag_new:
            return
        self.drag_new = None
        self.cv.delete("ghost")
        x, y = e.x_root - self.cv.winfo_rootx(), e.y_root - self.cv.winfo_rooty()
        cell = self._cell_at(x, y)
        self._highlight(None)
        if cell and cell not in self.cells:
            self._add(cell)

    def _double(self, e):
        cell = self._cell_at(e.x, e.y)
        if cell is None:
            return
        if cell in self.cells:
            self._edit(cell)
        else:
            self._add(cell)

    def _taken(self, skip=None):
        return [d["ip"] for k, d in self.cells.items() if k != skip and not d.get("master")]

    def _add(self, cell):
        dlg = PcDialog(self, "Thêm máy", taken=self._taken())
        if dlg.result:
            self.cells[cell] = dlg.result
        self._redraw()
        safe_grab(self)   # hộp thoại con đóng thì Tk bỏ chặn -> chặn lại

    def _edit(self, cell):
        d = self.cells[cell]
        if d.get("master"):
            messagebox.showinfo("MASTER", "Đây là máy chủ (máy đang chạy app này). Kéo để đổi vị trí so với các "
                                          "máy khác.", parent=self)
            return
        dlg = PcDialog(self, "Sửa máy", d["ip"], d["name"], d["sync"], taken=self._taken(cell))
        if dlg.result:
            self.cells[cell] = dlg.result
        self._redraw()
        safe_grab(self)

    def _delete(self, cell):
        if self.cells.get(cell, {}).get("master"):
            messagebox.showwarning("Không xóa được", "Không xóa được MASTER (máy chủ).", parent=self)
            return
        self.cells.pop(cell, None)

    def _toggle_sync(self, cell):
        self.cells[cell]["sync"] = not self.cells[cell]["sync"]
        self._redraw()

    def _menu(self, e):
        cell = self._cell_at(e.x, e.y)
        if cell is None:
            return
        m = tk.Menu(self, tearoff=0, bg=PANEL, fg=FG, activebackground=SEL, activeforeground=FG, bd=0)
        d = self.cells.get(cell)
        if d is None:
            m.add_command(label="Thêm máy ở đây…", command=lambda: self._add(cell))
        elif d.get("master"):
            m.add_command(label="MASTER (máy chủ) - kéo để đổi vị trí", state="disabled")
        else:
            m.add_command(label="Sửa…", command=lambda: self._edit(cell))
            m.add_command(label=("✓ " if d["sync"] else "    ") + "Làm theo khi đồng bộ",
                          command=lambda: self._toggle_sync(cell))
            m.add_separator()
            m.add_command(label="Xóa", command=lambda: (self._delete(cell), self._redraw()))
        m.tk_popup(e.x_root, e.y_root)

    # ---------- tab Nâng cao ----------
    def _tab_advanced(self, nb):
        tab = ttk.Frame(nb, padding=16)
        nb.add(tab, text="Nâng cao")
        self.port_var = tk.StringVar(value=str(self.cfg["PORT"]))
        self.raw_var = tk.BooleanVar(value=self.cfg["RAW_MOUSE"])
        self.like_var = tk.BooleanVar(value=self.cfg["MOUSE_LIKE_MASTER"])
        self.extra_var = tk.StringVar(value=", ".join(self.extra_sync))
        g = ttk.Frame(tab)
        g.pack(fill="x")
        ttk.Label(g, text="Cổng TCP (mọi máy phải giống nhau):").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Spinbox(g, from_=1, to=65535, textvariable=self.port_var, width=8).grid(row=0, column=1, sticky="w",
                                                                                    padx=12)
        ttk.Label(g, text="Máy CHỈ đồng bộ (không có trong bố cục), cách nhau dấu phẩy:").grid(
            row=1, column=0, sticky="w", pady=6)
        ttk.Entry(g, textvariable=self.extra_var, width=34).grid(row=1, column=1, sticky="w", padx=12)
        ttk.Separator(tab).pack(fill="x", pady=12)
        ttk.Checkbutton(tab, text="Chuyển máy bằng chuyển động chuột gốc (raw)", variable=self.raw_var,
                        command=self._raw_changed).pack(anchor="w", pady=(3, 0))
        ttk.Label(tab, text="Chỉ bật khi chơi game xoay camera bằng chuột trên máy khác (vd CS2, GTA; Valorant "
                            "thường không nhận). Máy khách bận thì có thể bị trễ.",
                  style="Muted.TLabel").pack(anchor="w", padx=(26, 0))
        self.like_cb = ttk.Checkbutton(tab, text="Máy khách dùng tạm tốc độ chuột của máy chủ (khi bật raw)",
                                       variable=self.like_var)
        self.like_cb.pack(anchor="w", padx=(26, 0), pady=(6, 0))
        self._raw_changed()
        ttk.Label(tab, style="Muted.TLabel", justify="left",
                  text="Máy khách tự chỉnh IP máy chủ, cổng và thời gian chờ click ngay trên cửa sổ MiniKVM "
                       "của máy đó.").pack(anchor="w", pady=(18, 0))

    def _raw_changed(self):
        self.like_cb.state(["!disabled"] if self.raw_var.get() else ["disabled"])


# ------------------------------- cài đặt riêng của app (%APPDATA%\MiniKVM\gui.json) -------------------------------
def load_settings():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(d):
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        tmp = SETTINGS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tmp, SETTINGS_FILE)
    except OSError:
        pass


def write_error(text):
    """Lỗi của app ghi vào %APPDATA%\\MiniKVM\\loi.txt (app chạy ẩn, không có CMD để xem)."""
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(os.path.join(os.path.dirname(SETTINGS_FILE), "loi.txt"), "a", encoding="utf-8") as f:
            f.write(time.strftime("=== %Y-%m-%d %H:%M:%S\n") + text.rstrip() + "\n")
    except OSError:
        pass


def guess_role(cfg):
    """Giống kvm.py: IP máy này có trong bố cục -> máy khách, không thì máy chủ."""
    return "client" if set(local_ips()) & {ip for ip, _ in peers_of(cfg)} else "master"


# ------------------------------- chỉ chạy 1 app: mở lần 2 thì hiện app đang chạy -------------------------------
class Control:
    def __init__(self, q):
        self.q, self.sock = q, None

    def listen(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if not IS_WIN:   # (Windows: KHÔNG đặt cờ này, nếu không 2 app cùng giữ được 1 cổng)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", CONTROL_PORT))
            s.listen(4)
        except OSError:
            s.close()
            return False
        self.sock = s
        threading.Thread(target=self._loop, args=(s,), name="control", daemon=True).start()
        return True

    def _loop(self, s):
        while True:
            try:
                c, _ = s.accept()
            except OSError:
                return
            try:
                c.settimeout(2.0)
                cmd = c.recv(64).decode("ascii", "replace").strip().lower()
                c.sendall(b"MiniKVM\n")
                self.q.put(("cmd", cmd))
                c.recv(16)   # chờ bên kia đóng trước: cổng của app không bị kẹt lại sau khi thoát
            except OSError:
                pass
            finally:
                c.close()

    def close(self):
        s, self.sock = self.sock, None
        if s is not None:
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            s.close()


def send_command(cmd):
    """Gửi lệnh cho MiniKVM đang chạy (show / quit / ping). -> True nếu có app trả lời."""
    try:
        with socket.create_connection(("127.0.0.1", CONTROL_PORT), timeout=2.0) as c:
            c.sendall(cmd.encode("ascii") + b"\n")
            return c.recv(16).startswith(b"MiniKVM")
    except OSError:
        return False


# ------------------------------- biểu tượng dưới khay -------------------------------
class Tray:
    """Biểu tượng cạnh đồng hồ (cần pystray + pillow). Màu = trạng thái: xám dừng, xanh lá chạy, xanh dương đồng bộ,
    vàng đang chờ, đỏ lỗi. Bấm trái: mở app; bấm phải: menu."""

    def __init__(self, app):
        self.app, self.icon, self.color, self.tip, self.on = app, None, None, None, None
        try:
            import pystray
            from PIL import Image, ImageDraw
        except Exception as e:
            self.why = f"{type(e).__name__}: {e}"
            return
        self.Image, self.Draw = Image, ImageDraw
        q, M = app.q, pystray.MenuItem
        menu = pystray.Menu(
            M("Mở MiniKVM", lambda *a: q.put(("call", app.show)), default=True),
            M(lambda item: "Dừng kvm" if self.on else "Bắt đầu kvm", lambda *a: q.put(("call", app.toggle_run))),
            pystray.Menu.SEPARATOR,
            M("Thoát", lambda *a: q.put(("call", app.quit))))
        try:
            self.icon = pystray.Icon(APP, self._image(GREY), APP, menu)
        except Exception as e:
            self.why = f"{type(e).__name__}: {e}"
            return
        self.thread = threading.Thread(target=self._run, name="tray", daemon=True)
        self.thread.start()

    @property
    def ok(self):
        return self.icon is not None

    def _run(self):
        try:
            self.icon.run()
        except Exception as e:
            self.icon = None
            self.app.q.put(("log", f"[!] Không hiện được biểu tượng dưới khay: {e}"))

    def _image(self, color):
        img = self.Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = self.Draw.Draw(img)
        d.rectangle((2, 6, 61, 46), fill="#0e0e0e")      # viền màn hình
        d.rectangle((7, 11, 56, 41), fill=color)         # màn hình = màu trạng thái
        d.rectangle((26, 46, 37, 53), fill="#c8c8c8")    # chân
        d.rectangle((14, 53, 49, 59), fill="#ededed")    # đế
        return img

    def set(self, color, tip, on):
        ic = self.icon
        if ic is None:
            return
        tip = tip if len(tip) <= 100 else tip[:99] + "…"   # (Windows giới hạn 127 ký tự)
        todo = []
        if on != self.on:
            self.on = on
            todo.append(ic.update_menu)   # chữ "Bắt đầu" / "Dừng" trong menu
        if color != self.color:
            self.color = color
            todo.append(lambda: setattr(ic, "icon", self._image(color)))
        if tip != self.tip:
            self.tip = tip
            todo.append(lambda: setattr(ic, "title", tip))
        for fn in todo:   # (lỗi 1 việc không làm hỏng việc khác)
            try:
                fn()
            except Exception:
                pass

    def notify(self, msg):
        if self.icon is not None:
            try:
                self.icon.notify(msg[:200], APP)
            except Exception:
                pass

    def stop(self):
        if self.icon is not None:
            try:
                self.icon.stop()
                self.thread.join(1.5)   # chờ gỡ biểu tượng xong (không để lại biểu tượng "ma" dưới khay)
            except Exception:
                pass


# ------------------------------- cửa sổ chính -------------------------------
class App:
    def __init__(self, opts, q, ctl):
        self.opts, self.q, self.ctl = opts, q, ctl
        self.runner = Runner(q)
        self.settings = load_settings()
        self.cfg, self.names, self.cfg_err = load_config()
        self.cfg_mtime = self._cfg_mtime()
        self.kvm, self.last_error, self.run_role = {}, None, None   # kvm: trạng thái kvm.py đang chạy gửi lên
        self.started_t, self.crashes = 0.0, []
        self.restart_after = self.quitting = self.dead = False
        self.cfg_win = self._poll_id = self._tick_id = None
        self.ips = local_ips()
        self.admin = is_admin()
        self.logf = self._open_logfile()

        self.root = root = tk.Tk(className=APP)
        root.withdraw()
        self.scale = max(1.0, root.winfo_fpixels("1i") / 96.0)
        self._fonts()
        self._style()
        self._window_icon()
        role = self.settings.get("role")
        self.role = tk.StringVar(value=role if role in ROLE_NAME else guess_role(self.cfg))
        self.auto_run = tk.BooleanVar(value=bool(self.settings.get("auto_run", True)))
        self.close_tray = tk.BooleanVar(value=bool(self.settings.get("close_to_tray", True)))
        self.autostart = tk.BooleanVar(value=False)
        self.admin_mode = tk.BooleanVar(value=admin_task_ready(self.settings))   # "Luôn mở bằng quyền Admin"
        self.master_ip, self.c_port, self.c_settle = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.any_master = tk.BooleanVar()   # máy khách: nhận kết nối từ mọi máy chủ (IP trong ô vẫn giữ)
        self._client_vars(force=True)
        self.tray = Tray(self)
        self._build()

    # ---------- giao diện ----------
    def _fonts(self):
        fams = set(tkfont.families(self.root))

        def pick(*names):
            return next((n for n in names if n in fams), names[-1])

        self.family = pick("Segoe UI", "DejaVu Sans", "Liberation Sans", "Arial")
        mono = pick("Cascadia Mono", "Consolas", "DejaVu Sans Mono", "Liberation Mono", "Courier New")
        for n in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont", "TkTooltipFont"):
            try:
                tkfont.nametofont(n).configure(family=self.family, size=10)
            except tk.TclError:
                pass
        self.f_norm, self.f_bold = (self.family, 10), (self.family, 10, "bold")
        self.f_small, self.f_head, self.f_mono = (self.family, 9), (self.family, 13, "bold"), (mono, 9)

    def _style(self):
        r, s = self.root, self.scale
        st = ttk.Style(r)
        st.theme_use("clam")
        st.configure(".", background=BG, foreground=FG, fieldbackground=FIELD, bordercolor=BORDER, darkcolor=BG,
                     lightcolor=BG, troughcolor=FIELD, focuscolor=ACCENT, selectbackground=SEL,
                     selectforeground=FG, insertcolor=FG, arrowcolor=FG, font=self.f_norm)
        st.map(".", foreground=[("disabled", "#6f6f6f")])
        st.configure("TLabel", background=BG, foreground=FG)
        st.configure("Muted.TLabel", foreground=MUTED, font=self.f_small)
        st.configure("Err.TLabel", foreground=ERR_C)
        st.configure("Warn.TLabel", foreground=WARN_C)
        st.configure("Ok.TLabel", foreground=OK_C)
        st.configure("Bold.TLabel", font=self.f_bold)
        btn = dict(background="#454545", foreground=FG, bordercolor="#5a5a5a", lightcolor="#4c4c4c",
                   darkcolor="#3c3c3c", padding=(12, 4), focusthickness=1)
        st.configure("TButton", **btn)
        st.map("TButton", background=[("disabled", "#383838"), ("pressed", "#2f2f2f"), ("active", "#525252")],
               foreground=[("disabled", "#777777")])
        for name, c, hi, lo in (("Accent", ACCENT, ACCENT_HI, "#2f75ad"), ("Stop", "#b04a4a", "#c95a5a", "#8f3a3a")):
            st.configure(f"{name}.TButton", background=c, foreground="white", bordercolor=c, lightcolor=c, darkcolor=c,
                         padding=(16, 6), font=self.f_bold)
            st.map(f"{name}.TButton", background=[("disabled", "#3f4a55"), ("pressed", lo), ("active", hi)],
                   lightcolor=[("active", hi)], darkcolor=[("active", hi)])
        st.configure("Small.TButton", padding=(8, 1), font=self.f_small)
        for w in ("TCheckbutton", "TRadiobutton"):
            st.configure(w, background=BG, foreground=FG, indicatorbackground=FIELD, indicatorforeground="white",
                         upperbordercolor=BORDER, lowerbordercolor=BORDER, focuscolor=BG)
            st.map(w, background=[("active", BG)],
                   indicatorbackground=[("disabled", BG), ("selected", ACCENT), ("pressed", SEL)])
        try:   # ô tick có dấu ✓ (giao diện "clam" mặc định vẽ dấu ✕ dễ hiểu nhầm là "không")
            on, off, d_on, d_off = self._check_imgs = self._make_checks()
            st.element_create("Mk.Checkbutton.indicator", "image", off, ("disabled", "selected", d_on),
                              ("disabled", d_off), ("selected", on), sticky="", padding=(0, 0, int(7 * s), 0))
            st.layout("TCheckbutton", [("Checkbutton.padding", {"sticky": "nswe", "children": [
                ("Mk.Checkbutton.indicator", {"side": "left", "sticky": ""}),
                ("Checkbutton.focus", {"side": "left", "sticky": "w", "children": [
                    ("Checkbutton.label", {"sticky": "nswe"})]})]})])
        except tk.TclError:
            pass
        st.configure("TEntry", fieldbackground=FIELD, foreground=FG, insertcolor=FG, padding=4)
        st.map("TEntry", bordercolor=[("focus", ACCENT)], fieldbackground=[("disabled", BG)])
        for w in ("TCombobox", "TSpinbox"):
            st.configure(w, fieldbackground=FIELD, background="#454545", foreground=FG, arrowcolor=FG, padding=3)
            st.map(w, fieldbackground=[("readonly", FIELD), ("disabled", BG)], bordercolor=[("focus", ACCENT)],
                   selectbackground=[("readonly", FIELD)], selectforeground=[("readonly", FG)])
        r.option_add("*TCombobox*Listbox.background", FIELD)
        r.option_add("*TCombobox*Listbox.foreground", FG)
        r.option_add("*TCombobox*Listbox.selectBackground", SEL)
        r.option_add("*TCombobox*Listbox.selectForeground", FG)
        r.option_add("*TCombobox*Listbox.font", f"{{{self.family}}} 10")
        st.configure("TNotebook", background=BG, bordercolor=BORDER, tabmargins=(2, 4, 2, 0))
        st.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(16, 6), bordercolor=BORDER,
                     lightcolor=PANEL)
        st.map("TNotebook.Tab", background=[("selected", BG)], foreground=[("selected", FG)],
               lightcolor=[("selected", BG)])
        st.configure("Treeview", background=FIELD, fieldbackground=FIELD, foreground=FG, bordercolor=BORDER,
                     rowheight=int(26 * s))
        st.map("Treeview", background=[("selected", SEL)], foreground=[("selected", FG)])
        st.configure("Treeview.Heading", background=PANEL, foreground=MUTED, bordercolor=BORDER, lightcolor=PANEL,
                     darkcolor=PANEL, relief="flat", padding=(6, 4))
        st.map("Treeview.Heading", background=[("active", "#404040")])
        st.configure("TLabelframe", background=BG, bordercolor=BORDER, lightcolor=BG, darkcolor=BG)
        st.configure("TLabelframe.Label", background=BG, foreground=MUTED, font=self.f_bold)
        st.configure("TSeparator", background=BORDER)
        st.configure("Vertical.TScrollbar", background="#4a4a4a", troughcolor=FIELD, bordercolor=FIELD,
                     arrowcolor=FG, lightcolor="#4a4a4a", darkcolor="#4a4a4a", gripcount=0)

    def _make_checks(self):
        n = max(13, int(round(14 * self.scale)))
        t = max(2, n // 6)

        def make(fill, border, mark):
            img = tk.PhotoImage(master=self.root, width=n, height=n)
            img.put(border, to=(0, 0, n, n))
            img.put(fill, to=(1, 1, n - 1, n - 1))
            if mark:
                pts = ((0.20, 0.50), (0.42, 0.72), (0.80, 0.28))
                for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                    for i in range(2 * n + 1):
                        x = int((x0 + (x1 - x0) * i / (2 * n)) * n - t / 2)
                        y = int((y0 + (y1 - y0) * i / (2 * n)) * n - t / 2)
                        x, y = max(1, min(x, n - 1 - t)), max(1, min(y, n - 1 - t))
                        img.put(mark, to=(x, y, x + t, y + t))
            return img

        return (make(ACCENT, ACCENT, "#ffffff"), make(FIELD, "#767676", None),
                make("#3f5468", "#3f5468", "#aab6c1"), make(BG, "#505050", None))

    def _window_icon(self):
        try:
            img = tk.PhotoImage(width=32, height=32)
            img.put("#0e0e0e", to=(1, 3, 31, 24))
            img.put(ACCENT, to=(4, 6, 28, 21))
            img.put("#c8c8c8", to=(13, 24, 19, 27))
            img.put("#ededed", to=(7, 27, 25, 30))
            self.root.iconphoto(True, img)
            self._icon_img = img
        except tk.TclError:
            pass

    def _build(self):
        root, s = self.root, self.scale
        root.title(f"{APP} - dùng chung chuột & bàn phím")
        root.configure(bg=BG)
        root.minsize(int(700 * s), int(560 * s))
        size = self.settings.get("size")
        w, h = (int(860 * s), int(720 * s))
        if isinstance(size, str) and re.fullmatch(r"\d{3,5}x\d{3,5}", size):
            w, h = (int(v) for v in size.split("x"))
        w, h = min(w, root.winfo_screenwidth()), min(h, root.winfo_screenheight() - 60)
        root.geometry(f"{w}x{h}+{max(0, (root.winfo_screenwidth() - w) // 2)}"
                      f"+{max(0, (root.winfo_screenheight() - h) // 3)}")
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.report_callback_exception = self._report
        main = ttk.Frame(root, padding=(14, 12, 14, 12))
        main.pack(fill="both", expand=True)
        self._build_status(main)
        self._build_role(main)
        self._build_info(main)
        self._build_options(main)   # (xếp từ dưới lên trước để nhật ký chiếm phần còn lại)
        self._build_log(main)
        self._build_peers(main)
        self._build_client(main)

    def _build_status(self, main):
        s = self.scale
        top = tk.Frame(main, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        top.pack(fill="x")
        d = int(16 * s)
        self.dot = tk.Canvas(top, width=d + 4, height=d + 4, bg=PANEL, highlightthickness=0)
        self.dot.pack(side="left", padx=(16, 8))
        self.btn_run = ttk.Button(top, text="Bắt đầu", style="Accent.TButton", width=9, command=self.toggle_run)
        self.btn_run.pack(side="right", padx=16, pady=14)
        box = tk.Frame(top, bg=PANEL)
        box.pack(side="left", fill="both", expand=True, pady=10)
        self.st_title = tk.Label(box, bg=PANEL, fg=FG, font=self.f_head, anchor="w", justify="left")
        self.st_title.pack(fill="x")
        self.st_sub = tk.Label(box, bg=PANEL, fg=MUTED, font=self.f_norm, anchor="w", justify="left")
        self.st_sub.pack(fill="x")
        box.bind("<Configure>", lambda e: (self.st_title.configure(wraplength=max(100, e.width - 8)),
                                           self.st_sub.configure(wraplength=max(100, e.width - 8))))

    def _build_role(self, main):
        box = ttk.LabelFrame(main, text=" Máy này dùng làm ", padding=(12, 6, 12, 10))
        box.pack(fill="x", pady=(12, 0))
        box.columnconfigure(0, weight=1)
        ttk.Radiobutton(box, text="Máy chủ (Master): dùng chuột + bàn phím của máy này điều khiển các máy khác",
                        variable=self.role, value="master", command=self.on_role).grid(row=0, column=0, sticky="w")
        self.lbl_layout = ttk.Label(box, style="Muted.TLabel")
        self.lbl_layout.grid(row=1, column=0, sticky="w", padx=(24, 0))
        self.btn_cfg = ttk.Button(box, text="Cấu hình máy chủ…", command=self.open_server_config)
        self.btn_cfg.grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))
        ttk.Separator(box).grid(row=2, column=0, columnspan=2, sticky="we", pady=8)
        ttk.Radiobutton(box, text="Máy khách (Client): để máy chủ điều khiển máy này", variable=self.role,
                        value="client", command=self.on_role).grid(row=3, column=0, columnspan=2, sticky="w")
        f = ttk.Frame(box)
        f.grid(row=4, column=0, columnspan=2, sticky="w", padx=(24, 0), pady=(6, 0))
        ttk.Label(f, text="IP máy chủ:").pack(side="left")
        self.ent_mip = ttk.Entry(f, textvariable=self.master_ip, width=16)
        self.ent_mip.pack(side="left", padx=(6, 14))
        ttk.Label(f, text="Cổng:").pack(side="left")
        self.ent_port = ttk.Spinbox(f, from_=1, to=65535, textvariable=self.c_port, width=6)
        self.ent_port.pack(side="left", padx=(6, 14))
        ttk.Label(f, text="Chờ trước khi click:").pack(side="left")
        self.ent_settle = ttk.Spinbox(f, from_=0, to=100, textvariable=self.c_settle, width=4)
        self.ent_settle.pack(side="left", padx=(6, 2))
        ttk.Label(f, text="ms").pack(side="left", padx=(0, 14))
        self.btn_mip = ttk.Button(f, text="Lưu", width=5, command=self.save_client)
        self.btn_mip.pack(side="left")
        fa = ttk.Frame(box)
        fa.grid(row=5, column=0, columnspan=2, sticky="w", padx=(24, 0), pady=(6, 0))
        self.cb_any = ttk.Checkbutton(fa, text="Nhận kết nối từ mọi máy chủ trong mạng LAN", variable=self.any_master)
        self.cb_any.pack(side="left")
        ttk.Label(fa, text="(IP trong ô vẫn được giữ, bỏ tick là dùng lại)", style="Muted.TLabel").pack(
            side="left", padx=(8, 0))
        ttk.Label(box, style="Muted.TLabel",
                  text="Khi ĐỒNG BỘ mà máy này click hụt thì tăng thời gian chờ lên 12 - 20 ms").grid(
            row=6, column=0, columnspan=2, sticky="w", padx=(24, 0), pady=(4, 0))
        for w in (self.ent_mip, self.ent_port, self.ent_settle):
            w.bind("<Return>", lambda e: self.save_client())
        for v in (self.master_ip, self.c_port, self.c_settle, self.any_master):
            v.trace_add("write", lambda *a: self._client_state())

    def _build_info(self, main):
        f = ttk.Frame(main)
        f.pack(fill="x", pady=(10, 0))
        self.lbl_info = ttk.Label(f)
        self.lbl_info.pack(side="left")
        self.cb_admin = self.btn_admin = None
        if self.admin:   # đang có quyền Admin: tick ô này là lần sau mở app tự có quyền Admin, không hỏi nữa
            self.cb_admin = ttk.Checkbutton(f, text="Luôn mở bằng quyền Admin (không hỏi lại)",
                                            variable=self.admin_mode, command=self.on_admin_mode)
            self.cb_admin.pack(side="right")
            ttk.Label(f, text="✓ Quyền Admin", style="Ok.TLabel").pack(side="right", padx=(0, 16))
        else:            # bấm 1 lần: Windows hỏi 1 lần, từ đó về sau mở app là tự có quyền Admin
            self.btn_admin = ttk.Button(f, text="Chạy bằng Admin", command=self.run_as_admin)
            self.btn_admin.pack(side="right")
            ttk.Label(f, text="⚠ Chưa có quyền Admin", style="Warn.TLabel").pack(side="right", padx=8)

    def _build_peers(self, main):
        s = self.scale
        self.peers_box = box = ttk.LabelFrame(main, text=" Các máy trong bố cục ", padding=(8, 6, 8, 8))
        cols = (("name", "Máy", 170, "w"), ("ip", "IP", 130, "w"), ("pos", "Vị trí", 80, "center"),
                ("st", "Trạng thái", 200, "w"), ("rtt", "Độ trễ", 70, "e"), ("sync", "Đồng bộ", 80, "center"))
        tv = self.tree = ttk.Treeview(box, columns=[c[0] for c in cols], show="headings", height=4,
                                      selectmode="none")
        for key, text, width, anchor in cols:
            tv.heading(key, text=text, anchor=anchor)
            tv.column(key, width=int(width * s), minwidth=int(50 * s), anchor=anchor, stretch=key in ("name", "st"))
        for tag, color in (("ok", OK_C), ("off", MUTED), ("warn", WARN_C)):
            tv.tag_configure(tag, foreground=color)
        tv.tag_configure("active", background="#22476a", foreground="white")
        tv.pack(fill="x")
        tv.bind("<Double-1>", lambda e: self.open_server_config())
        ttk.Label(box, style="Muted.TLabel",
                  text="Scroll Lock TẮT = chuyển máy (chuột ra cạnh màn hình)   ·   BẬT = đồng bộ tất cả   ·   "
                       "bấm đúp: sửa bố cục").pack(anchor="w", pady=(6, 0))

    def _build_client(self, main):
        self.client_box = box = ttk.LabelFrame(main, text=" Máy khách ", padding=(12, 8, 12, 10))
        self.cl_state = tk.Label(box, bg=BG, fg=FG, font=self.f_bold, anchor="w", justify="left")
        self.cl_state.pack(fill="x")
        self.cl_hint = ttk.Label(box, style="Muted.TLabel", justify="left")
        self.cl_hint.pack(fill="x", pady=(4, 0))
        fw = ttk.Frame(box)
        fw.pack(fill="x", pady=(8, 0))
        ttk.Label(fw, text="Máy chủ báo \"Chưa kết nối được\"? Có thể tường lửa Windows của máy này đang chặn.",
                  style="Muted.TLabel").pack(side="left")
        ttk.Button(fw, text="Mở cổng tường lửa", command=self.open_fw).pack(side="right")

    def _build_log(self, main):
        self.log_frame = f = ttk.Frame(main)
        f.pack(fill="both", expand=True, pady=(10, 0))
        head = ttk.Frame(f)
        head.pack(fill="x")
        ttk.Label(head, text="Nhật ký", style="Bold.TLabel").pack(side="left")
        ttk.Button(head, text="Xóa", style="Small.TButton", command=self.clear_log).pack(side="right")
        ttk.Button(head, text="Sao chép", style="Small.TButton", command=self.copy_log).pack(side="right", padx=6)
        body = tk.Frame(f, bg=FIELD, highlightthickness=1, highlightbackground=BORDER)
        body.pack(fill="both", expand=True, pady=(6, 0))
        self.log = tk.Text(body, bg=FIELD, fg=FG, relief="flat", bd=0, font=self.f_mono, wrap="word", height=6,
                           padx=8, pady=6, highlightthickness=0, insertbackground=FG, selectbackground=SEL,
                           cursor="arrow", state="disabled")
        sb = ttk.Scrollbar(body, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
        for tag, color in (("err", ERR_C), ("warn", WARN_C), ("ok", OK_C), ("sync", SYNC_C), ("gui", MUTED)):
            self.log.tag_configure(tag, foreground=color)

    def _build_options(self, main):
        f = ttk.Frame(main)
        f.pack(side="bottom", fill="x", pady=(10, 0))
        ttk.Checkbutton(f, text="Tự chạy kvm khi mở app", variable=self.auto_run, command=self._save).pack(
            side="left")
        self.cb_autostart = ttk.Checkbutton(f, text="Khởi động cùng Windows", variable=self.autostart,
                                            command=self.on_autostart)
        self.cb_autostart.pack(side="left", padx=18)
        ttk.Checkbutton(f, text="Bấm X = ẩn xuống khay", variable=self.close_tray, command=self._save).pack(
            side="left")
        ttk.Button(f, text="Thoát hẳn", command=self.quit).pack(side="right")
        self.note = None
        if not self.tray.ok:
            self.note = n = ttk.Frame(main)
            n.pack(side="bottom", fill="x", pady=(8, 0))
            ttk.Label(n, style="Warn.TLabel",
                      text="Chưa có biểu tượng dưới khay (cần thư viện pystray + pillow): bấm X chỉ thu nhỏ xuống "
                           "thanh taskbar.").pack(side="left")
            self.btn_pip = ttk.Button(n, text="Cài ngay", command=self.install_tray)
            self.btn_pip.pack(side="right")

    def _layout_role(self):
        m = self.role.get() == "master"
        self.btn_cfg.state(["!disabled"] if m else ["disabled"])
        for w in (self.cb_any, self.ent_port, self.ent_settle):
            w.state(["disabled"] if m else ["!disabled"])
        self._client_state()   # (ô IP máy chủ: mờ khi là máy chủ hoặc đang tick nhận mọi máy chủ)
        (self.client_box if m else self.peers_box).pack_forget()
        (self.peers_box if m else self.client_box).pack(fill="x", pady=(10, 0), before=self.log_frame)

    def _layout_text(self):
        c = self.cfg
        n = len(peers_of(c))
        sync = c["SYNC_IPS"]
        txt = f"Bố cục: {n} máy khác" + ("" if n else " (chưa có - bấm Cấu hình máy chủ)") + \
              ("   ·   đồng bộ: tất cả" if sync is None else f"   ·   đồng bộ: {len(sync)} máy") + \
              f"   ·   cổng {c['PORT']}"
        if self.cfg_err:
            txt += "   ·   ⚠ cấu hình lỗi"
        self.lbl_layout.configure(text=txt)
        self.lbl_info.configure(text=f"Tên máy: {socket.gethostname()}   ·   IP: {', '.join(self.ips) or '?'}")
        ip = ", ".join(self.ips) or "?"
        self.cl_hint.configure(text=f"IP máy này: {ip}   ·   cổng {c['PORT']}\n"
                                    f"Ở máy chủ: bấm \"Cấu hình máy chủ…\" rồi thêm IP này vào đúng vị trí "
                                    f"(máy này đặt bên nào của máy chủ).")

    def _client_vals(self):
        """Giá trị đã lưu của máy khách, dạng như trên các ô: (IP máy chủ, cổng, chờ click ms, nhận mọi máy chủ?).
        Nhận mọi máy chủ = MASTER_IP để trống; IP còn trong ô lúc đó được cất ở MASTER_IP_SAVED."""
        c = self.cfg
        any_m = c["MASTER_IP"] is None
        ip = (c.get("MASTER_IP_SAVED") or "") if any_m else c["MASTER_IP"]
        return ip, str(c["PORT"]), str(int(round(c["CLICK_SETTLE"] * 1000))), any_m

    def _client_now(self):
        """Giá trị đang có trên các ô của máy khách (cùng dạng với _client_vals)."""
        return (self.master_ip.get().strip(), self.c_port.get().strip(), self.c_settle.get().strip(),
                self.any_master.get())

    def _client_vars(self, force=False, old=None):
        """Đưa giá trị đã lưu lên các ô của máy khách (ô đang sửa dở thì giữ nguyên, trừ khi force)."""
        for var, now, o, n in zip((self.master_ip, self.c_port, self.c_settle, self.any_master), self._client_now(),
                                  old or (None,) * 4, self._client_vals()):
            if force or now == o:
                var.set(n)

    def _client_state(self):
        """Nút Lưu của máy khách chỉ sáng khi có ô bị sửa. Tick nhận mọi máy chủ thì ô IP mờ đi (IP vẫn giữ)."""
        client = self.role.get() != "master"
        self.ent_mip.state(["!disabled"] if client and not self.any_master.get() else ["disabled"])
        same = self._client_now() == self._client_vals()
        self.btn_mip.state(["disabled"] if same or not client else ["!disabled"])

    # ---------- trạng thái ----------
    def _pc_name(self, ip):
        n = self.names.get(ip)
        return f"{n} ({ip})" if n and n != ip else ip

    def _master_status(self, m):
        if not m:
            return OK_C, "Máy chủ đang chạy", ""
        peers = m.get("peers") or []
        n_ok = sum(p.get("st") == "ok" for p in peers)
        if m.get("sync"):
            n = sum(p.get("st") == "ok" and p.get("sync") for p in peers)
            color, title = SYNC_C, f"ĐỒNG BỘ: điều khiển máy chủ + {n} máy cùng lúc"
        else:
            act = m.get("active")
            color = OK_C
            title = "CHUYỂN MÁY: đang điều khiển " + (self._pc_name(act) if act else "máy chủ (máy này)")
        sub = f"Scroll Lock {'BẬT' if m.get('sync') else 'TẮT'}   ·   đã kết nối {n_ok}/{len(peers)} máy"
        return color, title, sub

    def _client_status(self, c):
        port = self.kvm.get("start", {}).get("port", self.cfg["PORT"])
        if not c or not c.get("master"):
            return WARN_C, "Đang chờ máy chủ kết nối…", \
                f"IP máy này: {', '.join(self.ips) or '?'}   ·   cổng {port}   ·   máy chủ phải có IP này trong bố cục"
        mip = c["master"]
        if c.get("sync"):
            return SYNC_C, f"ĐỒNG BỘ: đang làm theo máy chủ {mip}", ""
        if c.get("entered"):
            return OK_C, f"Máy chủ {mip} đang điều khiển máy này", ""
        return OK_C, f"Đã kết nối máy chủ {mip}", "Ở máy chủ đưa chuột ra cạnh màn hình để sang máy này"

    def refresh(self):
        if self.dead:
            return
        running, k = self.runner.running, self.kvm
        role = (self.run_role if running else None) or self.role.get()
        if not running:
            if self.last_error:
                color, title, sub = ERR_C, "Đã dừng vì lỗi", self.last_error
            else:
                color, title = GREY, "Đang dừng"
                sub = f"Bấm \"Bắt đầu\" để chạy kvm ({ROLE_NAME[role]})"
        elif k.get("error"):
            color, title, sub = ERR_C, "Lỗi", k["error"]
        elif "start" not in k:
            color, title, sub = WARN_C, "Đang khởi động…", ""
        elif role == "master":
            color, title, sub = self._master_status(k.get("master"))
        else:
            color, title, sub = self._client_status(k.get("client"))
        if running and k.get("cfg_error"):
            sub += f"\n⚠ Cấu hình lỗi: {k['cfg_error']} - kvm đang dùng giá trị ghi trong kvm.py"
        elif self.cfg_err:
            sub += f"\n⚠ Cấu hình lỗi: {self.cfg_err}"
        d = int(16 * self.scale)
        self.dot.delete("all")
        self.dot.create_oval(2, 2, d + 2, d + 2, fill=color, outline="")
        self.st_title.configure(text=title, fg=ERR_C if color == ERR_C else FG)
        self.st_sub.configure(text=sub.strip())
        self.btn_run.configure(text="Dừng" if running else "Bắt đầu",
                               style="Stop.TButton" if running else "Accent.TButton")
        self.cl_state.configure(text=title, fg=color if color != GREY else MUTED)
        self._refresh_peers()
        self.tray.set(color, f"{APP}: {title}", running)

    def _refresh_peers(self):
        tv = self.tree
        m = self.kvm.get("master") if self.runner.running else None
        dirs = directions(self.cfg["ipTable"])
        if m:
            rows = [(p.get("ip"), p.get("sync"), p.get("st"), p.get("rtt")) for p in m.get("peers") or ()]
        else:
            rows = [(ip, sync, None, None) for ip, sync in peers_of(self.cfg)]
        act = m.get("active") if m else None
        keep = {r[0] for r in rows}
        for iid in tv.get_children():
            if iid not in keep:
                tv.delete(iid)
        for i, (ip, sync, st, rtt) in enumerate(rows):
            text, tag = {None: ("—", "off"), "off": ("Chưa kết nối", "off"), "ok": ("Đã kết nối", "ok"),
                         "old": ("kvm.py KHÁC bản: chép cùng file sang", "warn"),
                         "wait": ("Đang kết nối…", "warn")}.get(st, (str(st), "warn"))
            tags = (tag,)
            if st == "ok" and rtt is not None and rtt >= 30:
                text, tags = "Đã kết nối (chậm)", ("warn",)
            name = self.names.get(ip, ip)
            if ip == act:
                text, tags, name = "▶ Đang điều khiển", ("ok", "active"), "▶ " + name
            vals = (name, ip, dirs.get(ip, "chỉ đồng bộ"), text, "" if rtt is None else f"{rtt} ms",
                    "Có" if sync else "Không")
            if tv.exists(ip):
                tv.item(ip, values=vals, tags=tags)
                tv.move(ip, "", i)
            else:
                tv.insert("", i, iid=ip, values=vals, tags=tags)
        tv.configure(height=max(2, min(8, len(rows))))

    # ---------- nhật ký ----------
    def _open_logfile(self):
        path = os.path.join(os.path.dirname(SETTINGS_FILE), "nhat_ky.txt")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if os.path.exists(path) and os.path.getsize(path) > 2_000_000:
                os.replace(path, path[:-4] + "_cu.txt")
            return open(path, "a", encoding="utf-8", buffering=1)
        except OSError:
            return None

    @staticmethod
    def _tag(line):
        if "LỖI" in line:
            return "err"
        if "[!]" in line or "[X]" in line or "[..]" in line or "⚠" in line:
            return "warn"
        if "[OK]" in line:
            return "ok"
        if "[SCROLL LOCK]" in line:
            return "sync"
        if "[GUI]" in line:
            return "gui"
        return ""

    def _append(self, lines):
        t = self.log
        at_end = t.yview()[1] >= 0.999
        t.configure(state="normal")
        for line in lines:
            t.insert("end", line + "\n", self._tag(line))
        n = int(t.index("end-1c").split(".")[0])
        if n > 3000:
            t.delete("1.0", f"{n - 2000}.0")
        t.configure(state="disabled")
        if at_end:
            t.see("end")
        if self.logf:
            try:
                self.logf.write("\n".join(lines) + "\n")
            except (OSError, ValueError):
                self.logf = None

    def log_gui(self, msg):
        self._append([time.strftime("[%H:%M:%S] ") + msg])

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def copy_log(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.log.get("1.0", "end-1c"))
        self.log_gui("[GUI] Đã sao chép nhật ký - dán (Ctrl+V) vào tin nhắn để gửi")

    def _report(self, exc, val, tb):
        import traceback
        text = "".join(traceback.format_exception(exc, val, tb))
        write_error(text)
        try:
            self.log_gui("[LỖI] Giao diện: " + (text.strip().splitlines() or ["?"])[-1])
        except Exception:
            pass

    # ---------- vòng xử lý: mọi thứ từ luồng khác đi qua hàng đợi ----------
    def _poll(self):
        lines = []
        try:
            for _ in range(2000):
                try:
                    kind, data = self.q.get_nowait()
                except queue.Empty:
                    break
                if kind == "log":
                    lines.append(data)
                    continue
                if lines:
                    self._append(lines)
                    lines = []
                try:
                    if kind == "ev":
                        self._on_event(data)
                    elif kind == "exit":
                        self._on_exit(*data)
                    elif kind == "call":
                        data()
                    elif kind == "cmd":
                        if data == "show":
                            self.show()
                        elif data == "quit":
                            self.quit()
                except Exception:
                    self._report(*sys.exc_info())
            if lines:
                self._append(lines)
        except Exception:
            self._report(*sys.exc_info())
        finally:
            if not self.dead:
                self._poll_id = self.root.after(40, self._poll)

    def _on_event(self, d):
        ev = d.get("ev")
        if ev == "start":
            self.kvm["start"] = d
            if d.get("ips"):
                self.ips = [str(x) for x in d["ips"]]
                self._layout_text()
        elif ev in ("master", "client"):
            self.kvm[ev] = d
        elif ev == "error":
            self.kvm["error"] = self.last_error = str(d.get("msg") or "Lỗi")
            self.tray.notify(self.last_error)
        elif ev == "config":
            if d.get("st") == "error":
                self.kvm["cfg_error"] = str(d.get("msg"))
            self._reload_config()
        self.refresh()

    def _on_exit(self, p, code):
        if p is not self.runner.p:
            return
        ran, expected = time.monotonic() - self.started_t, self.runner.stopping or self.quitting
        err = self.kvm.get("error")
        self.kvm = {}
        if expected:
            self.log_gui("[GUI] Đã dừng kvm")
        else:
            self.last_error = err or f"kvm.py tự tắt (mã {code}) - xem nhật ký bên dưới"
            self.log_gui(f"[LỖI] kvm.py đã dừng bất ngờ (mã {code})")
            if not err and ran >= 10 and not self.restart_after:   # chạy được 1 lúc rồi mới tắt -> tự chạy lại
                now = time.monotonic()
                self.crashes = [t for t in self.crashes if now - t < 300] + [now]
                if len(self.crashes) <= 3:
                    self.log_gui("[GUI] Tự chạy lại kvm sau 3 giây…")
                    self.root.after(3000, lambda: None if self.runner.running or self.quitting else self.start())
            self.tray.notify(self.last_error)
        if self.restart_after and not self.quitting:
            self.restart_after = False
            self.start()
            return
        self.refresh()

    def _tick(self):
        """2 giây/lần: cấu hình bị thay đổi ngoài app này -> đọc lại."""
        if self.dead:
            return
        try:
            m = self._cfg_mtime()
            if m != self.cfg_mtime:
                self._reload_config()
                self.log_gui("[GUI] Cấu hình vừa được thay đổi ngoài app - đã đọc lại" +
                             (" (bấm Dừng rồi Bắt đầu để kvm dùng)" if self.runner.running else ""))
                self.refresh()
        finally:
            if not self.dead:
                self._tick_id = self.root.after(2000, self._tick)

    @staticmethod
    def _cfg_mtime():
        try:
            return os.path.getmtime(CONFIG_FILE)
        except OSError:
            return None

    def _reload_config(self):
        old = self._client_vals()
        self.cfg, self.names, self.cfg_err = load_config()
        self.cfg_mtime = self._cfg_mtime()
        self._client_vars(old=old)
        self._layout_text()
        self._client_state()

    # ---------- chạy / dừng kvm ----------
    def toggle_run(self):
        if self.runner.running:
            self.stop()
        else:
            self.start()

    def start(self):
        if self.runner.running or self.quitting:
            return
        self.last_error, self.kvm = None, {}
        if not os.path.isfile(KVM_PATH):
            self.last_error = f"Không thấy kvm.py: đặt kvm_gui.pyw cùng thư mục với kvm.py ({HERE})"
            self.log_gui("[LỖI] " + self.last_error)
            self.refresh()
            return
        role = self.run_role = self.role.get()
        self.started_t = time.monotonic()
        try:
            self.runner.start(role)
        except OSError as e:
            self.last_error = f"Không chạy được kvm.py: {e}"
            self.log_gui("[LỖI] " + self.last_error)
        else:
            self.log_gui(f"[GUI] Bắt đầu kvm ({ROLE_NAME[role]})")
        self.refresh()

    def stop(self, restart=False):
        self.restart_after = restart
        if self.runner.running:
            if not self.runner.stopping:
                self.log_gui("[GUI] Đang dừng kvm…")
            self.runner.stop()
        elif restart:
            self.restart_after = False
            self.start()
        self.refresh()

    # ---------- các nút ----------
    def on_role(self):
        self._save()
        self._layout_role()
        if self.runner.running and self.run_role != self.role.get():
            self.log_gui(f"[GUI] Đổi sang {ROLE_NAME[self.role.get()]} -> chạy lại kvm")
            self.stop(restart=True)
        elif not self.runner.running and self.last_error:   # đang dừng vì lỗi -> thử lại với vai trò mới
            self.start()
        self.refresh()

    def open_server_config(self):
        if self.role.get() != "master":
            return
        if self.cfg_win is not None and self.cfg_win.winfo_exists():
            self.cfg_win.lift()
            self.cfg_win.focus_force()
            return
        cfg, names, err = load_config()
        self.show()
        if err and not messagebox.askyesno(
                "Cấu hình bị lỗi", f"{err}\n\nMở cấu hình mặc định để sửa lại? (bấm OK trong cửa sổ cấu hình "
                                  f"sẽ lưu đè cấu hình cũ)", parent=self.root):
            return
        self.cfg, self.names, self.cfg_err = cfg, names, err
        self.cfg_win = ServerConfig(self, cfg, names)

    def on_config_saved(self, cfg, names):
        self.cfg, self.names, self.cfg_err = cfg, names, None
        self.cfg_mtime = self._cfg_mtime()
        self._client_vars(force=True)
        self._client_state()
        self._layout_text()
        self.log_gui("[OK] Đã lưu cấu hình")
        if self.runner.running:
            self.log_gui("[GUI] Chạy lại kvm để dùng cấu hình mới")
            self.stop(restart=True)
        self.refresh()

    def save_client(self):
        """Lưu IP máy chủ + cổng + thời gian chờ click của máy khách (giữ nguyên các phần cấu hình khác)."""
        if self.role.get() == "master":
            return
        ip, port, settle, any_m = self._client_now()
        try:
            if ip and host_error(ip):
                raise ValueError(f"IP máy chủ không hợp lệ: {ip}")
            if not ip and not any_m:
                raise ValueError("Nhập IP máy chủ, hoặc tick \"Nhận kết nối từ mọi máy chủ\"")
            if not port.isdigit() or not 1 <= int(port) <= 65535:
                raise ValueError("Cổng phải là số từ 1 đến 65535")
            if not settle.isdigit() or not 0 <= int(settle) <= 100:
                raise ValueError("Thời gian chờ trước khi click phải là số từ 0 đến 100 (ms)")
        except ValueError as e:
            messagebox.showerror(APP, str(e), parent=self.root)
            return
        cfg, names, err = load_config()
        if err and not messagebox.askyesno("Cấu hình bị lỗi", f"{err}\n\nLưu đè bằng cấu hình mới?",
                                           parent=self.root):
            return
        cfg.update(MASTER_IP=None if any_m else ip, MASTER_IP_SAVED=ip or None, PORT=int(port),
                   CLICK_SETTLE=int(settle) / 1000)
        try:
            save_config(cfg, names)
        except (OSError, ValueError) as e:
            messagebox.showerror(APP, f"Không lưu được cấu hình:\n{e}", parent=self.root)
            return
        self.on_config_saved(cfg, names)

    def open_fw(self):
        ok, msg = open_firewall(self.cfg["PORT"])
        self.log_gui(("[OK] " if ok else "[!] ") + msg)
        (messagebox.showinfo if ok else messagebox.showwarning)(APP, msg, parent=self.root)

    def _bg(self, work, done):
        """Chạy việc chậm (schtasks, UAC, pip) ở luồng phụ, xong thì gọi done(kết quả) trên giao diện."""
        def run():
            try:
                res = work()
            except Exception as e:
                res = e
            self.q.put(("call", lambda: done(res)))

        threading.Thread(target=run, daemon=True).start()

    def _set_admin_flag(self, on, by_user=False):
        """Ghi nhớ "Luôn mở bằng quyền Admin" (bản quyền thường đọc cờ này để biết có nhờ tác vụ mở bản Admin).
        by_user: người dùng tự bỏ tick -> nhớ để không tự bật lại."""
        self.admin_mode.set(on)
        st, old = self.settings, dict(self.settings)
        if on:
            st["admin_task"] = APP_FILE
            st.pop("admin_off", None)
        else:
            st.pop("admin_task", None)
            if by_user:
                st["admin_off"] = True
        if st != old:
            self._save()

    def _check_autostart(self):
        """Đọc trạng thái 2 ô từ Windows. Tác vụ của bản cũ / của app nằm chỗ khác (đã chuyển thư mục)
        -> đang có quyền Admin thì ghi lại cho đúng app này, giữ nguyên lịch tự chạy khi đăng nhập."""
        flag, admin = admin_task_ready(self.settings), self.admin

        def work():
            info = task_query()
            mine = bool(info and info["new"] and flag)
            if info and not mine and admin and create_task(info["logon"])[0] == 0:
                mine = True
            rv = run_key_value()
            if rv is not None and rv != autostart_cmd():
                run_key(autostart_cmd())
            return mine, bool(info and info["logon"]) or rv is not None

        def done(res):
            if not isinstance(res, tuple):
                return
            mine, auto = res
            self.autostart.set(auto)
            self._set_admin_flag(mine)
            setup, self.opts.setup_admin = self.opts.setup_admin, False
            if not self.admin:
                return
            if mine:
                if setup:
                    self.log_gui("[OK] Luôn mở bằng quyền Admin: đã bật, lần sau mở MiniKVM không hỏi nữa")
            elif setup or not self.settings.get("admin_off"):
                # đang có quyền Admin (bấm "Chạy bằng Admin" / chuột phải "Run as administrator"...) -> bật luôn
                self.admin_mode.set(True)
                self.on_admin_mode(quiet=not setup)

        self._bg(work, done)

    def on_admin_mode(self, quiet=False):
        """Tick / bỏ tick "Luôn mở bằng quyền Admin". quiet: app tự bật -> lỗi chỉ ghi nhật ký, không hiện hộp báo."""
        want, auto = self.admin_mode.get(), self.autostart.get()
        if self.cb_admin is not None:
            self.cb_admin.state(["disabled"])

        def done(err):
            if self.cb_admin is not None:
                self.cb_admin.state(["!disabled"])
            if err is None:
                self._set_admin_flag(want, by_user=True)
                self.log_gui("[OK] " + ("Luôn mở bằng quyền Admin: đã bật, từ giờ mở MiniKVM tự có quyền Admin, "
                                        "Windows không hỏi nữa (bỏ tick ô này nếu không muốn)" if want
                                        else "Đã tắt \"Luôn mở bằng quyền Admin\""))
                return
            self.admin_mode.set(not want)
            if not quiet:
                messagebox.showwarning(APP, str(err), parent=self.root)
            self.log_gui("[!] Luôn mở bằng quyền Admin: " + str(err))

        self._bg(lambda: apply_startup(want, auto), done)

    def on_autostart(self):
        want, always = self.autostart.get(), self.admin_mode.get()
        if always and not self.admin:
            self.autostart.set(not want)
            messagebox.showwarning(APP, "App đang chạy quyền thường nên chưa đổi được.\n"
                                        "Bấm \"Chạy bằng Admin\" rồi làm lại.", parent=self.root)
            return
        self.cb_autostart.state(["disabled"])

        def done(err):
            self.cb_autostart.state(["!disabled"])
            if err is None:
                self.log_gui("[OK] Khởi động cùng Windows: " + (
                    ("bật - đăng nhập Windows là MiniKVM tự chạy dưới khay" + (" (quyền Admin)" if always else
                                                                                " (quyền thường)")) if want
                    else "tắt"))
                return
            self.autostart.set(not want)
            messagebox.showwarning(APP, str(err), parent=self.root)
            self.log_gui("[!] Khởi động cùng Windows: " + str(err))

        self._bg(lambda: apply_startup(always, want), done)

    def run_as_admin(self):
        """Mở lại bằng quyền Admin (Windows hỏi 1 lần) + tự bật "Luôn mở bằng quyền Admin" -> lần sau không hỏi."""
        extra = "--replace --setup-admin" + (" --start" if self.runner.running else "")
        self.btn_admin.state(["disabled"])

        def done(ok):
            self.btn_admin.state(["!disabled"])
            if ok is True:
                self.log_gui("[GUI] Đang mở lại MiniKVM bằng quyền Admin (Windows chỉ hỏi lần này)…")
            else:
                self.log_gui("[!] Không mở được bằng quyền Admin (đã bấm \"Không\" ở hộp thoại của Windows?)")

        self._bg(lambda: relaunch_as_admin(extra), done)

    def install_tray(self):
        self.btn_pip.state(["disabled"])
        self.btn_pip.configure(text="Đang cài…")
        self.log_gui("[GUI] Đang cài pystray + pillow (cần Internet, khoảng 1 phút)…")

        def work():
            r = subprocess.run([python_exe(), "-m", "pip", "install", "--disable-pip-version-check", "pystray",
                                "pillow"], capture_output=True, creationflags=CREATE_NO_WINDOW, timeout=600)
            return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")

        def done(res):
            ok = isinstance(res, tuple) and res[0] == 0
            if ok:
                import importlib
                import site
                try:
                    site.addsitedir(site.getusersitepackages())   # (pip cài vào thư mục của user lần đầu)
                except Exception:
                    pass
                importlib.invalidate_caches()
                self.tray = Tray(self)
            if ok and self.tray.ok:
                self.note.pack_forget()
                self.log_gui("[OK] Đã cài xong: MiniKVM có biểu tượng dưới khay (cạnh đồng hồ)")
                self.tray.on = None
                self.refresh()
                return
            tail = (res[1].strip().splitlines()[-2:] if isinstance(res, tuple) else [str(res)]) or ["?"]
            self.log_gui("[LỖI] Cài không được: " + " | ".join(tail) + ("" if not ok else " - hãy mở lại app"))
            self.btn_pip.state(["!disabled"])
            self.btn_pip.configure(text="Cài ngay")

        self._bg(work, done)

    # ---------- cửa sổ / khay / thoát ----------
    def show(self):
        if self.dead:
            return
        r = self.root
        r.deiconify()
        r.lift()
        try:   # Windows không cho app đang ẩn tự nhảy lên trên -> tạm đặt "luôn ở trên"
            r.attributes("-topmost", True)
            r.after(300, lambda: r.attributes("-topmost", False))
        except tk.TclError:
            pass
        r.focus_force()

    def on_close(self):
        if not self.close_tray.get():
            self.quit()
        elif self.tray.ok:
            self._save()
            self.root.withdraw()
            if not self.settings.get("tray_hint"):
                self.settings["tray_hint"] = True
                self._save()
                self.tray.notify("MiniKVM vẫn đang chạy dưới khay (cạnh đồng hồ). Bấm vào biểu tượng để mở lại.")
        else:
            self.root.iconify()

    def _save(self):
        st = self.settings
        st.update(role=self.role.get(), auto_run=self.auto_run.get(), close_to_tray=self.close_tray.get())
        try:
            if self.root.state() == "normal":
                st["size"] = f"{self.root.winfo_width()}x{self.root.winfo_height()}"
        except tk.TclError:
            pass
        save_settings(st)

    def quit(self):
        if self.quitting:
            return
        self.quitting, self.restart_after = True, False
        self._save()
        self.runner.stop()   # kvm thoát êm: client trả lại cài đặt chuột, nhả phím đang giữ
        self.root.withdraw()
        self._finish(time.monotonic() + 4.0)

    def _finish(self, deadline):
        if self.runner.running and time.monotonic() < deadline:
            self.root.after(100, lambda: self._finish(deadline))
            return
        if self.runner.running:
            try:
                self.runner.p.kill()
            except OSError:
                pass
        self.tray.stop()
        self.ctl.close()
        if self.logf:
            try:
                self.logf.close()
            except OSError:
                pass
        self.dead = True
        for aid in (self._poll_id, self._tick_id):
            if aid:
                try:
                    self.root.after_cancel(aid)
                except tk.TclError:
                    pass
        self.root.destroy()

    def run(self):
        self._layout_text()
        self._layout_role()
        self.refresh()
        self.log_gui(f"[GUI] {APP} - kvm.py: {KVM_PATH}")
        if self.cfg_err:
            self.log_gui(f"[!] Cấu hình lỗi: {self.cfg_err}")
        if not self.tray.ok:
            self.log_gui(f"[GUI] Không có biểu tượng khay ({getattr(self.tray, 'why', '?')})")
        if self.opts.handoff == "no_task":   # tác vụ "Luôn mở bằng quyền Admin" đã bị xóa (vd trong Task Scheduler)
            self._set_admin_flag(False)
            self.log_gui("[!] Không thấy tác vụ \"Luôn mở bằng quyền Admin\" (đã bị xóa?) - đang chạy quyền thường")
        elif self.opts.handoff == "timeout":
            self.log_gui("[!] Mở bản quyền Admin không được - đang chạy quyền thường")
        if not self.admin:
            self.log_gui("[!] Chưa có quyền Admin: không điều khiển được game/cửa sổ đang chạy bằng quyền Admin. "
                         "Bấm \"Chạy bằng Admin\" (Windows chỉ hỏi 1 lần, lần sau tự có quyền Admin)")
        if not self.opts.tray:
            self.show()   # (bản Admin do tác vụ mở: đưa cửa sổ lên trên cùng, không bị nằm dưới cửa sổ khác)
        elif not self.tray.ok:
            self.root.iconify()
        self._poll_id = self.root.after(40, self._poll)
        self._tick_id = self.root.after(2000, self._tick)
        if self.opts.tray or self.opts.start or self.auto_run.get():
            self.root.after(150, self.start)
        if IS_WIN:
            self._check_autostart()
        else:
            for cb in (self.cb_autostart, self.cb_admin):
                if cb is not None:
                    cb.state(["disabled"])
        self.root.mainloop()


def fatal(msg):
    write_error(msg)
    if IS_WIN:
        try:
            ctypes.windll.user32.MessageBoxW(None, msg[-1500:], APP, 0x10)
            return
        except Exception:
            pass
    print(msg, file=sys.stderr)


def main():
    args = [a.lower() for a in sys.argv[1:]]
    opts = types.SimpleNamespace(tray="--tray" in args, start="--start" in args, replace="--replace" in args,
                                 task="--task" in args, setup_admin="--setup-admin" in args, handoff=None)
    if opts.task:   # bản Admin do tác vụ "Luôn mở bằng quyền Admin" mở
        h = read_handoff()
        if h is None:   # Windows tự chạy lúc đăng nhập -> ẩn dưới khay, tự bật kvm
            opts.tray = True
        else:           # bản quyền thường vừa nhờ mở -> giữ đúng tùy chọn của nó
            opts.tray, opts.start = bool(h.get("tray")), bool(h.get("start"))
    hide_own_console()
    if IS_WIN:
        try:   # biểu tượng trên taskbar là của MiniKVM, không bị gộp chung với Python
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP)
        except Exception:
            pass
        try:   # chữ nét trên màn hình phóng to 125% / 150%
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
    q = queue.Queue()
    ctl = Control(q)
    if not ctl.listen():
        if opts.replace:   # (mở lại bằng quyền Admin) app cũ thoát rồi app mới chạy tiếp
            send_command("quit")
            t = time.monotonic() + 10
            while not ctl.listen() and time.monotonic() < t:
                time.sleep(0.25)
        elif send_command("ping" if opts.tray else "show"):
            return   # đã có MiniKVM đang chạy -> hiện cửa sổ của nó rồi thoát
    elif not (opts.task or opts.replace) and admin_task_ready(load_settings()) and not is_admin():
        opts.handoff = handoff_to_admin(opts, ctl)   # đã bật "Luôn mở bằng quyền Admin" -> mở bản Admin, không hỏi
        if opts.handoff == "ok":
            return
        if not ctl.listen() and send_command("ping" if opts.tray else "show"):
            return   # bản Admin mở lên trễ -> dùng luôn bản đó
    App(opts, q, ctl).run()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException:
        import traceback
        fatal("MiniKVM bị lỗi:\n\n" + traceback.format_exc())
