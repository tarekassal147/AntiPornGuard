"""
الإعدادات العامة ومسارات الملفات للتطبيق.
"""
import os
import sys

# المسار الأساسي للبيانات: %LOCALAPPDATA%\AntiPornGuard على ويندوز، وإلا مجلد home
if sys.platform.startswith("win"):
    BASE_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "AntiPornGuard")
else:
    BASE_DIR = os.path.join(os.path.expanduser("~"), ".antiporn_guard")

os.makedirs(BASE_DIR, exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, "guard.db")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# مسار ملف hosts حسب النظام
if sys.platform.startswith("win"):
    HOSTS_PATH = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "drivers", "etc", "hosts")
else:
    HOSTS_PATH = "/etc/hosts"

# العلامات اللي بنحط بينها الحجب في ملف hosts عشان نعرف نشيله بسهولة
HOSTS_MARK_START = "# >>> AntiPornGuard START >>>"
HOSTS_MARK_END = "# <<< AntiPornGuard END <<<"

REDIRECT_IP = "127.0.0.1"

APP_NAME = "AntiPorn Guard"
APP_VERSION = "1.0.0"

# الإعدادات الافتراضية (بتتخزن في قاعدة البيانات وبتتعدل من الواجهة)
DEFAULTS = {
    "blocking_enabled": "1",
    "screenshot_enabled": "0",
    "screenshot_interval_min": "15",   # دقائق
    "time_limit_enabled": "0",
    "allowed_start": "08:00",
    "allowed_end": "22:00",
    "keyword_filter_enabled": "1",
}
