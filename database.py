"""
طبقة قاعدة البيانات SQLite: الإعدادات، القوائم، الكلمات الممنوعة، والسجل.
"""
import sqlite3
import hashlib
import os
import secrets
from datetime import datetime

import config


def _conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """تجهيز الجداول وأول تشغيل."""
    conn = _conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS auth (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        salt TEXT,
        pwd_hash TEXT
    )""")

    # type: 'block' = قائمة سوداء، 'allow' = قائمة بيضاء
    c.execute("""CREATE TABLE IF NOT EXISTS domains (
        domain TEXT PRIMARY KEY,
        list_type TEXT NOT NULL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS keywords (
        word TEXT PRIMARY KEY
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS visit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        domain TEXT,
        action TEXT
    )""")

    conn.commit()

    # زرع الإعدادات الافتراضية لو مش موجودة
    for k, v in config.DEFAULTS.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()

    _seed_default_domains()


def _seed_default_domains():
    """نزرع قائمة مبدئية صغيرة من الدومينات لو القائمة فاضية."""
    existing = get_domains("block")
    if existing:
        return
    seed = [
        "pornhub.com", "www.pornhub.com",
        "xvideos.com", "www.xvideos.com",
        "xnxx.com", "www.xnxx.com",
        "xhamster.com", "www.xhamster.com",
        "redtube.com", "www.redtube.com",
        "youporn.com", "www.youporn.com",
        "spankbang.com", "www.spankbang.com",
        "chaturbate.com", "www.chaturbate.com",
    ]
    for d in seed:
        add_domain(d, "block")


# ---------- الإعدادات ----------
def get_setting(key, default=None):
    conn = _conn()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = _conn()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()


def get_bool(key):
    return get_setting(key, "0") == "1"


# ---------- الباسورد ----------
def is_password_set():
    conn = _conn()
    row = conn.execute("SELECT 1 FROM auth WHERE id = 1").fetchone()
    conn.close()
    return row is not None


def _hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000).hex()


def set_password(password):
    salt = secrets.token_hex(16)
    pwd_hash = _hash(password, salt)
    conn = _conn()
    conn.execute("INSERT OR REPLACE INTO auth (id, salt, pwd_hash) VALUES (1, ?, ?)", (salt, pwd_hash))
    conn.commit()
    conn.close()


def check_password(password):
    conn = _conn()
    row = conn.execute("SELECT salt, pwd_hash FROM auth WHERE id = 1").fetchone()
    conn.close()
    if not row:
        return False
    return secrets.compare_digest(_hash(password, row["salt"]), row["pwd_hash"])


# ---------- الدومينات ----------
def get_domains(list_type):
    conn = _conn()
    rows = conn.execute("SELECT domain FROM domains WHERE list_type = ? ORDER BY domain", (list_type,)).fetchall()
    conn.close()
    return [r["domain"] for r in rows]


def add_domain(domain, list_type):
    domain = domain.strip().lower()
    if not domain:
        return
    conn = _conn()
    conn.execute("INSERT OR REPLACE INTO domains (domain, list_type) VALUES (?, ?)", (domain, list_type))
    conn.commit()
    conn.close()


def remove_domain(domain):
    conn = _conn()
    conn.execute("DELETE FROM domains WHERE domain = ?", (domain.strip().lower(),))
    conn.commit()
    conn.close()


# ---------- الكلمات الممنوعة ----------
def get_keywords():
    conn = _conn()
    rows = conn.execute("SELECT word FROM keywords ORDER BY word").fetchall()
    conn.close()
    return [r["word"] for r in rows]


def add_keyword(word):
    word = word.strip().lower()
    if not word:
        return
    conn = _conn()
    conn.execute("INSERT OR IGNORE INTO keywords (word) VALUES (?)", (word,))
    conn.commit()
    conn.close()


def remove_keyword(word):
    conn = _conn()
    conn.execute("DELETE FROM keywords WHERE word = ?", (word.strip().lower(),))
    conn.commit()
    conn.close()


# ---------- السجل ----------
def log_event(domain, action):
    conn = _conn()
    conn.execute("INSERT INTO visit_log (ts, domain, action) VALUES (?, ?, ?)",
                 (datetime.now().isoformat(timespec="seconds"), domain, action))
    conn.commit()
    conn.close()


def get_log(limit=200):
    conn = _conn()
    rows = conn.execute("SELECT ts, domain, action FROM visit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [(r["ts"], r["domain"], r["action"]) for r in rows]


def clear_log():
    conn = _conn()
    conn.execute("DELETE FROM visit_log")
    conn.commit()
    conn.close()
