# -*- coding: utf-8 -*-
"""پرونده ورزشکاران - مدیریت پرونده، ارزیابی و گزارش پیشرفت (فارسی / راست‌به‌چپ)"""
import sys, os, json, sqlite3, html, traceback
from datetime import datetime
from pathlib import Path
import jdatetime
from PySide6.QtCore import Qt, QTimer, Signal, QMarginsF, QUrl, QRectF, QPointF, QSizeF
from PySide6.QtGui import (QFont, QPainter, QPen, QColor, QImage, QTextDocument,
                           QPdfWriter, QPageSize, QPageLayout, QPalette)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPlainTextEdit, QComboBox, QPushButton, QListWidget,
    QListWidgetItem, QTabWidget, QScrollArea, QGroupBox, QSplitter, QTableWidget,
    QTableWidgetItem, QMessageBox, QFileDialog, QInputDialog, QMenu, QHeaderView)

# ───────────────────────── مسیرها ─────────────────────────
def data_dir():
    base = os.environ.get("APPDATA") or str(Path.home() / ".local" / "share")
    p = Path(base) / "AthleteFiles"
    p.mkdir(parents=True, exist_ok=True)
    return p

BACKUP_DIR = Path.home() / "Documents" / "AthleteBackups"

# ───────────────────────── تعریف فرم‌ها ─────────────────────────
YN = ["ندارد", "دارد"]
PERSONAL = [
    ("name", "نام و نام خانوادگی", "text"),
    ("birth", "تاریخ تولد (شمسی)", "date"),
    ("age", "سن", "auto"),
    ("gender", "جنسیت", "choice", ["مرد", "زن"]),
    ("phone", "شماره تماس", "text"),
    ("parent", "نام و شماره تماس والدین (زیر ۱۸ سال)", "text"),
    ("sport", "رشته ورزشی", "text"),
    ("level", "سطح ورزشی", "choice", ["مبتدی", "متوسط", "پیشرفته"]),
    ("history", "سابقه فعالیت ورزشی", "text"),
    ("per_week", "تعداد جلسات تمرین در هفته", "text"),
    ("duration", "مدت هر جلسه تمرین", "text"),
]
MEDICAL = [
    ("m_heart", "سابقه بیماری قلبی و عروقی", "combo", YN),
    ("m_resp", "سابقه بیماری تنفسی و آسم", "combo", YN),
    ("m_diab", "سابقه دیابت", "combo", YN),
    ("m_seiz", "سابقه تشنج", "combo", YN),
    ("m_bone", "سابقه بیماری‌های استخوانی و مفصلی", "combo", YN),
    ("m_neuro", "سابقه مشکلات عصبی", "combo", YN),
    ("m_surg", "سابقه جراحی", "combo", YN),
    ("m_hosp", "سابقه بستری در بیمارستان", "combo", YN),
    ("m_allergy", "حساسیت دارویی یا غذایی", "text"),
    ("m_meds", "داروهای مصرفی", "text"),
    ("m_supp", "مکمل‌های مصرفی", "text"),
    ("m_injury", "سابقه آسیب‌دیدگی ورزشی", "combo", YN),
    ("m_inj_place", "محل آسیب‌دیدگی", "text"),
    ("m_inj_time", "زمان وقوع آسیب", "text"),
    ("m_inj_now", "وضعیت فعلی آسیب", "text"),
    ("m_fracture", "سابقه شکستگی استخوان", "combo", YN),
    ("m_limit", "محدودیت پزشکی در فعالیت ورزشی", "text"),
    ("m_doctor", "تأییدیه پزشک برای فعالیت ورزشی", "text"),
]
HEALTH = [
    ("h_sleepq", "کیفیت خواب", "choice", ["خوب", "متوسط", "ضعیف"]),
    ("h_sleeph", "میانگین ساعات خواب", "text"),
    ("h_fatigue", "میزان خستگی روزانه", "choice", ["کم", "متوسط", "زیاد"]),
    ("h_appetite", "وضعیت اشتها", "choice", ["خوب", "متوسط", "کم", "زیاد"]),
    ("h_nutrition", "وضعیت تغذیه", "text"),
    ("h_water", "میزان مصرف آب", "text"),
    ("h_dizzy", "سابقه سرگیجه هنگام فعالیت", "combo", YN),
    ("h_chest", "سابقه درد قفسه سینه هنگام فعالیت", "combo", YN),
    ("h_breath", "سابقه تنگی نفس غیرمعمول", "combo", YN),
    ("h_faint", "سابقه غش یا نزدیک به غش", "combo", YN),
    ("h_mental", "سلامت روان و استرس (در صورت تمایل ورزشکار)", "text"),
]
GOALS = [
    ("goals", "اهداف تمرینی ورزشکار", "bigtext"),
    ("coach", "توضیحات کلی مربی", "bigtext"),
]
A_DATE = [("adate", "تاریخ ارزیابی", "date")]
ANTHRO = [
    ("height", "قد ایستاده (cm)", "num"), ("weight", "وزن بدن (kg)", "num"),
    ("bmi", "شاخص توده بدنی (خودکار)", "auto"), ("head", "دور سر (cm)", "num"),
    ("neck", "دور گردن", "num"), ("shoulder", "دور شانه", "num"),
    ("chest", "دور قفسه سینه", "num"), ("waist", "دور کمر", "num"),
    ("abdomen", "دور شکم", "num"), ("hip", "دور لگن", "num"),
    ("arm_r", "بازوی راست", "num"), ("arm_l", "بازوی چپ", "num"),
    ("fore_r", "ساعد راست", "num"), ("fore_l", "ساعد چپ", "num"),
    ("thigh_r", "ران راست", "num"), ("thigh_l", "ران چپ", "num"),
    ("calf_r", "ساق راست", "num"), ("calf_l", "ساق چپ", "num"),
]
COMP = [
    ("fat_pct", "درصد چربی بدن (%)", "num"), ("fat_mass", "توده چربی (خودکار، kg)", "auto"),
    ("lean_mass", "توده بدون چربی (خودکار، kg)", "auto"), ("muscle", "توده عضلانی تخمینی (kg)", "num"),
    ("bc_method", "روش اندازه‌گیری", "text"), ("bc_date", "تاریخ ارزیابی ترکیب بدن", "date"),
]
POSTURE = [
    ("p_head", "وضعیت سر و گردن", "combo", ["نرمال", "سر به جلو"]),
    ("p_shoulder", "وضعیت شانه‌ها", "combo", ["نرمال", "گرد", "نابرابر"]),
    ("p_spine", "وضعیت ستون فقرات", "combo", ["نرمال", "کایفوز", "لوردوز", "اسکولیوز"]),
    ("p_pelvis", "وضعیت لگن", "combo", ["نرمال", "کج‌شدگی قدامی", "کج‌شدگی خلفی"]),
    ("p_knee", "وضعیت زانوها", "combo", ["نرمال", "ضربدری", "پرانتزی", "هایپراکستنشن"]),
    ("p_ankle", "وضعیت مچ پا", "combo", ["نرمال", "پرونیشن", "سوپینیشن"]),
    ("p_arch", "بررسی قوس کف پا", "combo", ["نرمال", "صافی کف پا", "گودی زیاد"]),
    ("p_sym", "بررسی تقارن اندام‌ها", "combo", ["قرینه", "غیرقرینه"]),
    ("p_rom", "وجود محدودیت حرکت", "combo", YN),
]
A_NOTES = [("notes", "توضیحات این جلسه", "multiline")]
METRICS = [(f[0], f[1].replace(" (خودکار)", "").replace("خودکار، ", "")) for f in ANTHRO + COMP
           if f[2] in ("num", "auto")]

