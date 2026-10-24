"""
AntiPorn Guard — واجهة سطح المكتب (Tkinter).
تشغيل: python app.py
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import config
import database as db
import blocker
from monitor import MonitorService, _HAS_PIL


# ------------------------------------------------------------------
# شاشات الباسورد
# ------------------------------------------------------------------
def ask_set_password(root):
    """أول تشغيل: نحدد باسورد الوالدين."""
    while True:
        p1 = simpledialog.askstring("إنشاء كلمة مرور",
                                    "اختر كلمة مرور للحماية (للوالدين):",
                                    show="*", parent=root)
        if p1 is None:
            return False
        if len(p1) < 4:
            messagebox.showwarning("تنبيه", "كلمة المرور قصيرة جدًا (4 أحرف على الأقل).")
            continue
        p2 = simpledialog.askstring("تأكيد", "أعد كتابة كلمة المرور:", show="*", parent=root)
        if p1 != p2:
            messagebox.showwarning("تنبيه", "كلمتا المرور غير متطابقتين.")
            continue
        db.set_password(p1)
        return True


def ask_login(root):
    """طلب الباسورد للدخول على الإعدادات."""
    for _ in range(3):
        p = simpledialog.askstring("كلمة المرور", "ادخل كلمة المرور:", show="*", parent=root)
        if p is None:
            return False
        if db.check_password(p):
            return True
        messagebox.showerror("خطأ", "كلمة المرور غير صحيحة.")
    return False


# ------------------------------------------------------------------
# التطبيق الرئيسي
# ------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{config.APP_NAME} {config.APP_VERSION}")
        self.geometry("760x560")
        self.minsize(700, 520)

        self.monitor = MonitorService(on_time_violation=self._on_time_violation)
        self._time_warned = False

        self._build_ui()
        self._refresh_all()

        # نطبّق الحجب ونشغّل المراقبة عند البدء
        blocker.sync()
        self.monitor.start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- بناء الواجهة ----------
    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_status = ttk.Frame(nb)
        self.tab_lists = ttk.Frame(nb)
        self.tab_settings = ttk.Frame(nb)
        self.tab_log = ttk.Frame(nb)

        nb.add(self.tab_status, text="الحالة")
        nb.add(self.tab_lists, text="قوائم الحجب")
        nb.add(self.tab_settings, text="الإعدادات")
        nb.add(self.tab_log, text="السجل")

        self._build_status_tab()
        self._build_lists_tab()
        self._build_settings_tab()
        self._build_log_tab()

    # ---------- تبويب الحالة ----------
    def _build_status_tab(self):
        f = self.tab_status
        self.lbl_admin = ttk.Label(f, text="", font=("Segoe UI", 10))
        self.lbl_admin.pack(anchor="w", padx=12, pady=(14, 4))

        self.lbl_block = ttk.Label(f, text="", font=("Segoe UI", 12, "bold"))
        self.lbl_block.pack(anchor="w", padx=12, pady=4)

        self.btn_toggle = ttk.Button(f, text="تفعيل / إيقاف الحجب", command=self._toggle_block)
        self.btn_toggle.pack(anchor="w", padx=12, pady=10)

        info = ("البرنامج بيحجب المواقع عن طريق ملف hosts في النظام.\n"
                "لازم تشغّله بصلاحيات مدير (Run as administrator) عشان الحجب يشتغل.\n"
                "لتغيير الإعدادات أو إيقاف الحجب هيطلب منك كلمة المرور.")
        ttk.Label(f, text=info, justify="right", foreground="#555").pack(anchor="w", padx=12, pady=16)

    # ---------- تبويب القوائم ----------
    def _build_lists_tab(self):
        f = self.tab_lists
        container = ttk.Frame(f)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        # قائمة سوداء
        blk = ttk.LabelFrame(container, text="القائمة السوداء (محجوبة)")
        blk.pack(side="left", fill="both", expand=True, padx=4)
        self.lst_block = tk.Listbox(blk)
        self.lst_block.pack(fill="both", expand=True, padx=4, pady=4)
        row = ttk.Frame(blk); row.pack(fill="x", padx=4, pady=4)
        self.ent_block = ttk.Entry(row); self.ent_block.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="إضافة", command=self._add_block).pack(side="left", padx=2)
        ttk.Button(blk, text="حذف المحدد", command=self._del_block).pack(fill="x", padx=4, pady=(0, 4))

        # قائمة بيضاء
        alw = ttk.LabelFrame(container, text="القائمة البيضاء (مسموحة دائمًا)")
        alw.pack(side="left", fill="both", expand=True, padx=4)
        self.lst_allow = tk.Listbox(alw)
        self.lst_allow.pack(fill="both", expand=True, padx=4, pady=4)
        row2 = ttk.Frame(alw); row2.pack(fill="x", padx=4, pady=4)
        self.ent_allow = ttk.Entry(row2); self.ent_allow.pack(side="left", fill="x", expand=True)
        ttk.Button(row2, text="إضافة", command=self._add_allow).pack(side="left", padx=2)
        ttk.Button(alw, text="حذف المحدد", command=self._del_allow).pack(fill="x", padx=4, pady=(0, 4))

        # كلمات ممنوعة
        kw = ttk.LabelFrame(container, text="كلمات ممنوعة في الدومين")
        kw.pack(side="left", fill="both", expand=True, padx=4)
        self.lst_kw = tk.Listbox(kw)
        self.lst_kw.pack(fill="both", expand=True, padx=4, pady=4)
        row3 = ttk.Frame(kw); row3.pack(fill="x", padx=4, pady=4)
        self.ent_kw = ttk.Entry(row3); self.ent_kw.pack(side="left", fill="x", expand=True)
        ttk.Button(row3, text="إضافة", command=self._add_kw).pack(side="left", padx=2)
        ttk.Button(kw, text="حذف المحدد", command=self._del_kw).pack(fill="x", padx=4, pady=(0, 4))

    # ---------- تبويب الإعدادات ----------
    def _build_settings_tab(self):
        f = self.tab_settings
        pad = {"padx": 12, "pady": 6}

        self.var_block = tk.BooleanVar()
        ttk.Checkbutton(f, text="تفعيل حجب المواقع",
                        variable=self.var_block, command=self._save_settings).grid(row=0, column=0, sticky="w", **pad)

        self.var_kw = tk.BooleanVar()
        ttk.Checkbutton(f, text="تفعيل فلترة الكلمات الممنوعة",
                        variable=self.var_kw, command=self._save_settings).grid(row=1, column=0, sticky="w", **pad)

        # لقطات الشاشة
        self.var_shot = tk.BooleanVar()
        sc = ttk.Checkbutton(f, text="تفعيل لقطات الشاشة الدورية",
                             variable=self.var_shot, command=self._save_settings)
        sc.grid(row=2, column=0, sticky="w", **pad)
        if not _HAS_PIL:
            sc.state(["disabled"])
            ttk.Label(f, text="(محتاج تثبّت Pillow: pip install pillow)",
                      foreground="#a00").grid(row=2, column=1, sticky="w")

        ttk.Label(f, text="كل كم دقيقة (لقطة):").grid(row=3, column=0, sticky="w", **pad)
        self.ent_shot_int = ttk.Entry(f, width=8)
        self.ent_shot_int.grid(row=3, column=1, sticky="w")

        # حدود الوقت
        self.var_time = tk.BooleanVar()
        ttk.Checkbutton(f, text="تفعيل حدود وقت الاستخدام",
                        variable=self.var_time, command=self._save_settings).grid(row=4, column=0, sticky="w", **pad)

        ttk.Label(f, text="من (HH:MM):").grid(row=5, column=0, sticky="w", **pad)
        self.ent_start = ttk.Entry(f, width=8); self.ent_start.grid(row=5, column=1, sticky="w")
        ttk.Label(f, text="إلى (HH:MM):").grid(row=6, column=0, sticky="w", **pad)
        self.ent_end = ttk.Entry(f, width=8); self.ent_end.grid(row=6, column=1, sticky="w")

        ttk.Button(f, text="حفظ كل الإعدادات", command=self._save_settings_full).grid(row=7, column=0, sticky="w", **pad)
        ttk.Button(f, text="تغيير كلمة المرور", command=self._change_password).grid(row=7, column=1, sticky="w", **pad)

    # ---------- تبويب السجل ----------
    def _build_log_tab(self):
        f = self.tab_log
        cols = ("time", "domain", "action")
        self.tree = ttk.Treeview(f, columns=cols, show="headings")
        self.tree.heading("time", text="الوقت")
        self.tree.heading("domain", text="الدومين / الحدث")
        self.tree.heading("action", text="الإجراء")
        self.tree.column("time", width=160)
        self.tree.column("domain", width=320)
        self.tree.column("action", width=120)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        btns = ttk.Frame(f); btns.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(btns, text="تحديث", command=self._refresh_log).pack(side="left")
        ttk.Button(btns, text="مسح السجل", command=self._clear_log).pack(side="left", padx=6)

    # ---------- أفعال القوائم ----------
    def _add_block(self):
        db.add_domain(self.ent_block.get(), "block")
        self.ent_block.delete(0, "end")
        self._refresh_lists(); blocker.sync()

    def _del_block(self):
        for i in self.lst_block.curselection():
            db.remove_domain(self.lst_block.get(i))
        self._refresh_lists(); blocker.sync()

    def _add_allow(self):
        db.add_domain(self.ent_allow.get(), "allow")
        self.ent_allow.delete(0, "end")
        self._refresh_lists(); blocker.sync()

    def _del_allow(self):
        for i in self.lst_allow.curselection():
            db.remove_domain(self.lst_allow.get(i))
        self._refresh_lists(); blocker.sync()

    def _add_kw(self):
        db.add_keyword(self.ent_kw.get())
        self.ent_kw.delete(0, "end")
        self._refresh_lists()

    def _del_kw(self):
        for i in self.lst_kw.curselection():
            db.remove_keyword(self.lst_kw.get(i))
        self._refresh_lists()

    # ---------- حجب on/off ----------
    def _toggle_block(self):
        new_val = not db.get_bool("blocking_enabled")
        db.set_setting("blocking_enabled", "1" if new_val else "0")
        ok, msg = blocker.sync()
        if not ok:
            messagebox.showerror("تعذّر", msg)
        self.var_block.set(new_val)
        self._refresh_status()

    # ---------- الإعدادات ----------
    def _save_settings(self):
        db.set_setting("blocking_enabled", "1" if self.var_block.get() else "0")
        db.set_setting("keyword_filter_enabled", "1" if self.var_kw.get() else "0")
        db.set_setting("screenshot_enabled", "1" if self.var_shot.get() else "0")
        db.set_setting("time_limit_enabled", "1" if self.var_time.get() else "0")
        blocker.sync()
        self._refresh_status()

    def _save_settings_full(self):
        self._save_settings()
        interval = self.ent_shot_int.get().strip() or "15"
        db.set_setting("screenshot_interval_min", interval)
        db.set_setting("allowed_start", self.ent_start.get().strip() or "08:00")
        db.set_setting("allowed_end", self.ent_end.get().strip() or "22:00")
        messagebox.showinfo("تم", "تم حفظ الإعدادات.")

    def _change_password(self):
        if not ask_login(self):
            return
        ask_set_password(self)
        messagebox.showinfo("تم", "تم تغيير كلمة المرور.")

    def _on_time_violation(self):
        if not self._time_warned:
            self._time_warned = True
            try:
                self.after(0, lambda: messagebox.showwarning(
                    "خارج وقت الاستخدام المسموح",
                    "الوقت الحالي خارج ساعات الاستخدام المسموح بها."))
            except Exception:
                pass

    # ---------- تحديث ----------
    def _refresh_all(self):
        self._refresh_status()
        self._refresh_lists()
        self._refresh_settings_fields()
        self._refresh_log()

    def _refresh_status(self):
        admin = blocker.is_admin()
        self.lbl_admin.config(
            text=("✔ شغّال بصلاحيات مدير" if admin else "✖ مش شغّال كمدير — الحجب مش هيشتغل"),
            foreground=("#0a0" if admin else "#a00"))
        enabled = db.get_bool("blocking_enabled")
        self.lbl_block.config(text=("الحجب: مُفعّل" if enabled else "الحجب: متوقف"),
                              foreground=("#0a0" if enabled else "#a00"))

    def _refresh_lists(self):
        self.lst_block.delete(0, "end")
        for d in db.get_domains("block"):
            self.lst_block.insert("end", d)
        self.lst_allow.delete(0, "end")
        for d in db.get_domains("allow"):
            self.lst_allow.insert("end", d)
        self.lst_kw.delete(0, "end")
        for w in db.get_keywords():
            self.lst_kw.insert("end", w)

    def _refresh_settings_fields(self):
        self.var_block.set(db.get_bool("blocking_enabled"))
        self.var_kw.set(db.get_bool("keyword_filter_enabled"))
        self.var_shot.set(db.get_bool("screenshot_enabled"))
        self.var_time.set(db.get_bool("time_limit_enabled"))
        self.ent_shot_int.delete(0, "end"); self.ent_shot_int.insert(0, db.get_setting("screenshot_interval_min", "15"))
        self.ent_start.delete(0, "end"); self.ent_start.insert(0, db.get_setting("allowed_start", "08:00"))
        self.ent_end.delete(0, "end"); self.ent_end.insert(0, db.get_setting("allowed_end", "22:00"))

    def _refresh_log(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for ts, domain, action in db.get_log():
            self.tree.insert("", "end", values=(ts, domain, action))

    def _clear_log(self):
        if messagebox.askyesno("تأكيد", "مسح كل السجل؟"):
            db.clear_log(); self._refresh_log()

    def _on_close(self):
        # الخروج محمي بالباسورد عشان الطفل ما يقفلش البرنامج ببساطة
        if ask_login(self):
            self.monitor.stop()
            self.destroy()


def main():
    db.init_db()

    root = tk.Tk()
    root.withdraw()

    # أول تشغيل: لازم باسورد
    if not db.is_password_set():
        messagebox.showinfo(config.APP_NAME, "أول تشغيل: لازم تحدد كلمة مرور للحماية.")
        if not ask_set_password(root):
            root.destroy(); return
    else:
        if not ask_login(root):
            root.destroy(); return

    root.destroy()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
