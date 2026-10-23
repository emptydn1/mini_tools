#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crop Tool — cắt ảnh và lấy toạ độ vùng cắt (top, left, width, height).

Chạy (Windows): nhấp đúp file crop_app.pyw — không hiện cửa sổ console, không cần build exe.
  Lần đầu nếu máy chưa có PySide6, app sẽ hỏi để tự cài.

Mở ảnh:
  • Kéo thả ảnh vào cửa sổ app
  • Kéo thả ảnh lên file crop_app.pyw (hoặc shortcut của nó) / "Open with" → app
  • Ctrl+O để chọn file, Ctrl+V để dán ảnh (vd. sau Win+Shift+S) hoặc đường dẫn

Chọn vùng cắt:
  • Nhấn giữ chuột trái và kéo ở bất kỳ đâu trên ảnh để chọn vùng (giống Snipping Tool)
    – giữ Shift khi kéo để chọn hình vuông
  • Kéo góc / cạnh của vùng đã chọn để chỉnh kích thước
  • Ctrl + kéo bên trong vùng: di chuyển vùng; Esc: bỏ chọn; Ctrl+A: chọn cả ảnh
  • Lăn chuột: phóng to / thu nhỏ quanh con trỏ
  • Chuột phải / chuột giữa, hoặc giữ Space + kéo: di chuyển ảnh
  • Mũi tên: nhích vùng 1px (Shift: 10px); Ctrl + mũi tên: đổi kích thước

Trong lúc kéo, ô bên dưới hiện ngay top / left / width / height (pixel của ảnh gốc);
thả chuột là toạ độ tự được sao chép vào clipboard (Enter / Ctrl+C để sao chép lại).