# ───────────────────────── ابزارهای کمکی ─────────────────────────
_TR = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٫،", "01234567890123456789.,")
def norm(s): return (s or "").translate(_TR).strip()
def num(s):
    try: return float(norm(str(s)).replace("/", ".").replace(",", "."))
    except ValueError: return None
def parse_date(s):
    parts = norm(s).replace("-", "/").split("/")
    if len(parts) != 3: return None
    try: return jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, TypeError): return None
def fmt_date(d): return f"{d.year:04d}/{d.month:02d}/{d.day:02d}"
def today_str(): return fmt_date(jdatetime.date.today())
def canon(s):
    d = parse_date(s)
    return fmt_date(d) if d else norm(s)
def calc_age(birth):
    b = parse_date(birth)
    if not b: return ""
    t = jdatetime.date.today()
    a = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
    return str(a) if a >= 0 else ""
def fmt(v):
    return "—" if v is None else f"{round(v, 2):g}"

def ask(parent, text):
    m = QMessageBox(parent); m.setWindowTitle("تأیید"); m.setText(text)
    m.setIcon(QMessageBox.Icon.Question)
    y = m.addButton("بله", QMessageBox.ButtonRole.YesRole)
    m.addButton("خیر", QMessageBox.ButtonRole.NoRole)
    m.exec()
    return m.clickedButton() is y

def info(parent, text, icon=QMessageBox.Icon.Information):
    m = QMessageBox(parent); m.setWindowTitle("پیام"); m.setText(text); m.setIcon(icon)
    m.addButton("باشه", QMessageBox.ButtonRole.AcceptRole); m.exec()

# ───────────────────────── پایگاه داده + پشتیبان ─────────────────────────
class DB:
    def __init__(self, path):
        self.c = sqlite3.connect(path)
        self.c.executescript("""
        CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY, name TEXT, data TEXT, created TEXT);
        CREATE TABLE IF NOT EXISTS assessments(id INTEGER PRIMARY KEY, student_id INTEGER, date TEXT, data TEXT);
        """)
        self.c.commit()
    def students(self):
        return self.c.execute("SELECT id,name FROM students ORDER BY name COLLATE NOCASE").fetchall()
    def get_student(self, sid):
        r = self.c.execute("SELECT name,data FROM students WHERE id=?", (sid,)).fetchone()
        return (r[0], json.loads(r[1] or "{}")) if r else ("", {})
    def add_student(self, name):
        cur = self.c.execute("INSERT INTO students(name,data,created) VALUES(?,?,?)",
                             (name, json.dumps({"name": name}, ensure_ascii=False), datetime.now().isoformat()))
        self.c.commit(); return cur.lastrowid
    def save_student(self, sid, name, data):
        self.c.execute("UPDATE students SET name=?,data=? WHERE id=?",
                       (name, json.dumps(data, ensure_ascii=False), sid)); self.c.commit()
    def delete_student(self, sid):
        self.c.execute("DELETE FROM assessments WHERE student_id=?", (sid,))
        self.c.execute("DELETE FROM students WHERE id=?", (sid,)); self.c.commit()
    def assessments(self, sid):
        rows = self.c.execute("SELECT id,date,data FROM assessments WHERE student_id=? ORDER BY date,id", (sid,)).fetchall()
        return [{"id": r[0], "date": r[1], "data": json.loads(r[2] or "{}")} for r in rows]
    def add_assessment(self, sid, date, data):
        cur = self.c.execute("INSERT INTO assessments(student_id,date,data) VALUES(?,?,?)",
                             (sid, date, json.dumps(data, ensure_ascii=False))); self.c.commit(); return cur.lastrowid
    def save_assessment(self, aid, date, data):
        self.c.execute("UPDATE assessments SET date=?,data=? WHERE id=?",
                       (date, json.dumps(data, ensure_ascii=False), aid)); self.c.commit()
    def delete_assessment(self, aid):
        self.c.execute("DELETE FROM assessments WHERE id=?", (aid,)); self.c.commit()

