"""
خدمة المراقبة الخلفية:
  - لقطات شاشة دورية
  - فرض حدود وقت الاستخدام (قفل/تنبيه خارج الساعات المسموحة)
  - تشغيل في خيط منفصل
"""
import os
import time
import threading
from datetime import datetime

import config
import database as db

try:
    from PIL import ImageGrab  # Pillow
    _HAS_PIL = True
except Exception:
    _HAS_PIL = False


class MonitorService:
    def __init__(self, on_time_violation=None):
        self._stop = threading.Event()
        self._thread = None
        self._last_shot = 0
        self.on_time_violation = on_time_violation  # callback تنادى لما نكون خارج الوقت المسموح

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception:
                pass
            # نتأكد كل 20 ثانية
            self._stop.wait(20)

    def _tick(self):
        now = time.time()

        # --- لقطات الشاشة ---
        if db.get_bool("screenshot_enabled") and _HAS_PIL:
            interval = int(db.get_setting("screenshot_interval_min", "15")) * 60
            if now - self._last_shot >= interval:
                self._take_screenshot()
                self._last_shot = now

        # --- حدود الوقت ---
        if db.get_bool("time_limit_enabled"):
            if not self._within_allowed_hours():
                db.log_event("-", "time_block")
                if self.on_time_violation:
                    self.on_time_violation()

    def _take_screenshot(self):
        try:
            img = ImageGrab.grab()
            fname = datetime.now().strftime("shot_%Y%m%d_%H%M%S.png")
            img.save(os.path.join(config.SCREENSHOT_DIR, fname))
            db.log_event("screenshot", "capture")
        except Exception:
            pass

    @staticmethod
    def _within_allowed_hours():
        start = db.get_setting("allowed_start", "08:00")
        end = db.get_setting("allowed_end", "22:00")
        try:
            sh, sm = map(int, start.split(":"))
            eh, em = map(int, end.split(":"))
        except Exception:
            return True
        now = datetime.now()
        cur = now.hour * 60 + now.minute
        s = sh * 60 + sm
        e = eh * 60 + em
        if s <= e:
            return s <= cur <= e
        else:  # الفترة بتعدي منتصف الليل
            return cur >= s or cur <= e
