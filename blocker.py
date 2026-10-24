"""
نظام الحجب: تعديل ملف hosts لإعادة توجيه الدومينات الممنوعة إلى 127.0.0.1.
بيحترم القائمة البيضاء (allow) فلا يحجبها حتى لو اتطابقت.
"""
import os
import shutil
import ctypes
import sys

import config
import database as db


def is_admin():
    """هل البرنامج شغال بصلاحيات admin (مطلوبة لتعديل hosts)."""
    if sys.platform.startswith("win"):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    return os.geteuid() == 0


def _read_hosts():
    try:
        with open(config.HOSTS_PATH, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def _strip_our_block(content):
    """نشيل الكتلة القديمة بتاعتنا من محتوى hosts."""
    start = config.HOSTS_MARK_START
    end = config.HOSTS_MARK_END
    if start in content and end in content:
        before = content.split(start)[0]
        after = content.split(end, 1)[1]
        return (before.rstrip() + "\n" + after.lstrip()).strip() + "\n"
    return content


def apply_blocking():
    """
    نكتب كتلة الحجب في ملف hosts بناءً على القائمة السوداء،
    مع استثناء القائمة البيضاء. بيرجّع (نجاح, رسالة).
    """
    if not is_admin():
        return False, "محتاج صلاحيات مدير (Run as administrator) عشان أعدل ملف hosts."

    block_list = set(db.get_domains("block"))
    allow_list = set(db.get_domains("allow"))
    effective = sorted(block_list - allow_list)

    content = _read_hosts()
    content = _strip_our_block(content)

    lines = [config.HOSTS_MARK_START]
    for d in effective:
        lines.append(f"{config.REDIRECT_IP} {d}")
    lines.append(config.HOSTS_MARK_END)
    block_text = "\n".join(lines) + "\n"

    new_content = content.rstrip() + "\n\n" + block_text

    # نسخة احتياطية مرة واحدة
    backup = config.HOSTS_PATH + ".antiporn.bak"
    if not os.path.exists(backup):
        try:
            shutil.copy2(config.HOSTS_PATH, backup)
        except Exception:
            pass

    try:
        with open(config.HOSTS_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        _flush_dns()
        return True, f"تم تفعيل الحجب على {len(effective)} دومين."
    except PermissionError:
        return False, "مرفوض الوصول لملف hosts. شغّل البرنامج كمدير."
    except Exception as e:
        return False, f"خطأ: {e}"


def remove_blocking():
    """نشيل كتلة الحجب بتاعتنا من hosts (إيقاف الحجب)."""
    if not is_admin():
        return False, "محتاج صلاحيات مدير عشان أعدل ملف hosts."
    content = _read_hosts()
    new_content = _strip_our_block(content)
    try:
        with open(config.HOSTS_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        _flush_dns()
        return True, "تم إيقاف الحجب."
    except Exception as e:
        return False, f"خطأ: {e}"


def _flush_dns():
    """تفريغ كاش DNS عشان الحجب يسري فورًا."""
    try:
        if sys.platform.startswith("win"):
            os.system("ipconfig /flushdns >nul 2>&1")
    except Exception:
        pass


def sync():
    """يعيد تطبيق الحجب حسب الإعداد الحالي (blocking_enabled)."""
    if db.get_bool("blocking_enabled"):
        return apply_blocking()
    else:
        return remove_blocking()