def auto_backup(conn, tag):
    """یک نسخه پشتیبان خودکار در Documents/AthleteBackups می‌سازد و فقط ۴۰ تای آخر را نگه می‌دارد."""
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        out = sqlite3.connect(BACKUP_DIR / f"backup_{datetime.now():%Y%m%d_%H%M%S}_{tag}.db")
        conn.backup(out); out.close()
        for f in sorted(BACKUP_DIR.glob("backup_*.db"))[:-40]: f.unlink()
    except Exception:
        pass

# ───────────────────────── ویجت‌های فرم ─────────────────────────
class DateEdit(QWidget):
    textChanged = Signal(str)
    def __init__(self):
        super().__init__()
        l = QHBoxLayout(self); l.setContentsMargins(0, 0, 0, 0)
        self.e = QLineEdit(); self.e.setPlaceholderText("مثلاً 1404/05/20")
        b = QPushButton("امروز"); b.setFixedWidth(60)
        b.clicked.connect(lambda: self.e.setText(today_str()))
        l.addWidget(self.e); l.addWidget(b)
        self.e.textChanged.connect(self._chg)
        self.e.editingFinished.connect(self._fix)
    def _chg(self, t):
        bad = bool(t.strip()) and parse_date(t) is None
        self.e.setStyleSheet("border:1px solid #d33;" if bad else "")
        self.textChanged.emit(t)
    def _fix(self):
        d = parse_date(self.e.text())
        if d and self.e.text() != fmt_date(d): self.e.setText(fmt_date(d))
    def text(self): return self.e.text()
    def setText(self, t): self.e.setText(t)

class FormPanel(QWidget):
    changed = Signal()
    def __init__(self, fields, cols=1):
        super().__init__()
        self.w = {}
        g = QGridLayout(self)
        for i, f in enumerate(fields):
            key, label, kind = f[:3]; opts = f[3] if len(f) > 3 else []
            if kind in ("multiline", "bigtext"):
                w = QPlainTextEdit(); w.setMinimumHeight(70 if kind == "multiline" else 200)
                w.textChanged.connect(self.changed)
            elif kind in ("choice", "combo"):
                w = QComboBox(); w.setEditable(kind == "combo"); w.addItems([""] + opts)
                w.currentTextChanged.connect(self.changed)
            elif kind == "date":
                w = DateEdit(); w.textChanged.connect(self.changed)
            elif kind == "auto":
                w = QLabel("—"); w.setStyleSheet("font-weight:bold;color:#1a5fb4;")
            else:
                w = QLineEdit(); w.textChanged.connect(self.changed)
            self.w[key] = (w, kind)
            r, c = divmod(i, cols)
            lab = QLabel(label + ":"); lab.setWordWrap(True)
            g.addWidget(lab, r, c * 2); g.addWidget(w, r, c * 2 + 1)
            g.setColumnStretch(c * 2 + 1, 1)
        g.setRowStretch(g.rowCount(), 1)
    def get(self):
        d = {}
        for k, (w, kind) in self.w.items():
            if kind in ("multiline", "bigtext"): v = w.toPlainText().strip()
            elif kind in ("choice", "combo"): v = w.currentText().strip()
            elif kind == "auto": v = "" if w.text() == "—" else w.text()
            elif kind == "date": v = canon(w.text())
            elif kind == "num": v = norm(w.text()).replace("/", ".").replace(",", ".")
            else: v = w.text().strip()
            d[k] = v
        return d
    def value(self, key): return self.get()[key]
    def set_auto(self, key, text): self.w[key][0].setText(text or "—")
    def set(self, d, prev=None):
        for k, (w, kind) in self.w.items():
            v = d.get(k, "") or ""
            if kind in ("multiline", "bigtext"): w.setPlainText(v)
            elif kind in ("choice", "combo"):
                i = w.findText(v)
                if i < 0 and v: w.addItem(v); i = w.findText(v)
                w.setCurrentIndex(max(i, 0))
            elif kind == "auto": w.setText(v or "—")
            else:
                w.setText(v)
                if kind == "num":
                    p = (prev or {}).get(k)
                    w.setPlaceholderText(f"قبلی: {p}" if p else "")