Cài đặt thủ công:  pip install PySide6
Chạy từ dòng lệnh: python crop_app.pyw [đường_dẫn_ảnh]
"""

import json
import os
import sys


def _ensure_pyside6():
    """Chạy bằng pythonw (.pyw) thì lỗi thiếu thư viện sẽ bị nuốt mất —
    nên kiểm tra trước, hỏi người dùng và tự cài PySide6 nếu cần."""
    try:
        import PySide6  # noqa: F401
        return
    except ImportError:
        pass
    title = "Crop Tool"
    if sys.platform != "win32":
        sys.stderr.write("Thiếu PySide6. Hãy chạy:  pip install PySide6\n")
        sys.exit(1)
    import ctypes
    import subprocess
    box = ctypes.windll.user32.MessageBoxW
    MB_YESNO, MB_ICONQUESTION, MB_ICONERROR, IDYES = 0x04, 0x20, 0x10, 6
    ask = ("Máy chưa có thư viện PySide6 (cần để chạy app).\n\n"
           "Cài ngay bây giờ? Cần kết nối mạng, mất khoảng 1–2 phút.")
    if box(None, ask, title, MB_YESNO | MB_ICONQUESTION) != IDYES:
        sys.exit(1)
    exe = sys.executable
    folder, name = os.path.split(exe)
    console_exe = os.path.join(folder, "python.exe")
    if name.lower() == "pythonw.exe" and os.path.exists(console_exe):
        exe = console_exe   # dùng python.exe để hiện cửa sổ cài đặt, thấy được tiến trình
    result = subprocess.run([exe, "-m", "pip", "install", "PySide6"],
                            creationflags=subprocess.CREATE_NEW_CONSOLE)
    if result.returncode != 0:
        box(None, "Cài PySide6 không thành công.\n\nHãy mở Command Prompt và chạy:\n"
                  "    pip install PySide6", title, MB_ICONERROR)
        sys.exit(1)
    # mở lại app trong tiến trình mới để Python nhận thư viện vừa cài
    subprocess.Popen([sys.executable, os.path.abspath(__file__)] + sys.argv[1:])
    sys.exit(0)


_ensure_pyside6()

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (QAction, QColor, QCursor, QFont, QFontMetricsF, QGuiApplication, QIcon,
                           QImage, QImageReader, QKeySequence, QPainter, QPainterPath,
                           QPalette, QPen, QPixmap)
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout,
                               QLabel, QLineEdit, QMainWindow, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget, QMessageBox)

APP_NAME = "Crop Tool"
ACCENT = "#4CC2FF"
BG = "#202020"

ASPECTS = [
    ("Tự do", None),
    ("Tỉ lệ gốc", "orig"),
    ("1:1", 1.0),
    ("4:3", 4 / 3),
    ("3:4", 3 / 4),
    ("3:2", 3 / 2),
    ("16:9", 16 / 9),
    ("9:16", 9 / 16),
]

FORMATS = [
    ("Văn bản", lambda d: "top: {top}, left: {left}, width: {width}, height: {height}".format(**d)),
    ("JSON", lambda d: json.dumps(d)),
    ("CSS", lambda d: "top: {top}px; left: {left}px; width: {width}px; height: {height}px;".format(**d)),
]

HANDLE_CURSORS = {
    "nw": Qt.CursorShape.SizeFDiagCursor, "se": Qt.CursorShape.SizeFDiagCursor,
    "ne": Qt.CursorShape.SizeBDiagCursor, "sw": Qt.CursorShape.SizeBDiagCursor,
    "n": Qt.CursorShape.SizeVerCursor, "s": Qt.CursorShape.SizeVerCursor,
    "e": Qt.CursorShape.SizeHorCursor, "w": Qt.CursorShape.SizeHorCursor,
    "move": Qt.CursorShape.SizeAllCursor,
}


def supported_exts():
    exts = set()
    for f in QImageReader.supportedImageFormats():
        try:
            exts.add("." + bytes(f.data()).decode("ascii", "ignore").lower())
        except Exception:
            pass
    return exts or {".png", ".jpg", ".jpeg", ".bmp", ".gif"}


# --------------------------------------------------------------------------- #
#  Vùng hiển thị ảnh + khung cắt
# --------------------------------------------------------------------------- #
class CropCanvas(QWidget):
    selectionChanged = Signal()    # vùng chọn thay đổi (kể cả khi đang kéo)
    selectionFinished = Signal()   # đã chọn xong (thả chuột, Ctrl+A, phím mũi tên…)
    zoomChanged = Signal(float)
    openRequested = Signal()

    MARGIN = 40   # khoảng trống quanh ảnh khi "vừa khung"
    HIT = 9       # bán kính bắt tay cầm (px màn hình)
    DRAG_MIN = 3  # kéo ít hơn số px này coi như chỉ là cú click

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(320, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._image = None          # QImage gốc
        self._pix = None            # QPixmap để vẽ
        self._img_w = self._img_h = 0
        self._scale = 1.0           # px màn hình (logic) / px ảnh
        self._offset = QPointF(0, 0)
        self._fit_mode = True
        self._crop = QRectF()       # toạ độ ảnh (số nguyên); rỗng = chưa chọn vùng
        self._aspect_spec = None

        self._mode = None           # None | pan | move | new | n s e w nw ne sw se
        self._started = False       # đã kéo đủ xa để tính là kéo (không phải click)
        self._mods = Qt.KeyboardModifier.NoModifier
        self._press_screen = QPointF()
        self._press_img = QPointF()
        self._start_rect = QRectF()
        self._prev_crop = QRectF()
        self._pan_last = QPointF()
        self._hover = None          # vị trí chuột (px màn hình) để vẽ đường dóng
        self._space = False
        self._drop_hover = False

        self._cache = None
        self._cache_key = None

    # ---------------- trạng thái ----------------
    @property
    def has_image(self):
        return self._pix is not None

    def image(self):
        return self._image

    def image_size(self):
        return self._img_w, self._img_h

    def zoom(self):
        return self._scale * self.devicePixelRatioF()

    def aspect(self):
        if self._aspect_spec == "orig":
            return self._img_w / self._img_h if self.has_image else None
        return self._aspect_spec

    @property
    def has_selection(self):
        return self.has_image and not self._crop.isEmpty()

    def crop_values(self):
        """(left, top, width, height) theo pixel ảnh gốc; None nếu chưa chọn vùng."""
        if not self.has_selection:
            return None
        r = self._crop
        return int(r.x()), int(r.y()), int(r.width()), int(r.height())

    def set_image(self, image: QImage):
        self._image = image
        self._pix = QPixmap.fromImage(image)
        self._img_w, self._img_h = image.width(), image.height()
        self._cache = self._cache_key = None
        self._mode = None
        self._crop = QRectF()       # mở ảnh mới: chưa chọn vùng nào
        self.fit()
        self.selectionChanged.emit()

    def set_drop_hover(self, on):
        self._drop_hover = on
        self.update()

    # ---------------- toạ độ ----------------
    def to_img(self, p):
        return QPointF((p.x() - self._offset.x()) / self._scale,
                       (p.y() - self._offset.y()) / self._scale)

    def to_screen_rect(self, r):
        s = self._scale
        return QRectF(self._offset.x() + r.x() * s, self._offset.y() + r.y() * s,
                      r.width() * s, r.height() * s)

    # ---------------- zoom / pan ----------------
    def fit(self):
        if not self.has_image:
            return
        dpr = self.devicePixelRatioF()
        aw = max(1.0, self.width() - 2 * self.MARGIN)
        ah = max(1.0, self.height() - 2 * self.MARGIN)
        self._scale = min(aw / self._img_w, ah / self._img_h, 1.0 / dpr)
        self._offset = QPointF((self.width() - self._img_w * self._scale) / 2,
                               (self.height() - self._img_h * self._scale) / 2)
        self._fit_mode = True
        self.update()
        self.zoomChanged.emit(self.zoom())

    def set_zoom(self, zoom, anchor=None):
        if not self.has_image:
            return
        zoom = max(0.02, min(32.0, zoom))
        if anchor is None:
            anchor = QPointF(self.width() / 2, self.height() / 2)
        ip = self.to_img(anchor)
        self._scale = zoom / self.devicePixelRatioF()
        self._offset = QPointF(anchor.x() - ip.x() * self._scale,
                               anchor.y() - ip.y() * self._scale)
        self._fit_mode = False
        self._clamp_offset()
        self.update()
        self.zoomChanged.emit(self.zoom())

    def zoom_in(self):
        self.set_zoom(self.zoom() * 1.25)

    def zoom_out(self):
        self.set_zoom(self.zoom() / 1.25)

    def _clamp_offset(self):
        w, h = self._img_w * self._scale, self._img_h * self._scale
        m = self.MARGIN
        x, y = self._offset.x(), self._offset.y()
        x = (self.width() - w) / 2 if w + 2 * m <= self.width() else min(m, max(self.width() - m - w, x))
        y = (self.height() - h) / 2 if h + 2 * m <= self.height() else min(m, max(self.height() - m - h, y))
        self._offset = QPointF(x, y)

    def resizeEvent(self, e):
        if self.has_image:
            if self._fit_mode:
                self.fit()
            else:
                self._clamp_offset()
        super().resizeEvent(e)

    # ---------------- khung cắt ----------------
    def _set_crop(self, l, t, r, b):
        W, H = self._img_w, self._img_h
        l = int(round(min(max(l, 0), W - 1)))
        t = int(round(min(max(t, 0), H - 1)))
        r = int(round(min(max(r, 0), W)))
        b = int(round(min(max(b, 0), H)))
        if r <= l:
            r = l + 1
        if b <= t:
            b = t + 1
        new = QRectF(l, t, r - l, b - t)
        if new != self._crop:
            self._crop = new
            self.selectionChanged.emit()
        self.update()

    def _largest_rect(self, a, center):
        W, H = float(self._img_w), float(self._img_h)
        w, h = W, W / a
        if h > H:
            h, w = H, H * a
        cx = min(max(center.x(), w / 2), W - w / 2)
        cy = min(max(center.y(), h / 2), H - h / 2)
        return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2

    def clear_selection(self):
        if not self.has_image:
            return
        self._mode = None
        if not self._crop.isEmpty():
            self._crop = QRectF()
            self.selectionChanged.emit()
        self.update()

    def select_all(self):
        if not self.has_image:
            return
        a = self.aspect()
        if a:
            self._set_crop(*self._largest_rect(a, QPointF(self._img_w / 2, self._img_h / 2)))
        else:
            self._set_crop(0, 0, self._img_w, self._img_h)
        self.selectionFinished.emit()

    def cancel_drag(self):
        """Esc khi đang kéo: trả lại vùng cũ. Trả về True nếu đã huỷ một thao tác kéo."""
        if self._mode in (None, "pan"):
            return False
        self._mode = None
        self._started = False
        if self._crop != self._prev_crop:
            self._crop = QRectF(self._prev_crop)
            self.selectionChanged.emit()
        self.update()
        return True

    def set_aspect(self, spec):
        self._aspect_spec = spec
        a = self.aspect()
        if self.has_selection and a:
            # thu vùng hiện tại về đúng tỉ lệ, giữ nguyên tâm
            c = self._crop
            w, h = c.width(), c.height()
            if w / h > a:
                w = h * a
            else:
                h = w / a
            cx, cy = c.center().x(), c.center().y()
            self._set_crop(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            self.selectionFinished.emit()
        self.update()

    def _fit_aspect(self, m, l, t, r, b, a):
        """Ép khung theo tỉ lệ a = w/h, neo theo cạnh/góc đối diện."""
        W, H = float(self._img_w), float(self._img_h)
        s = self._start_rect
        w, h = max(r - l, 1.0), max(b - t, 1.0)
        if len(m) == 2:  # kéo góc
            ax = s.right() if "w" in m else s.left()
            ay = s.bottom() if "n" in m else s.top()
            if w / h > a:
                h = w / a
            else:
                w = h * a
            max_w = ax if "w" in m else W - ax
            max_h = ay if "n" in m else H - ay
            if w > max_w:
                w, h = max_w, max_w / a
            if h > max_h:
                h, w = max_h, max_h * a
            l = ax - w if "w" in m else ax
            t = ay - h if "n" in m else ay
            return l, t, l + w, t + h
        if m in ("e", "w"):  # kéo cạnh trái/phải → giữ tâm dọc
            h = w / a
            cy = s.center().y()
            max_h = 2 * min(cy, H - cy)
            if h > max_h:
                h, w = max_h, max_h * a
            if m == "e":
                r = l + w
            else:
                l = r - w
            return l, cy - h / 2, r, cy + h / 2
        # kéo cạnh trên/dưới → giữ tâm ngang
        w = h * a
        cx = s.center().x()
        max_w = 2 * min(cx, W - cx)
        if w > max_w:
            w, h = max_w, max_w / a
        if m == "s":
            b = t + h
        else:
            t = b - h
        return cx - w / 2, t, cx + w / 2, b

    def _hit_test(self, pos, mods=None):
        """Trả về tay cầm dưới con trỏ: n s e w nw ne sw se, 'move' (Ctrl + bên trong vùng)
        hoặc None (→ kéo sẽ vẽ vùng chọn mới)."""
        if not self.has_selection:
            return None
        if mods is None:
            mods = QGuiApplication.keyboardModifiers()
        r = self.to_screen_rect(self._crop)
        t = self.HIT
        x, y = pos.x(), pos.y()
        if not (r.left() - t <= x <= r.right() + t and r.top() - t <= y <= r.bottom() + t):
            return None
        inside = r.contains(pos)
        if inside and mods & Qt.KeyboardModifier.ControlModifier:
            return "move"
        ix, iy = min(t, r.width() / 4), min(t, r.height() / 4)   # dung sai phía trong
        near_l = x <= r.left() + ix
        near_r = x >= r.right() - ix
        near_t = y <= r.top() + iy
        near_b = y >= r.bottom() - iy
        v = "n" if near_t else "s" if near_b else ""
        hz = "w" if near_l else "e" if near_r else ""
        return (v + hz) or None

    def _drag_to(self, pos):
        W, H = self._img_w, self._img_h
        p = self.to_img(pos)
        s = self._start_rect
        a = self.aspect()
        m = self._mode
        dx, dy = p.x() - self._press_img.x(), p.y() - self._press_img.y()

        if m == "move":
            x = round(min(max(0.0, s.x() + dx), W - s.width()))
            y = round(min(max(0.0, s.y() + dy), H - s.height()))
            self._set_crop(x, y, x + s.width(), y + s.height())
            return

        if m == "new":
            ax, ay = s.x(), s.y()
            px, py = min(max(0.0, p.x()), W), min(max(0.0, p.y()), H)
            l, r = min(ax, px), max(ax, px)
            t, b = min(ay, py), max(ay, py)
            if not a and self._mods & Qt.KeyboardModifier.ShiftModifier:
                a = 1.0   # giữ Shift: hình vuông
            if a:
                corner = ("n" if py < ay else "s") + ("w" if px < ax else "e")
                l, t, r, b = self._fit_aspect(corner, l, t, r, b, a)
            self._set_crop(l, t, r, b)
            return

        l, t, r, b = s.left(), s.top(), s.right(), s.bottom()
        if "w" in m:
            l = min(max(0.0, l + dx), r - 1)
        if "e" in m:
            r = max(min(float(W), r + dx), l + 1)
        if "n" in m:
            t = min(max(0.0, t + dy), b - 1)
        if "s" in m:
            b = max(min(float(H), b + dy), t + 1)
        if a:
            l, t, r, b = self._fit_aspect(m, l, t, r, b, a)
        self._set_crop(l, t, r, b)

    # ---------------- chuột / phím ----------------
    def _refresh_cursor(self, pos, mods=None):
        if not self.has_image:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        elif self._space:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(HANDLE_CURSORS.get(self._hit_test(pos, mods), Qt.CursorShape.CrossCursor))

    def _over_image(self, pos):
        return self.has_image and self.to_screen_rect(
            QRectF(0, 0, self._img_w, self._img_h)).contains(pos)

    def mousePressEvent(self, e):
        pos = e.position()
        btn = e.button()
        if not self.has_image:
            if btn == Qt.MouseButton.LeftButton:
                self.openRequested.emit()
            return
        self.setFocus()
        if btn in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton) or \
                (btn == Qt.MouseButton.LeftButton and self._space):
            self._mode = "pan"
            self._pan_last = pos
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        if btn != Qt.MouseButton.LeftButton:
            return
        self._mods = e.modifiers()
        self._press_screen = pos
        self._press_img = self.to_img(pos)
        self._start_rect = QRectF(self._crop)
        self._prev_crop = QRectF(self._crop)
        self._started = False
        m = self._hit_test(pos, self._mods)
        if m is None:  # nhấn giữ chuột trái → bắt đầu vẽ vùng chọn mới từ điểm này
            ax = round(min(max(0.0, self._press_img.x()), self._img_w))
            ay = round(min(max(0.0, self._press_img.y()), self._img_h))
            self._start_rect = QRectF(ax, ay, 0, 0)
            m = "new"
        self._mode = m
        self.update()

    def mouseMoveEvent(self, e):
        pos = e.position()
        self._hover = pos
        if self._mode == "pan":
            d = pos - self._pan_last
            self._pan_last = pos
            self._offset = self._offset + d
            self._fit_mode = False
            self._clamp_offset()
            self.update()
            return
        if self._mode:
            self._mods = e.modifiers()
            if not self._started:
                if (pos - self._press_screen).manhattanLength() < self.DRAG_MIN:
                    return
                self._started = True
            self._drag_to(pos)
            return
        self._refresh_cursor(pos, e.modifiers())
        if self.has_image:
            self.update()   # vẽ lại đường dóng theo con trỏ

    def mouseReleaseEvent(self, e):
        # cú click không kéo → giữ nguyên vùng đang có
        finished = self._mode not in (None, "pan") and self._started and self._crop != self._prev_crop
        self._mode = None
        self._started = False
        if finished:
            self.selectionFinished.emit()
        self._refresh_cursor(e.position(), e.modifiers())
        self.update()

    def leaveEvent(self, e):
        self._hover = None
        self.update()
        super().leaveEvent(e)

    def wheelEvent(self, e):
        if not self.has_image:
            return
        dy = e.angleDelta().y()
        if dy:
            self.set_zoom(self.zoom() * (1.2 ** (dy / 120.0)), e.position())

    def _modifier_changed(self, mods):
        """Nhấn/thả Ctrl hoặc Shift: cập nhật con trỏ, hoặc vùng đang vẽ (Shift = vuông)."""
        if not self.has_image:
            return
        if self._mode == "new" and self._started and self._hover is not None:
            self._mods = mods
            self._drag_to(self._hover)
        elif self._mode is None:
            self._refresh_cursor(QPointF(self.mapFromGlobal(QCursor.pos())), mods)

    def keyPressEvent(self, e):
        k, mods = e.key(), e.modifiers()
        if k in (Qt.Key.Key_Control, Qt.Key.Key_Shift):
            self._modifier_changed(mods)
            return
        if k == Qt.Key.Key_Space:
            if not e.isAutoRepeat():
                self._space = True
                if self._mode is None:
                    self.setCursor(Qt.CursorShape.OpenHandCursor)
            return
        arrows = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0),
                  Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}
        if self.has_selection and k in arrows and self._mode is None:
            step = 10 if mods & Qt.KeyboardModifier.ShiftModifier else 1
            dx, dy = arrows[k][0] * step, arrows[k][1] * step
            c = self._crop
            if mods & Qt.KeyboardModifier.ControlModifier:
                self._set_crop(c.left(), c.top(), max(c.left() + 1, c.right() + dx),
                               max(c.top() + 1, c.bottom() + dy))
            else:
                x = min(max(0.0, c.x() + dx), self._img_w - c.width())
                y = min(max(0.0, c.y() + dy), self._img_h - c.height())
                self._set_crop(x, y, x + c.width(), y + c.height())
            self.selectionFinished.emit()
            return
        super().keyPressEvent(e)

    def keyReleaseEvent(self, e):
        if e.key() in (Qt.Key.Key_Control, Qt.Key.Key_Shift):
            self._modifier_changed(e.modifiers())
            return
        if e.key() == Qt.Key.Key_Space and not e.isAutoRepeat():
            self._space = False
            if self._mode is None:
                self.setCursor(Qt.CursorShape.CrossCursor)
            return
        super().keyReleaseEvent(e)

    def focusOutEvent(self, e):
        self._space = False
        super().focusOutEvent(e)

    # ---------------- vẽ ----------------
    def paintEvent(self, _e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(BG))
        if not self.has_image:
            self._paint_empty(p)
            return

        self._paint_image(p)
        img_r = self.to_screen_rect(QRectF(0, 0, self._img_w, self._img_h))
        dragging = self._mode not in (None, "pan") and self._started

        if self.has_selection:
            cr = self.to_screen_rect(self._crop)
            # làm tối phần nằm ngoài vùng chọn
            path = QPainterPath()
            path.setFillRule(Qt.FillRule.OddEvenFill)
            path.addRect(img_r)
            path.addRect(cr)
            p.fillPath(path, QColor(0, 0, 0, 150))

            if dragging:  # lưới 1/3 khi đang kéo
                p.setPen(QPen(QColor(255, 255, 255, 110), 1))
                for i in (1, 2):
                    x = cr.left() + cr.width() * i / 3
                    y = cr.top() + cr.height() * i / 3
                    p.drawLine(QPointF(x, cr.top()), QPointF(x, cr.bottom()))
                    p.drawLine(QPointF(cr.left(), y), QPointF(cr.right(), y))

            p.setPen(QPen(QColor(255, 255, 255, 230), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(cr)
            self._paint_handles(p, cr)
            if dragging:
                self._paint_badge(p, cr)
        else:
            self._paint_tip(p, img_r, "Nhấn giữ chuột trái và kéo để chọn vùng cần cắt")

        if not dragging and self._mode is None and not self._space and self._hover is not None \
                and img_r.contains(self._hover) and self._hit_test(self._hover) is None:
            self._paint_guides(p, img_r, self._hover)

        if self._drop_hover:
            p.fillRect(self.rect(), QColor(0, 0, 0, 140))
            self._paint_drop_frame(p, QRectF(self.rect()).adjusted(14, 14, -14, -14), "Thả để mở ảnh mới")

    def _paint_image(self, p):
        dpr = self.devicePixelRatioF()
        target = self.to_screen_rect(QRectF(0, 0, self._img_w, self._img_h))
        z = self._scale * dpr
        if z < 1.0:
            # thu nhỏ: dùng bản scale sẵn (mượt, nhanh khi kéo)
            tw, th = max(1, round(self._img_w * z)), max(1, round(self._img_h * z))
            if self._cache_key != (tw, th, dpr):
                self._cache = self._pix.scaled(tw, th, Qt.AspectRatioMode.IgnoreAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation)
                self._cache.setDevicePixelRatio(dpr)
                self._cache_key = (tw, th, dpr)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            p.drawPixmap(target.topLeft(), self._cache)
        else:
            # phóng to: chỉ vẽ phần đang thấy; zoom lớn thì giữ pixel sắc nét
            vis = target.intersected(QRectF(self.rect()))
            if vis.isEmpty():
                return
            src = QRectF((vis.left() - self._offset.x()) / self._scale,
                         (vis.top() - self._offset.y()) / self._scale,
                         vis.width() / self._scale, vis.height() / self._scale)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, z < 2.5)
            p.drawPixmap(vis, self._pix, src)

    def _paint_handles(self, p, r):
        th, ln, mid = 4.0, 22.0, 28.0
        L, T, R, B = r.left(), r.top(), r.right(), r.bottom()
        lw = min(ln, max(8.0, r.width() / 2))
        lh = min(ln, max(8.0, r.height() / 2))
        rects = [
            QRectF(L - th, T - th, lw + th, th), QRectF(L - th, T - th, th, lh + th),   # trên trái
            QRectF(R - lw, T - th, lw + th, th), QRectF(R, T - th, th, lh + th),        # trên phải
            QRectF(L - th, B, lw + th, th), QRectF(L - th, B - lh, th, lh + th),        # dưới trái
            QRectF(R - lw, B, lw + th, th), QRectF(R, B - lh, th, lh + th),             # dưới phải
        ]
        if r.width() > 3 * ln:
            cx = r.center().x()
            rects += [QRectF(cx - mid / 2, T - th, mid, th), QRectF(cx - mid / 2, B, mid, th)]
        if r.height() > 3 * ln:
            cy = r.center().y()
            rects += [QRectF(L - th, cy - mid / 2, th, mid), QRectF(R, cy - mid / 2, th, mid)]
        shadow, white = QColor(0, 0, 0, 110), QColor(255, 255, 255)
        for rr in rects:
            p.fillRect(rr.adjusted(-1, -1, 1, 1), shadow)
        for rr in rects:
            p.fillRect(rr, white)

    def _paint_guides(self, p, img_r, pos):
        """Đường dóng ngang/dọc theo con trỏ + toạ độ pixel, giúp chọn điểm bắt đầu chính xác."""
        pen = QPen(QColor(255, 255, 255, 120), 1)
        pen.setDashPattern([4, 4])
        p.setPen(pen)
        p.drawLine(QPointF(pos.x(), img_r.top()), QPointF(pos.x(), img_r.bottom()))
        p.drawLine(QPointF(img_r.left(), pos.y()), QPointF(img_r.right(), pos.y()))
        ip = self.to_img(pos)
        x = int(min(max(0.0, ip.x()), self._img_w))
        y = int(min(max(0.0, ip.y()), self._img_h))
        text = f"left {x} · top {y}"
        f = QFont(self.font())
        f.setPointSizeF(9)
        p.setFont(f)
        fm = QFontMetricsF(f)
        bw, bh = fm.horizontalAdvance(text) + 14, fm.height() + 8
        bx, by = pos.x() + 14, pos.y() + 16
        if bx + bw > self.width() - 4:
            bx = pos.x() - bw - 10
        if by + bh > self.height() - 4:
            by = pos.y() - bh - 10
        box = QRectF(bx, by, bw, bh)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 190))
        p.drawRoundedRect(box, 4, 4)
        p.setPen(QColor("#ffffff"))
        p.drawText(box, Qt.AlignmentFlag.AlignCenter, text)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    def _paint_tip(self, p, img_r, text):
        """Nhãn hướng dẫn nổi phía trên ảnh khi chưa chọn vùng."""
        f = QFont(self.font())
        f.setPointSizeF(10)
        p.setFont(f)
        fm = QFontMetricsF(f)
        bw, bh = fm.horizontalAdvance(text) + 28, fm.height() + 14
        visible = img_r.intersected(QRectF(self.rect()))
        x = visible.center().x() - bw / 2
        y = max(8.0, visible.top() + 12)
        box = QRectF(min(max(4.0, x), self.width() - bw - 4), y, bw, bh)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(QColor(ACCENT), 1))
        p.setBrush(QColor(10, 10, 10, 215))
        p.drawRoundedRect(box, bh / 2, bh / 2)
        p.setPen(QColor("#ffffff"))
        p.drawText(box, Qt.AlignmentFlag.AlignCenter, text)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    def _paint_badge(self, p, cr):
        l, t, w, h = self.crop_values()
        text = f"{w} × {h}    top {t} · left {l}"
        f = QFont(self.font())
        f.setPointSizeF(9.5)
        p.setFont(f)
        fm = QFontMetricsF(f)
        bw, bh = fm.horizontalAdvance(text) + 18, fm.height() + 10
        x = cr.center().x() - bw / 2
        y = cr.bottom() + 14
        if y + bh > self.height() - 4:
            y = cr.bottom() - bh - 12
        x = min(max(4.0, x), self.width() - bw - 4)
        y = max(4.0, y)
        box = QRectF(x, y, bw, bh)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 205))
        p.drawRoundedRect(box, 5, 5)
        p.setPen(QColor("#ffffff"))
        p.drawText(box, Qt.AlignmentFlag.AlignCenter, text)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    def _paint_drop_frame(self, p, box, title, subtitle=None):
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        hover = self._drop_hover
        col = QColor(ACCENT) if hover else QColor("#5c5c5c")
        pen = QPen(col, 2)
        pen.setDashPattern([5, 4])
        p.setPen(pen)
        p.setBrush(QColor(76, 194, 255, 22) if hover else Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(box, 14, 14)

        # biểu tượng cắt
        cx, cy = box.center().x(), box.center().y() - 38
        ip = QPen(QColor(ACCENT) if hover else QColor("#c8c8c8"), 4)
        ip.setCapStyle(Qt.PenCapStyle.SquareCap)
        p.setPen(ip)
        p.drawLine(QPointF(cx - 10, cy - 22), QPointF(cx - 10, cy + 10))
        p.drawLine(QPointF(cx - 10, cy + 10), QPointF(cx + 22, cy + 10))
        p.drawLine(QPointF(cx - 22, cy - 10), QPointF(cx + 10, cy - 10))
        p.drawLine(QPointF(cx + 10, cy - 10), QPointF(cx + 10, cy + 22))

        f = QFont(self.font())
        f.setPointSizeF(15)
        f.setWeight(QFont.Weight.DemiBold)
        p.setFont(f)
        p.setPen(QColor("#f0f0f0"))
        p.drawText(QRectF(box.left(), cy + 36, box.width(), 32), Qt.AlignmentFlag.AlignCenter, title)
        if subtitle:
            f2 = QFont(self.font())
            f2.setPointSizeF(10)
            p.setFont(f2)
            p.setPen(QColor("#9a9a9a"))
            p.drawText(QRectF(box.left() + 16, cy + 72, box.width() - 32, 44),
                       Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                       subtitle)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    def _paint_empty(self, p):
        w = min(540.0, self.width() - 60.0)
        h = min(300.0, self.height() - 60.0)
        box = QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h)
        if self._drop_hover:
            self._paint_drop_frame(p, box, "Thả ảnh để mở")
        else:
            self._paint_drop_frame(p, box, "Kéo & thả ảnh vào đây",
                                   "hoặc bấm vào đây để chọn ảnh  ·  Ctrl+V để dán ảnh từ clipboard")


class ElidedLabel(QLabel):
    """QLabel tự rút gọn chữ bằng '…' khi không đủ chỗ (thay vì bị cắt cụt)."""

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setFont(self.font())
        p.setPen(self.palette().color(QPalette.ColorRole.WindowText))
        r = self.contentsRect()
        text = self.fontMetrics().elidedText(self.text(), Qt.TextElideMode.ElideRight, r.width())
        p.drawText(r, int(self.alignment()), text)


# --------------------------------------------------------------------------- #
#  Cửa sổ chính
# --------------------------------------------------------------------------- #
class MainWindow(QMainWindow):
    HINT = ("Giữ chuột trái + kéo: chọn vùng (Shift: vuông)  ·  Ctrl + kéo: di chuyển vùng  ·  "
            "Lăn chuột: zoom  ·  Chuột phải: kéo ảnh  ·  Esc: bỏ chọn  ·  Thả chuột: tự sao chép")

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1180, 760)
        self.setAcceptDrops(True)
        self._exts = supported_exts()
        self._file_path = None
        self._name = None
        self._drag_ok = False

        central = QWidget(objectName="central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- thanh trên ----
        top = QFrame(objectName="topBar")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(14, 10, 14, 10)
        tl.setSpacing(6)
        self.btn_zoom_out = self._button("−", "Thu nhỏ (Ctrl+-)", square=True)
        self.lbl_zoom = QLabel("—", objectName="zoomLabel")
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_zoom.setFixedWidth(54)
        self.btn_zoom_in = self._button("+", "Phóng to (Ctrl+=)", square=True)
        self.btn_fit = self._button("Vừa khung", "Vừa cửa sổ (Ctrl+0)")
        self.btn_100 = self._button("100%", "Kích thước thật (Ctrl+1)")
        self.btn_all = self._button("Cả ảnh", "Chọn toàn bộ ảnh (Ctrl+A)")
        self.btn_reset = self._button("Bỏ chọn", "Bỏ vùng đang chọn để kéo chọn lại (Esc)")
        for wdg in (self.btn_zoom_out, self.lbl_zoom, self.btn_zoom_in, self.btn_fit, self.btn_100):
            tl.addWidget(wdg)
        tl.addWidget(self._vsep())
        tl.addWidget(self.btn_all)
        tl.addWidget(self.btn_reset)
        tl.addStretch(1)

        self.btn_open = self._button("Mở ảnh…", "Mở ảnh (Ctrl+O)")
        tl.addWidget(self.btn_open)
        lbl_aspect = QLabel("Tỉ lệ", objectName="muted")
        tl.addSpacing(8)
        tl.addWidget(lbl_aspect)
        self.cmb_aspect = QComboBox()
        self.cmb_aspect.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for name, _ in ASPECTS:
            self.cmb_aspect.addItem(name)
        tl.addWidget(self.cmb_aspect)
        root.addWidget(top)

        # ---- vùng ảnh ----
        self.canvas = CropCanvas()
        root.addWidget(self.canvas, 1)

        # ---- thanh dưới ----
        bottom = QFrame(objectName="bottomBar")
        bl = QVBoxLayout(bottom)
        bl.setContentsMargins(14, 8, 14, 12)
        bl.setSpacing(8)

        row1 = QHBoxLayout()
        self.lbl_info = QLabel("Chưa có ảnh", objectName="info")
        self.lbl_hint = ElidedLabel(self.HINT, objectName="muted")
        self.lbl_hint.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_hint.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.lbl_hint.setToolTip(self.HINT)
        row1.addWidget(self.lbl_info)
        row1.addSpacing(16)
        row1.addWidget(self.lbl_hint, 1)
        bl.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(6)
        self.txt_result = QLineEdit(objectName="result")
        self.txt_result.setReadOnly(True)
        self.txt_result.setAcceptDrops(False)
        self.txt_result.setPlaceholderText(
            "Nhấn giữ chuột trái và kéo trên ảnh — top / left / width / height sẽ hiện ở đây")
        self._ui_font = QFont(self.txt_result.font())
        self._mono_font = QFont("Consolas")
        self._mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self._mono_font.setPointSizeF(10.5)
        # placeholder dùng font thường, kết quả dùng font monospace
        self.txt_result.textChanged.connect(
            lambda t: self.txt_result.setFont(self._mono_font if t else self._ui_font))
        self.cmb_format = QComboBox()
        self.cmb_format.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for name, _ in FORMATS:
            self.cmb_format.addItem(name)
        self.btn_copy = self._button("Sao chép", "Sao chép đoạn toạ độ (Enter / Ctrl+C)")
        self.btn_copy.setMinimumWidth(118)
        self.btn_save = self._button("Lưu ảnh cắt…", "Lưu phần ảnh trong khung ra file (Ctrl+S)")
        row2.addWidget(self.txt_result, 1)
        row2.addWidget(self.cmb_format)
        row2.addWidget(self.btn_copy)
        row2.addWidget(self.btn_save)
        bl.addLayout(row2)
        root.addWidget(bottom)

        # ---- kết nối ----
        self.btn_zoom_out.clicked.connect(self.canvas.zoom_out)
        self.btn_zoom_in.clicked.connect(self.canvas.zoom_in)
        self.btn_fit.clicked.connect(self.canvas.fit)
        self.btn_100.clicked.connect(lambda: self.canvas.set_zoom(1.0))
        self.btn_all.clicked.connect(self.canvas.select_all)
        self.btn_reset.clicked.connect(self.canvas.clear_selection)
        self.btn_open.clicked.connect(self.open_dialog)
        self.btn_copy.clicked.connect(self.copy_result)
        self.btn_save.clicked.connect(self.save_crop)
        self.cmb_aspect.currentIndexChanged.connect(lambda i: self.canvas.set_aspect(ASPECTS[i][1]))
        self.cmb_format.currentIndexChanged.connect(lambda _i: self._render_result())
        self.canvas.selectionChanged.connect(self._on_selection)
        self.canvas.selectionFinished.connect(self.copy_result)   # thả chuột → tự sao chép
        self.canvas.zoomChanged.connect(lambda z: self.lbl_zoom.setText(f"{round(z * 100)}%"))
        self.canvas.openRequested.connect(self.open_dialog)

        self._copy_timer = QTimer(self, singleShot=True, interval=1600)
        self._copy_timer.timeout.connect(lambda: self.btn_copy.setText("Sao chép"))
        self._hint_timer = QTimer(self, singleShot=True, interval=3500)
        self._hint_timer.timeout.connect(self._restore_hint)

        self._shortcut("Ctrl+O", self.open_dialog)
        self._shortcut("Ctrl+V", self.paste)
        self._shortcut(["Return", "Enter", "Ctrl+C", "Ctrl+Shift+C"], self.copy_result)
        self._shortcut("Ctrl+S", self.save_crop)
        self._shortcut("Esc", self.escape)
        self._shortcut("Ctrl+A", self.canvas.select_all)
        self._shortcut("Ctrl+0", self.canvas.fit)
        self._shortcut("Ctrl+1", lambda: self.canvas.set_zoom(1.0))
        self._shortcut(["Ctrl+=", "Ctrl++"], self.canvas.zoom_in)
        self._shortcut("Ctrl+-", self.canvas.zoom_out)

        self._update_controls()
        self.canvas.setFocus()
        _dark_title_bar(self)

    # ---------- tiện ích UI ----------
    def _button(self, text, tip, square=False):
        b = QPushButton(text)
        b.setToolTip(tip)
        b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if square:
            b.setObjectName("square")
            b.setFixedWidth(34)
        return b

    def _vsep(self):
        s = QFrame(objectName="vsep")
        s.setFixedSize(1, 22)
        return s

    def _shortcut(self, keys, slot):
        act = QAction(self)
        keys = keys if isinstance(keys, list) else [keys]
        act.setShortcuts([QKeySequence(k) for k in keys])
        act.triggered.connect(slot)
        self.addAction(act)

    def _notify(self, msg, error=False):
        self.lbl_hint.setText(msg)
        self.lbl_hint.setStyleSheet(f"color: {'#ff8a80' if error else ACCENT};")
        self._hint_timer.start()

    def _restore_hint(self):
        self.lbl_hint.setText(self.HINT)
        self.lbl_hint.setStyleSheet("")

    def _update_controls(self):
        has = self.canvas.has_image
        sel = self.canvas.has_selection
        for wdg in (self.btn_zoom_out, self.btn_zoom_in, self.btn_fit, self.btn_100, self.btn_all):
            wdg.setEnabled(has)
        for wdg in (self.btn_reset, self.btn_save):
            wdg.setEnabled(sel)
        self.btn_copy.setEnabled(bool(self.txt_result.text()))

    def _on_selection(self):
        """Gọi liên tục trong lúc kéo → ô kết quả cập nhật trực tiếp."""
        if not self.canvas.has_image:
            self.lbl_info.setText("Chưa có ảnh")
        else:
            W, H = self.canvas.image_size()
            suffix = "" if self.canvas.has_selection else "   ·   Chưa chọn vùng"
            self.lbl_info.setText(f"Ảnh {W} × {H} px{suffix}")
        if self.canvas.has_selection:
            self._restore_hint()
        self._render_result()

    def escape(self):
        if not self.canvas.cancel_drag():
            self.canvas.clear_selection()

    # ---------- mở ảnh ----------
    def _is_image_file(self, path):
        if not os.path.isfile(path):
            return False
        if os.path.splitext(path)[1].lower() in self._exts:
            return True
        return QImageReader(path).canRead()

    def open_dialog(self):
        start = os.path.dirname(self._file_path) if self._file_path else ""
        pattern = " ".join("*" + e for e in sorted(self._exts))
        path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh", start,
                                              f"Ảnh ({pattern});;Tất cả file (*)")
        if path:
            self.load_path(path)

    def load_path(self, path):
        reader = QImageReader(path)
        reader.setAutoTransform(True)   # xoay theo EXIF giống trình xem ảnh
        img = reader.read()
        if img.isNull():
            QMessageBox.warning(self, APP_NAME, f"Không mở được ảnh:\n{path}\n\n{reader.errorString()}")
            return False
        self._file_path = path
        self._set_image(img, os.path.basename(path))
        return True

    def _set_image(self, img, name):
        self._name = name
        self.canvas.set_image(img)
        self.setWindowTitle(f"{name}  ({img.width()} × {img.height()})  —  {APP_NAME}")
        self._update_controls()
        self.canvas.setFocus()

    def paste(self):
        cb = QGuiApplication.clipboard()
        mime = cb.mimeData()
        if mime is not None and mime.hasUrls():
            for u in mime.urls():
                if u.isLocalFile() and self._is_image_file(u.toLocalFile()):
                    self.load_path(u.toLocalFile())
                    return
        if mime is not None and mime.hasImage():
            img = cb.image()
            if not img.isNull():
                self._file_path = None
                self._set_image(img, "Ảnh từ clipboard")
                return
        txt = cb.text().strip().strip('"')
        if txt and self._is_image_file(txt):
            self.load_path(txt)
            return
        self._notify("Clipboard không có ảnh", error=True)

    # ---------- kéo thả ----------
    def _local_image_from(self, mime):
        if mime.hasUrls():
            for u in mime.urls():
                if u.isLocalFile() and self._is_image_file(u.toLocalFile()):
                    return u.toLocalFile()
        return None

    def dragEnterEvent(self, e):
        mime = e.mimeData()
        self._drag_ok = bool(self._local_image_from(mime)) or mime.hasImage()
        if self._drag_ok:
            e.acceptProposedAction()
            self.canvas.set_drop_hover(True)
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if self._drag_ok:
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragLeaveEvent(self, e):
        self.canvas.set_drop_hover(False)

    def dropEvent(self, e):
        self.canvas.set_drop_hover(False)
        mime = e.mimeData()
        path = self._local_image_from(mime)
        if path and self.load_path(path):
            e.acceptProposedAction()
            return
        if mime.hasImage():
            data = mime.imageData()
            img = data.toImage() if isinstance(data, QPixmap) else data
            if isinstance(img, QImage) and not img.isNull():
                self._file_path = None
                self._set_image(img, "Ảnh được thả vào")
                e.acceptProposedAction()
                return
        self._notify("Không đọc được ảnh vừa thả", error=True)

    # ---------- kết quả ----------
    def _render_result(self):
        vals = self.canvas.crop_values()
        if vals is None:
            self.txt_result.clear()
        else:
            l, t, w, h = vals
            fmt = FORMATS[self.cmb_format.currentIndex()][1]
            self.txt_result.setText(fmt({"top": t, "left": l, "width": w, "height": h}))
            self.txt_result.setCursorPosition(0)
        self._update_controls()

    def copy_result(self):
        text = self.txt_result.text()
        if not text:
            if self.canvas.has_image:
                self._notify("Hãy nhấn giữ chuột trái và kéo để chọn vùng trước", error=True)
            return
        QGuiApplication.clipboard().setText(text)
        self.btn_copy.setText("Đã sao chép ✓")
        self._copy_timer.start()

    def save_crop(self):
        vals = self.canvas.crop_values()
        if vals is None:
            return
        l, t, w, h = vals
        if self._file_path:
            base = os.path.splitext(self._file_path)[0]
        else:
            base = os.path.join(os.path.expanduser("~"), "anh")
        default = f"{base}_crop_{l}_{t}_{w}x{h}.png"
        path, _ = QFileDialog.getSaveFileName(self, "Lưu ảnh đã cắt", default,
                                              "PNG (*.png);;JPEG (*.jpg *.jpeg);;WebP (*.webp);;BMP (*.bmp)")
        if not path:
            return
        if not os.path.splitext(path)[1]:
            path += ".png"
        if self.canvas.image().copy(l, t, w, h).save(path):
            self._notify(f"Đã lưu: {os.path.basename(path)}")
        else:
            QMessageBox.warning(self, APP_NAME, f"Không lưu được file:\n{path}")


# --------------------------------------------------------------------------- #
#  Giao diện tối + khởi chạy
# --------------------------------------------------------------------------- #
STYLE = f"""
QWidget#central {{ background: {BG}; }}
QFrame#topBar, QFrame#bottomBar {{ background: #1b1b1b; }}
QFrame#topBar {{ border-bottom: 1px solid #2c2c2c; }}
QFrame#bottomBar {{ border-top: 1px solid #2c2c2c; }}
QFrame#vsep {{ background: #3a3a3a; }}
QLabel {{ color: #d8d8d8; }}
QLabel#muted {{ color: #8c8c8c; }}
QLabel#info {{ color: #e6e6e6; }}
QLabel#zoomLabel {{ color: #e6e6e6; }}
QPushButton {{
    background: #2c2c2c; color: #ececec; border: 1px solid #3a3a3a;
    border-radius: 6px; padding: 6px 12px;
}}
QPushButton:hover {{ background: #383838; }}
QPushButton:pressed {{ background: #242424; }}
QPushButton:disabled {{ color: #666; background: #242424; border-color: #2e2e2e; }}
QPushButton#square {{ padding: 4px 0; font-size: 15px; }}
QPushButton#accent {{
    background: {ACCENT}; color: #0a0a0a; border: none; font-weight: 600; padding: 7px 20px;
}}
QPushButton#accent:hover {{ background: #74d1ff; }}
QPushButton#accent:pressed {{ background: #3aa9e0; }}
QPushButton#accent:disabled {{ background: #2b4250; color: #73838c; }}
QComboBox {{
    background: #2c2c2c; color: #ececec; border: 1px solid #3a3a3a;
    border-radius: 6px; padding: 5px 10px; min-width: 84px;
}}
QComboBox:hover {{ background: #383838; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{ image: url(__ARROW__); width: 10px; height: 6px; margin-right: 8px; }}
QComboBox QAbstractItemView {{
    background: #2b2b2b; color: #ececec; border: 1px solid #3a3a3a;
    selection-background-color: #31556a; outline: 0;
}}
QLineEdit#result {{
    background: #121212; color: #f4f4f4; border: 1px solid #3a3a3a;
    border-radius: 6px; padding: 7px 10px; selection-background-color: #2d6f94;
}}
QLineEdit#result:focus {{ border-color: {ACCENT}; }}
QToolTip {{ background: #2b2b2b; color: #eee; border: 1px solid #444; padding: 4px 6px; }}
"""


def apply_dark(app):
    app.setStyle("Fusion")
    pal = QPalette()
    roles = {
        QPalette.ColorRole.Window: "#202020", QPalette.ColorRole.WindowText: "#e6e6e6",
        QPalette.ColorRole.Base: "#151515", QPalette.ColorRole.AlternateBase: "#262626",
        QPalette.ColorRole.Text: "#e6e6e6", QPalette.ColorRole.Button: "#2c2c2c",
        QPalette.ColorRole.ButtonText: "#e6e6e6", QPalette.ColorRole.Highlight: "#2d6f94",
        QPalette.ColorRole.HighlightedText: "#ffffff", QPalette.ColorRole.ToolTipBase: "#2b2b2b",
        QPalette.ColorRole.ToolTipText: "#eeeeee", QPalette.ColorRole.PlaceholderText: "#7a7a7a",
    }
    for role, col in roles.items():
        pal.setColor(role, QColor(col))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#666"))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#666"))
    app.setPalette(pal)
    app.setStyleSheet(STYLE.replace("__ARROW__", _arrow_png()))


def _arrow_png():
    """Vẽ mũi tên ▾ cho QComboBox, lưu ra thư mục tạm (stylesheet cần đường dẫn file)."""
    import tempfile
    path = os.path.join(tempfile.gettempdir(), "crop_tool_arrow.png")
    pm = QPixmap(20, 12)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(QColor("#c8c8c8"), 2.4)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.drawLine(QPointF(3, 3), QPointF(10, 9))
    p.drawLine(QPointF(10, 9), QPointF(17, 3))
    p.end()
    pm.save(path)
    return path.replace("\\", "/")


def make_icon():
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#2a2a2a"))
    p.drawRoundedRect(2, 2, 60, 60, 13, 13)
    pen = QPen(QColor(ACCENT), 6)
    pen.setCapStyle(Qt.PenCapStyle.SquareCap)
    p.setPen(pen)
    p.drawLine(22, 12, 22, 42)
    p.drawLine(22, 42, 52, 42)
    pen.setColor(QColor("#ffffff"))
    p.setPen(pen)
    p.drawLine(12, 22, 42, 22)
    p.drawLine(42, 22, 42, 52)
    p.end()
    return QIcon(pm)


def _dark_title_bar(widget):
    """Thanh tiêu đề tối trên Windows 10/11."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = int(widget.winId())
        val = ctypes.c_int(1)
        for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (mới / cũ)
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(val),
                                                          ctypes.sizeof(val)) == 0:
                break
    except Exception:
        pass


def _install_error_popup():
    """pythonw không có console nên lỗi bị ẩn — hiện lỗi bằng hộp thoại và ghi ra file log."""
    import tempfile
    import traceback
    log_path = os.path.join(tempfile.gettempdir(), "crop_tool_error.log")
    showing = [False]

    def hook(exc_type, exc, tb):
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception:
            pass
        if showing[0] or QApplication.instance() is None:
            return
        showing[0] = True
        try:
            QMessageBox.critical(None, APP_NAME,
                                 f"Có lỗi xảy ra (app vẫn tiếp tục chạy):\n\n{exc_type.__name__}: {exc}"
                                 f"\n\nChi tiết đã ghi vào:\n{log_path}")
        finally:
            showing[0] = False

    sys.excepthook = hook


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("croptool.coords")
        except Exception:
            pass
    _install_error_popup()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    apply_dark(app)
    app.setWindowIcon(make_icon())

    win = MainWindow()
    win.show()
    path = next((a for a in sys.argv[1:] if os.path.isfile(a)), None)
    if path:
        QTimer.singleShot(0, lambda: win.load_path(path))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()