# ───────────────────────── نمودار ─────────────────────────
def draw_chart(p, W, H, title, labels, vals, s=1.0):
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.fillRect(QRectF(0, 0, W, H), QColor("white"))
    f = QFont("Tahoma"); f.setPixelSize(int(13 * s)); p.setFont(f)
    fb = QFont(f); fb.setBold(True); p.setFont(fb)
    p.setPen(QColor("#222"))
    p.drawText(QRectF(10 * s, 4 * s, W - 30 * s, 30 * s), int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), title)
    p.setFont(f)
    pts = [(i, v) for i, v in enumerate(vals) if v is not None]
    if not pts: return
    pl = QRectF(62 * s, 44 * s, W - 90 * s, H - 90 * s)
    lo, hi = min(v for _, v in pts), max(v for _, v in pts)
    if lo == hi: lo, hi = lo - 1, hi + 1
    pad = (hi - lo) * 0.2; lo -= pad; hi += pad
    n = len(vals)
    X = lambda i: pl.left() + pl.width() * (i + 0.5) / n
    Y = lambda v: pl.bottom() - (v - lo) / (hi - lo) * pl.height()
    for k in range(5):
        v = lo + (hi - lo) * k / 4; y = Y(v)
        p.setPen(QPen(QColor("#ddd"), 1)); p.drawLine(QPointF(pl.left(), y), QPointF(pl.right(), y))
        p.setPen(QColor("#666"))
        p.drawText(QRectF(0, y - 10 * s, pl.left() - 6 * s, 20 * s), int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), f"{v:.1f}")
    p.setPen(QPen(QColor("#1a5fb4"), 2.5 * s))
    for (i1, v1), (i2, v2) in zip(pts, pts[1:]):
        p.drawLine(QPointF(X(i1), Y(v1)), QPointF(X(i2), Y(v2)))
    step = max(1, n // 8)
    for i, v in pts:
        p.setBrush(QColor("#1a5fb4")); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(X(i), Y(v)), 4.5 * s, 4.5 * s)
        p.setPen(QColor("#111"))
        p.drawText(QRectF(X(i) - 40 * s, Y(v) - 26 * s, 80 * s, 20 * s), int(Qt.AlignmentFlag.AlignCenter), fmt(v))
    p.setPen(QColor("#444"))
    for i, t in enumerate(labels):
        if i % step == 0:
            p.drawText(QRectF(X(i) - 45 * s, pl.bottom() + 8 * s, 90 * s, 22 * s), int(Qt.AlignmentFlag.AlignCenter), t)

class ChartWidget(QWidget):
    def __init__(self):
        super().__init__(); self.setMinimumHeight(240); self.d = ("", [], [])
    def set_data(self, title, labels, vals): self.d = (title, labels, vals); self.update()
    def paintEvent(self, e):
        p = QPainter(self); draw_chart(p, self.width(), self.height(), *self.d); p.end()

# ───────────────────────── گزارش PDF ─────────────────────────
def metric_rows(ass):
    rows = []
    for key, label in METRICS:
        vals = [num(a["data"].get(key)) for a in ass]
        if any(v is not None for v in vals): rows.append((key, label, vals))
    return rows

def change(vals):
    v = [x for x in vals if x is not None]
    if len(v) < 2: return "—"
    return "\u200e" + f"{round(v[-1] - v[0], 2):+g}" + "\u200e"

def tr(cells): return "<tr>" + "".join(reversed(cells)) + "</tr>"   # Qt ستون‌ها را برای RTL برعکس نمی‌کند
def th(t): return f'<th bgcolor="#1a5fb4"><font color="white">{html.escape(t)}</font></th>'
TBL = '<table border="1" cellspacing="0" cellpadding="5" width="100%">'

def kv_table(title, fields, data):
    items = [(f[1], data.get(f[0], "")) for f in fields if data.get(f[0])]
    if not items: return ""
    h = f"<h3>{title}</h3>{TBL}"
    for i in range(0, len(items), 2):
        cells = []
        for lab, val in items[i:i + 2]:
            cells += [f'<td bgcolor="#eef3fb" width="22%"><b>{html.escape(lab)}</b></td>', f'<td width="28%">{html.escape(val)}</td>']
        if len(cells) == 2: cells.append('<td colspan="2"></td>')
        h += tr(cells)
    return h + "</table>"

def build_report(student, ass, full):
    sdata = student
    images = {}
    h = '<body dir="rtl" style="font-family:Tahoma; font-size:10pt;">'
    h += f'<h1 align="center"><font color="#1a5fb4">{"پرونده و گزارش پیشرفت ورزشکار" if full else "گزارش پیشرفت ورزشکار"}</font></h1>'
    h += f'<p align="center">نام: <b>{html.escape(sdata.get("name", ""))}</b> &nbsp;|&nbsp; رشته: {html.escape(sdata.get("sport", "") or "—")} &nbsp;|&nbsp; تاریخ گزارش: {today_str()}</p>'
    if full:
        h += kv_table("بخش اول: اطلاعات فردی", PERSONAL, sdata)
        h += kv_table("بخش دوم: سوابق پزشکی", MEDICAL, sdata)
        h += kv_table("بخش سوم: وضعیت سلامت عمومی", HEALTH, sdata)
    h += "<h3>مقایسه ارزیابی‌ها (پیکرسنجی و ترکیب بدن)</h3>"
    rows = metric_rows(ass)
    if not rows:
        h += "<p>هنوز ارزیابی‌ای ثبت نشده است.</p>"
    for s in range(0, len(ass), 6):
        if not rows: break
        part = ass[s:s + 6]
        h += TBL + tr([th("شاخص")] + [th(a["date"]) for a in part] + [th("تغییر کل")])
        for key, label, vals in rows:
            h += tr([f'<td bgcolor="#eef3fb"><b>{html.escape(label)}</b></td>']
                    + [f'<td align="center">{fmt(v)}</td>' for v in vals[s:s + 6]]
                    + [f'<td align="center" bgcolor="#fff7e0"><b>{change(vals)}</b></td>'])
        h += "</table><br>"
    charts = [("weight", "وزن (kg)"), ("bmi", "شاخص توده بدنی (BMI)"), ("fat_pct", "درصد چربی بدن"), ("waist", "دور کمر (cm)")]
    labels = [a["date"] for a in ass]
    for key, title in charts:
        vals = [num(a["data"].get(key)) for a in ass]
        if sum(v is not None for v in vals) >= 2:
            img = QImage(1000, 380, QImage.Format.Format_ARGB32); p = QPainter(img)
            draw_chart(p, 1000, 380, title, labels, vals, 1.5); p.end()
            images["chart_" + key] = img
            h += f'<p align="center"><img src="chart_{key}" width="620"></p>'
    if ass:
        if full:
            h += kv_table("وضعیت قامتی و اسکلتی (آخرین ارزیابی)", POSTURE, ass[-1]["data"])
        notes = [(a["date"], a["data"].get("notes", "")) for a in ass if a["data"].get("notes")]
        if notes:
            h += "<h3>توضیحات مربی در هر جلسه</h3>" + TBL
            for d, n in notes:
                h += tr([f'<td bgcolor="#eef3fb" width="15%"><b>{d}</b></td>', f'<td>{html.escape(n)}</td>'])
            h += "</table>"
    if full:
        for k, t in (("goals", "اهداف تمرینی ورزشکار"), ("coach", "توضیحات کلی مربی")):
            if sdata.get(k): h += f"<h3>{t}</h3><p>{html.escape(sdata[k]).replace(chr(10), '<br>')}</p>"
        h += "<br><br>" + TBL.replace('border="1"', 'border="0"') + \
             tr(['<td>امضای ورزشکار / والدین: ........................</td>', '<td>امضای مربی: ........................</td>']) + '</table>'
    return h + "</body>", images

def export_pdf(path, student, ass, full):
    html_text, images = build_report(student, ass, full)
    doc = QTextDocument(); doc.setDefaultFont(QFont("Tahoma", 10))
    o = doc.defaultTextOption(); o.setTextDirection(Qt.LayoutDirection.RightToLeft); doc.setDefaultTextOption(o)
    for name, img in images.items():
        doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(name), img)
    doc.setHtml(html_text)
    w = QPdfWriter(path)
    w.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    w.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Unit.Millimeter)
    w.setResolution(96)   # واحد سند = پیکسل 96dpi؛ خروجی PDF برداری است و کیفیتش پایین نمی‌آید
    doc.setPageSize(QSizeF(w.width(), w.height()))   # بدون این، جدول‌ها فقط ~۷۸٪ عرض صفحه را پر می‌کنند
    doc.print_(w)

# ───────────────────────── پنجره اصلی ─────────────────────────
def scroll(w):
    s = QScrollArea(); s.setWidgetResizable(True); s.setWidget(w); return s

class Main(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db; self.sid = None; self.aid = None; self.loading = False; self.dirty = False
        self.setWindowTitle("پرونده ورزشکاران"); self.resize(1250, 800)

        # لیست ورزشکاران
        side = QWidget(); sl = QVBoxLayout(side)
        self.search = QLineEdit(); self.search.setPlaceholderText("🔍 جستجوی نام...")
        self.search.textChanged.connect(lambda: self.refresh_students(self.sid))
        self.lst = QListWidget(); self.lst.currentItemChanged.connect(self.on_student)
        b_new = QPushButton("➕ ورزشکار جدید"); b_new.clicked.connect(self.new_student)
        b_del = QPushButton("🗑 حذف ورزشکار"); b_del.clicked.connect(self.del_student)
        for x in (self.search, self.lst, b_new, b_del): sl.addWidget(x)

        # تب‌ها
        self.p_personal = FormPanel(PERSONAL, 2); self.p_med = FormPanel(MEDICAL, 2)
        self.p_health = FormPanel(HEALTH, 2); self.p_goals = FormPanel(GOALS, 1)
        self.tabs = QTabWidget()
        self.tabs.addTab(scroll(self.p_personal), "۱. اطلاعات فردی")
        self.tabs.addTab(scroll(self.p_med), "۲. سوابق پزشکی")
        self.tabs.addTab(scroll(self.p_health), "۳. سلامت عمومی")
        self.tabs.addTab(self.build_assess_tab(), "۴. ارزیابی‌ها (هر جلسه)")
        self.tabs.addTab(self.build_progress_tab(), "۵. مقایسه و پیشرفت")
        self.tabs.addTab(scroll(self.p_goals), "۶. اهداف و توضیحات")
        self.tabs.currentChanged.connect(self.on_tab)

        # نوار دکمه‌ها
        bar = QHBoxLayout()
        b_save = QPushButton("💾 ذخیره"); b_save.clicked.connect(lambda: self.save_all(True))
        b_pdf = QPushButton("📄 خروجی PDF ▾"); m = QMenu(b_pdf)
        m.addAction("گزارش کامل (پرونده + پیشرفت)", lambda: self.pdf(True))
        m.addAction("فقط مقایسه پیشرفت", lambda: self.pdf(False)); b_pdf.setMenu(m)
        b_bak = QPushButton("📦 پشتیبان‌گیری"); b_bak.clicked.connect(self.backup)
        b_res = QPushButton("♻️ بازیابی"); b_res.clicked.connect(self.restore)
        for b in (b_save, b_pdf, b_bak, b_res): bar.addWidget(b)
        bar.addStretch()
        right = QWidget(); rl = QVBoxLayout(right); rl.addLayout(bar); rl.addWidget(self.tabs)
        sp = QSplitter(); sp.addWidget(side); sp.addWidget(right); sp.setStretchFactor(1, 1)
        sp.setSizes([260, 950]); self.setCentralWidget(sp)
        self.statusBar().showMessage(f"محل ذخیره اطلاعات: {data_dir()} | نسخه‌های خودکار: {BACKUP_DIR}")

        for p in (self.p_personal, self.p_med, self.p_health, self.p_goals,
                  self.f_date, self.f_anth, self.f_comp, self.f_post, self.f_notes):
            p.changed.connect(self.mark)
        self.p_personal.changed.connect(lambda: self.p_personal.set_auto("age", calc_age(self.p_personal.value("birth"))))
        self.f_anth.changed.connect(self.calc_assess); self.f_comp.changed.connect(self.calc_assess)
        self.timer = QTimer(self); self.timer.timeout.connect(lambda: self.save_all()); self.timer.start(15000)
        self.refresh_students(None)
        if self.lst.count(): self.lst.setCurrentRow(0)
        else: self.set_enabled(False)

    # ---- ساخت تب‌ها ----
    def build_assess_tab(self):
        w = QWidget(); l = QHBoxLayout(w)
        left = QWidget(); ll = QVBoxLayout(left); left.setFixedWidth(210)
        ll.addWidget(QLabel("جلسه‌های ارزیابی:"))
        self.alist = QListWidget(); self.alist.currentItemChanged.connect(self.on_assess); ll.addWidget(self.alist)
        b1 = QPushButton("➕ ارزیابی جدید"); b1.clicked.connect(self.new_assess)
        b2 = QPushButton("🗑 حذف این ارزیابی"); b2.clicked.connect(self.del_assess)
        ll.addWidget(b1); ll.addWidget(b2)
        self.f_date = FormPanel(A_DATE); self.f_anth = FormPanel(ANTHRO, 2)
        self.f_comp = FormPanel(COMP, 2); self.f_post = FormPanel(POSTURE, 2); self.f_notes = FormPanel(A_NOTES)
        body = QWidget(); bl = QVBoxLayout(body); bl.addWidget(self.f_date)
        for t, f in (("بخش ۴: پیکرسنجی (سانتی‌متر / کیلوگرم)", self.f_anth), ("بخش ۵: ترکیب بدن", self.f_comp),
                     ("بخش ۶: وضعیت قامتی و اسکلتی", self.f_post)):
            g = QGroupBox(t); QVBoxLayout(g).addWidget(f); bl.addWidget(g)
        bl.addWidget(self.f_notes)
        self.assess_scroll = scroll(body)
        l.addWidget(left); l.addWidget(self.assess_scroll, 1)
        return w

    def build_progress_tab(self):
        w = QWidget(); l = QVBoxLayout(w)
        l.addWidget(QLabel("روی هر ردیف کلیک کنید تا نمودارش پایین نمایش داده شود."))
        self.table = QTableWidget(); self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.currentCellChanged.connect(lambda r, *_: self.show_chart(r))
        self.chart = ChartWidget()
        sp = QSplitter(Qt.Orientation.Vertical); sp.addWidget(self.table); sp.addWidget(self.chart); sp.setSizes([300, 360]); l.addWidget(sp)
        return w

    # ---- وضعیت ----
    def mark(self):
        if not self.loading: self.dirty = True

    def set_enabled(self, on):
        for p in (self.p_personal, self.p_med, self.p_health, self.p_goals): p.setEnabled(on)
        self.assess_scroll.setEnabled(on and self.aid is not None)

    def calc_assess(self):
        h, w = num(self.f_anth.value("height")), num(self.f_anth.value("weight"))
        self.f_anth.set_auto("bmi", f"{w / (h / 100) ** 2:.1f}" if h and w and h > 0 else "")
        fp = num(self.f_comp.value("fat_pct"))
        if w and fp is not None:
            self.f_comp.set_auto("fat_mass", f"{w * fp / 100:.1f}"); self.f_comp.set_auto("lean_mass", f"{w - w * fp / 100:.1f}")
        else:
            self.f_comp.set_auto("fat_mass", ""); self.f_comp.set_auto("lean_mass", "")

    def assess_get(self):
        d = {}
        for p in (self.f_date, self.f_anth, self.f_comp, self.f_post, self.f_notes): d.update(p.get())
        return d

    # ---- ذخیره ----
    def save_all(self, manual=False):
        if self.sid is not None and self.dirty:
            data = {}
            for p in (self.p_personal, self.p_med, self.p_health, self.p_goals): data.update(p.get())
            self.db.save_student(self.sid, data.get("name") or "بدون نام", data)
            if self.aid is not None:
                self.calc_assess(); a = self.assess_get(); self.db.save_assessment(self.aid, a.get("adate") or today_str(), a)
            self.dirty = False
            self.refresh_students(self.sid); self.refresh_assess(self.aid)
            self.statusBar().showMessage(f"✓ ذخیره شد ({datetime.now():%H:%M:%S})", 4000)
        elif manual:
            self.statusBar().showMessage("همه‌چیز از قبل ذخیره است ✓", 3000)

    # ---- ورزشکاران ----
    def refresh_students(self, select):
        q = self.search.text().strip()
        self.lst.blockSignals(True); self.lst.clear(); row = -1
        for sid, name in self.db.students():
            if q and q not in (name or ""): continue
            it = QListWidgetItem(name or "بدون نام"); it.setData(Qt.ItemDataRole.UserRole, sid); self.lst.addItem(it)
            if sid == select: row = self.lst.count() - 1
        if row >= 0: self.lst.setCurrentRow(row)
        self.lst.blockSignals(False)

    def new_student(self):
        self.save_all()
        d = QInputDialog(self); d.setWindowTitle("ورزشکار جدید"); d.setLabelText("نام و نام خانوادگی:")
        d.setOkButtonText("ایجاد"); d.setCancelButtonText("انصراف")
        if d.exec() and d.textValue().strip():
            sid = self.db.add_student(d.textValue().strip())
            self.search.clear(); self.refresh_students(sid); self.load_student(sid)

    def del_student(self):
        if self.sid is None: return
        name = self.db.get_student(self.sid)[0]
        if ask(self, f"پرونده «{name}» و همه ارزیابی‌هایش حذف شود؟\n(قبل از حذف یک نسخه پشتیبان ساخته می‌شود)"):
            self.save_all(); auto_backup(self.db.c, "before_delete")
            self.db.delete_student(self.sid); self.sid = None; self.aid = None
            self.refresh_students(None)
            if self.lst.count(): self.lst.setCurrentRow(0)
            else: self.clear_forms(); self.set_enabled(False)

    def on_student(self, cur, prev):
        self.save_all()
        if cur: self.load_student(cur.data(Qt.ItemDataRole.UserRole))

    def clear_forms(self):
        self.loading = True
        for p in (self.p_personal, self.p_med, self.p_health, self.p_goals, self.f_date, self.f_anth,
                  self.f_comp, self.f_post, self.f_notes): p.set({})
        self.alist.clear(); self.table.clear(); self.table.setRowCount(0); self.table.setColumnCount(0)
        self.loading = False; self.dirty = False

    def load_student(self, sid):
        self.loading = True; self.sid = sid
        _, data = self.db.get_student(sid)
        for p in (self.p_personal, self.p_med, self.p_health, self.p_goals): p.set(data)
        self.p_personal.set_auto("age", calc_age(data.get("birth", "")))
        self.loading = False; self.dirty = False
        ass = self.db.assessments(sid); self.aid = ass[-1]["id"] if ass else None
        self.refresh_assess(self.aid, load=True); self.set_enabled(True)
        if self.tabs.currentIndex() == 4: self.refresh_progress()

    # ---- ارزیابی‌ها ----
    def refresh_assess(self, select, load=False):
        self.alist.blockSignals(True); self.alist.clear(); row = -1
        for a in self.db.assessments(self.sid):
            w = a["data"].get("weight"); it = QListWidgetItem(a["date"] + (f" — {w} کیلو" if w else ""))
            it.setData(Qt.ItemDataRole.UserRole, a["id"]); self.alist.addItem(it)
            if a["id"] == select: row = self.alist.count() - 1
        if row >= 0: self.alist.setCurrentRow(row)
        self.alist.blockSignals(False)
        if load: self.load_assess(select)

    def load_assess(self, aid):
        self.aid = aid; self.loading = True
        ass = self.db.assessments(self.sid); cur = next((a for a in ass if a["id"] == aid), None)
        prev = None
        if cur:
            i = ass.index(cur); prev = ass[i - 1]["data"] if i > 0 else None
        d = cur["data"] if cur else {}
        for p in (self.f_date, self.f_anth, self.f_comp, self.f_post, self.f_notes): p.set(d, prev)
        self.calc_assess(); self.loading = False; self.dirty = False
        self.assess_scroll.setEnabled(cur is not None)

    def on_assess(self, cur, prev):
        self.save_all()
        if cur: self.load_assess(cur.data(Qt.ItemDataRole.UserRole))

    def new_assess(self):
        if self.sid is None: return
        self.save_all()
        aid = self.db.add_assessment(self.sid, today_str(), {"adate": today_str()})
        self.refresh_assess(aid, load=True)

    def del_assess(self):
        if self.aid is None: return
        if ask(self, "این ارزیابی حذف شود؟"):
            auto_backup(self.db.c, "before_delete"); self.db.delete_assessment(self.aid)
            ass = self.db.assessments(self.sid); self.aid = ass[-1]["id"] if ass else None
            self.refresh_assess(self.aid, load=True)

    # ---- پیشرفت ----
    def on_tab(self, i):
        if i == 4: self.save_all(); self.refresh_progress()

    def refresh_progress(self):
        ass = self.db.assessments(self.sid) if self.sid else []
        self.rows = metric_rows(ass); self.labels = [a["date"] for a in ass]
        t = self.table; t.clear(); t.setRowCount(len(self.rows)); t.setColumnCount(len(ass) + 1)
        t.setHorizontalHeaderLabels(self.labels + ["تغییر کل"]); t.setVerticalHeaderLabels([r[1] for r in self.rows])
        for r, (_, _, vals) in enumerate(self.rows):
            for c, v in enumerate(vals):
                it = QTableWidgetItem(fmt(v)); it.setTextAlignment(Qt.AlignmentFlag.AlignCenter); t.setItem(r, c, it)
            it = QTableWidgetItem(change(vals)); it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it.setBackground(QColor("#fff3cd")); t.setItem(r, len(ass), it)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        if self.rows: t.setCurrentCell(0, 0)
        else: self.chart.set_data("", [], [])

    def show_chart(self, r):
        if 0 <= r < len(self.rows): self.chart.set_data(self.rows[r][1], self.labels, self.rows[r][2])

    # ---- PDF و پشتیبان ----
    def pdf(self, full):
        if self.sid is None: return info(self, "اول یک ورزشکار انتخاب کنید.")
        self.save_all(); name, data = self.db.get_student(self.sid)
        path, _ = QFileDialog.getSaveFileName(self, "ذخیره PDF", f"{name}_{today_str().replace('/', '-')}.pdf", "PDF (*.pdf)")
        if not path: return
        try:
            export_pdf(path, data, self.db.assessments(self.sid), full)
            info(self, "فایل PDF ساخته شد ✓")
            if sys.platform == "win32": os.startfile(path)
        except Exception as e:
            info(self, f"ساخت PDF ناموفق بود:\n{e}", QMessageBox.Icon.Warning)

    def backup(self):
        self.save_all()
        path, _ = QFileDialog.getSaveFileName(self, "ذخیره نسخه پشتیبان", f"backup_{datetime.now():%Y-%m-%d}.db", "Backup (*.db)")
        if not path: return
        out = sqlite3.connect(path); self.db.c.backup(out); out.close()
        info(self, "نسخه پشتیبان ذخیره شد ✓\nاین فایل را روی فلش یا فضای ابری نگه دارید.")

    def restore(self):
        path, _ = QFileDialog.getOpenFileName(self, "انتخاب فایل پشتیبان", "", "Backup (*.db)")
        if not path: return
        try:
            src = sqlite3.connect(path)
            tabs = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {"students", "assessments"} <= tabs: raise ValueError("این فایل پشتیبان این برنامه نیست.")
        except Exception as e:
            return info(self, f"فایل نامعتبر است:\n{e}", QMessageBox.Icon.Warning)
        if not ask(self, "همه اطلاعات فعلی با این پشتیبان جایگزین می‌شود.\n(از اطلاعات فعلی هم یک نسخه امن ساخته می‌شود.) ادامه؟"):
            return
        self.save_all(); auto_backup(self.db.c, "before_restore")
        src.backup(self.db.c); src.close()
        self.sid = None; self.aid = None; self.refresh_students(None)
        if self.lst.count(): self.lst.setCurrentRow(0)
        else: self.clear_forms(); self.set_enabled(False)
        info(self, "اطلاعات با موفقیت بازیابی شد ✓")

    def closeEvent(self, e):
        self.save_all(); auto_backup(self.db.c, "exit"); e.accept()

STYLE = """
* { font-family: Tahoma, 'Segoe UI'; font-size: 10pt; }
QPushButton { background:#1a5fb4; color:white; border:none; padding:8px 14px; border-radius:6px; }
QPushButton:hover { background:#2a73d0; }
QLineEdit, QComboBox, QPlainTextEdit { padding:5px; border:1px solid #bbb; border-radius:4px; background:white; color:#222; }
QComboBox QAbstractItemView { background:white; color:#222; selection-background-color:#1a5fb4; selection-color:white; }
QListWidget, QTableWidget { background:white; color:#222; }
QGroupBox { font-weight:bold; border:1px solid #ccc; border-radius:6px; margin-top:10px; padding-top:10px; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top right; padding: 0 10px; }
QListWidget::item { padding:7px; } QListWidget::item:selected { background:#1a5fb4; color:white; }
QTabBar::tab { padding:9px 14px; }
"""

def light_palette():
    """پالت روشن ثابت؛ مستقل از حالت تیره ویندوز، تا متن و کادرها همیشه خوانا باشند."""
    pal = QPalette()
    for role, col in [
        (QPalette.ColorRole.Window, "#f3f3f3"), (QPalette.ColorRole.WindowText, "#222222"),
        (QPalette.ColorRole.Base, "#ffffff"), (QPalette.ColorRole.AlternateBase, "#f0f0f0"),
        (QPalette.ColorRole.Text, "#222222"), (QPalette.ColorRole.Button, "#e8e8e8"),
        (QPalette.ColorRole.ButtonText, "#222222"), (QPalette.ColorRole.Highlight, "#1a5fb4"),
        (QPalette.ColorRole.HighlightedText, "#ffffff"), (QPalette.ColorRole.PlaceholderText, "#888888"),
        (QPalette.ColorRole.ToolTipBase, "#ffffff"), (QPalette.ColorRole.ToolTipText, "#222222"),
    ]:
        pal.setColor(role, QColor(col))
    return pal

def main():
    def hook(t, v, tb):
        try:
            with (data_dir() / "error.log").open("a", encoding="utf-8") as f:
                f.write(datetime.now().isoformat() + "\n" + "".join(traceback.format_exception(t, v, tb)) + "\n")
        except Exception: pass
        info(None, "یک خطای غیرمنتظره رخ داد. اطلاعات ذخیره‌شده سالم است.\n\n" + str(v), QMessageBox.Icon.Critical)
    sys.excepthook = hook
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(light_palette())
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setStyleSheet(STYLE)
    db = DB(data_dir() / "athletes.db")
    auto_backup(db.c, "start")
    w = Main(db); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
