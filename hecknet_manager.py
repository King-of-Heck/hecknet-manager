"""
Process manager for the printer scripts.

A small Tkinter panel that launches each script as a subprocess, streams its
output into a log pane, and shows status:

    green    running, no errors recently
    yellow   running, but errors seen in the last window
    red      not running

Each configured folder is scanned at startup and the highest-numbered script
in it is the one launched, so dropping in a newer file is enough to switch to
it. Set HECKNET_ROOT to point at the folder holding the script directories.

    python hecknet_manager.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, font as tkfont
import subprocess
import threading
import time
import os
import sys
import queue
import re
from datetime import datetime, timedelta

# DPI AWARENESS — must be called before any tkinter window is created
# Without this, Windows scales the window up on high-DPI screens and the

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


PY314 = r"C:\path\to\python.exe"
PY312 = "py"   # py -3.12 launcher

# Version auto-discovery
# Each script entry supplies a folder and a base stem (filename without the

def _parse_version(filename: str, stem: str) -> tuple:
    """
    Given a filename like 'Morning_Report_1.9.py' and stem 'Morning_Report_',
    return the version as a tuple of ints for sorting, e.g. (1, 9).
    Returns () if no version can be parsed.
    """
    name = os.path.splitext(filename)[0]   # strip .py
    suffix = name[len(stem):]              # e.g. "1.9" or "1.13.1"
    if not suffix:
        return ()
    try:
        return tuple(int(x) for x in suffix.split("."))
    except ValueError:
        return ()

def resolve_script(folder: str, stem: str) -> tuple:
    """
    Scan *folder* for .py files matching <stem><version>.py and return
    (resolved_path, status_message).
    stem should end with '_', e.g. 'Morning_Report_'.
    Case-insensitive match so Windows filename casing doesn't matter.
    Falls back to stem-minus-trailing-underscore + '.py' if nothing found.
    """
    fallback_name = stem.rstrip("_") + ".py"
    fallback = os.path.join(folder, fallback_name)

    if not os.path.isdir(folder):
        return fallback, f"WARNING: Folder not found: {folder}"

    candidates = []
    for fname in os.listdir(folder):
        if not fname.endswith(".py"):
            continue
        if not fname.lower().startswith(stem.lower()):
            continue
        ver = _parse_version(fname, stem)
        if ver:
            candidates.append((ver, os.path.join(folder, fname)))

    if not candidates:
        return fallback, f"WARNING: No versioned file found in {folder} matching {stem}*.py"

    candidates.sort(key=lambda x: x[0], reverse=True)
    chosen = candidates[0][1]
    return chosen, f"OK: {os.path.basename(chosen)}"


# Script definitions
# folder : directory that holds the script(s)

_BASE = os.environ.get(
    "HECKNET_ROOT",
    os.path.dirname(os.path.abspath(__file__)),
)

_SCRIPT_DEFS = [
    {
        "id":     "morning",
        "label":  "Morning Report",
        "desc":   "8 AM daily weather report + r/aww + news",
        "folder": os.path.join(_BASE, "Morning Report"),
        "stem":   "Morning_Report_",
        "py":     "3.14",
        "exe":    PY314,
        "extra":  [],
    },
    {
        "id":     "evening",
        "label":  "Evening Report",
        "desc":   "22:30 next-day forecast slots",
        "folder": os.path.join(_BASE, "Evening Report"),
        "stem":   "Evening_Report_",
        "py":     "3.14",
        "exe":    PY314,
        "extra":  [],
    },
    {
        "id":     "nuclear",
        "label":  "Nuclear News Dispatch",
        "desc":   "53-feed nuclear news monitor (10 min poll)",
        "folder": os.path.join(_BASE, "Nuclear News"),
        "stem":   "Nuclear_News_",
        "py":     "3.14",
        "exe":    PY314,
        "extra":  [],
    },
    {
        "id":     "flora",
        "label":  "Flora Discord Printer",
        "desc":   "Discord → thermal printer (Flora channels)",
        "folder": os.path.join(_BASE, "Discord Printer"),
        "stem":   "Discord_Printer_",
        "py":     "3.14",
        "exe":    PY314,
        "extra":  [],
    },
    {
        "id":     "hecknet_printer",
        "label":  "HeckNet Printer",
        "desc":   "Discord → thermal printer (HeckNet channels)",
        "folder": os.path.join(_BASE, "HeckNet Discord Printer"),
        "stem":   "HeckNet_Printer_",
        "py":     "3.14",
        "exe":    PY314,
        "extra":  [],
    },
    {
        "id":     "homedepot",
        "label":  "HeckNet Home Depot List-o-Matic",
        "desc":   "Discord homedepot.ca product scanner",
        "folder": os.path.join(_BASE, "Home Depot List"),
        "stem":   "HeckNet_HomeDepot_",
        "py":     "3.12",
        "exe":    PY312,
        "extra":  ["-3.12"],
    },
    {
        "id":     "jays",
        "label":  "Blue Jays Tracker",
        "desc":   "Live MLB game monitor + HR receipts",
        "folder": os.path.join(_BASE, "Jays Tracker"),
        "stem":   "BlueJays_GameDay_",
        "py":     "3.14",
        "exe":    PY314,
        "extra":  [],
    },
]

def _build_scripts() -> list:
    """Resolve versioned paths and build the final SCRIPTS list."""
    scripts = []
    print("HeckNet Manager — resolving script paths:")
    for d in _SCRIPT_DEFS:
        path, status = resolve_script(d["folder"], d["stem"])
        print(f"  {d['label']:35s} {status}")
        # Pull version string out of the resolved filename, e.g.
        # "Morning_Report_1.10.py""v1.10"
        fname_no_ext = os.path.splitext(os.path.basename(path))[0]
        ver_tuple    = _parse_version(os.path.basename(path), d["stem"])
        ver_str      = "v" + ".".join(str(x) for x in ver_tuple) if ver_tuple else "?"
        scripts.append({
            "id":       d["id"],
            "label":    d["label"],
            "desc":     d["desc"],
            "cmd":      [d["exe"]] + d["extra"] + [path],
            "py":       d["py"],
            "path":     path,
            "resolved": status,
            "version":  ver_str,
        })
    print()
    return scripts

SCRIPTS = _build_scripts()

ERROR_PATTERNS = [
    re.compile(r"\b(error|exception|traceback|failed|failure|timeout|refused)\b", re.I),
    re.compile(r"❌"),
    re.compile(r"^\s*File \".*\", line \d+", re.M),
]

ERROR_COOLDOWN = 120


BG          = "#0d0d0d"
BG_PANEL    = "#141414"
BG_CARD     = "#1a1a1a"
BG_LOG      = "#0a0a0a"
ACCENT      = "#00ff99"        # phosphor green
ACCENT_DIM  = "#006633"
FG          = "#cccccc"
FG_DIM      = "#555555"
FG_LABEL    = "#ffffff"
BORDER      = "#2a2a2a"
RED         = "#ff3333"
YELLOW      = "#ffcc00"
GREEN       = "#00ff66"
FONT_MONO   = ("Courier New", 9)
FONT_LABEL  = ("Courier New", 11, "bold")
FONT_TITLE  = ("Courier New", 14, "bold")
FONT_SMALL  = ("Courier New", 8)


class ProcessMonitor:
    def __init__(self, cfg: dict):
        self.cfg         = cfg
        self.proc        = None
        self.start_time  = None
        self.last_error  = None          # datetime of most recent error line
        self.log_queue   = queue.Queue() # (line_text, is_error)
        self._reader_t   = None
        self._lock       = threading.Lock()


    @property
    def running(self) -> bool:
        with self._lock:
            return self.proc is not None and self.proc.poll() is None

    @property
    def status(self) -> str:   # "stopped" | "error" | "ok"
        if not self.running:
            return "stopped"
        if (self.last_error is not None and
                (datetime.now() - self.last_error).total_seconds() < ERROR_COOLDOWN):
            return "error"
        return "ok"

    @property
    def uptime_str(self) -> str:
        if not self.running or self.start_time is None:
            return "—"
        delta = datetime.now() - self.start_time
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s   = divmod(rem, 60)
        if h:
            return f"{h}h {m:02d}m"
        return f"{m}m {s:02d}s"


    def start(self):
        if self.running:
            return
        # Insert -u (unbuffered) immediately before the script path so output
        # streams in real time. Placing it last-before-script works for both:
        raw_cmd     = self.cfg["cmd"]
        script_path = raw_cmd[-1]
        exe_and_flags = raw_cmd[:-1]
        if "-u" not in exe_and_flags:
            exe_and_flags = exe_and_flags + ["-u"]
        cmd = exe_and_flags + [script_path]
        if not os.path.exists(script_path):
            self.log_queue.put((
                f"[MANAGER] ❌  Script not found:\n"
                f"[MANAGER]    {script_path}\n"
                f"[MANAGER]    Check folder path and stem in _SCRIPT_DEFS at the top of this file.\n"
                f"[MANAGER]    Resolution status: {self.cfg.get('resolved', 'unknown')}\n",
                True
            ))
            return
        try:
            with self._lock:
                self.proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            self.start_time = datetime.now()
            self.last_error = None
            self._reader_t  = threading.Thread(
                target=self._read_output, daemon=True
            )
            self._reader_t.start()
            resolved = os.path.basename(script_path)
            self.log_queue.put((
                f"[MANAGER] ▶  Started at {self.start_time.strftime('%H:%M:%S')} "
                f"→ {resolved}\n",
                False
            ))
        except Exception as e:
            self.log_queue.put((f"[MANAGER] ❌  Failed to start: {e}\n", True))

    def stop(self):
        with self._lock:
            proc = self.proc
        if proc is None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        except Exception:
            pass
        with self._lock:
            self.proc = None
        self.log_queue.put(("[MANAGER] ■  Stopped.\n", False))

    def restart(self):
        self.stop()
        time.sleep(0.5)
        self.start()


    def _read_output(self):
        proc = self.proc
        if proc is None or proc.stdout is None:
            return
        try:
            for line in proc.stdout:
                is_err = any(p.search(line) for p in ERROR_PATTERNS)
                if is_err:
                    self.last_error = datetime.now()
                self.log_queue.put((line, is_err))
        except Exception:
            pass
        self.log_queue.put(("[MANAGER] ◼  Process ended.\n", False))
        with self._lock:
            self.proc = None


class ScriptCard(tk.Frame):
    LOG_MAX_LINES = 500

    def __init__(self, parent, monitor: ProcessMonitor, **kwargs):
        super().__init__(parent, bg=BG_CARD, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER,
                         **kwargs)
        self.monitor   = monitor
        self.log_open  = False
        self._log_lines = 0
        self._build()

    def _build(self):
        cfg = self.monitor.cfg

        top = tk.Frame(self, bg=BG_CARD, padx=10, pady=8)
        top.pack(fill="x")

        self.light = tk.Label(top, text="●", font=("Courier New", 18),
                              bg=BG_CARD, fg=RED, width=2)
        self.light.pack(side="left")

        info = tk.Frame(top, bg=BG_CARD)
        info.pack(side="left", padx=(6, 0), fill="x", expand=True)

        title_row = tk.Frame(info, bg=BG_CARD)
        title_row.pack(anchor="w", fill="x")
        tk.Label(title_row, text=cfg["label"], font=FONT_LABEL,
                 bg=BG_CARD, fg=FG_LABEL, anchor="w").pack(side="left")
        tk.Label(title_row, text=f"  {cfg.get('version', '?')}",
                 font=FONT_SMALL, bg=BG_CARD, fg=ACCENT_DIM, anchor="w").pack(side="left", pady=(2,0))

        self.desc_label = tk.Label(info, text=cfg["desc"], font=FONT_SMALL,
                                   bg=BG_CARD, fg=FG_DIM, anchor="w")
        self.desc_label.pack(anchor="w")

        meta = tk.Frame(top, bg=BG_CARD)
        meta.pack(side="left", padx=16)

        tk.Label(meta, text=f"py{cfg['py']}", font=FONT_SMALL,
                 bg=BG_CARD, fg=ACCENT_DIM).pack()
        self.uptime_label = tk.Label(meta, text="—", font=FONT_SMALL,
                                     bg=BG_CARD, fg=FG_DIM)
        self.uptime_label.pack()

        btn_frame = tk.Frame(top, bg=BG_CARD)
        btn_frame.pack(side="right")

        self.start_btn   = self._btn(btn_frame, "▶ START",   GREEN,   self.monitor.start)
        self.stop_btn    = self._btn(btn_frame, "■ STOP",    RED,     self.monitor.stop)
        self.restart_btn = self._btn(btn_frame, "↺ RESTART", YELLOW,  self.monitor.restart)
        self.log_btn     = self._btn(btn_frame, "LOG ▾",     FG_DIM,  self._toggle_log)

        self.start_btn.pack(side="left", padx=(0, 4))
        self.stop_btn.pack(side="left", padx=(0, 4))
        self.restart_btn.pack(side="left", padx=(0, 4))
        self.log_btn.pack(side="left")

        self.log_frame = tk.Frame(self, bg=BG_LOG)

        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            font=FONT_MONO,
            bg=BG_LOG,
            fg=FG,
            insertbackground=ACCENT,
            selectbackground=ACCENT_DIM,
            relief="flat",
            height=12,
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True, padx=4, pady=(2, 4))
        self.log_text.tag_configure("err",  foreground=RED)
        self.log_text.tag_configure("mgr",  foreground=ACCENT_DIM)
        self.log_text.tag_configure("norm", foreground=FG)
        self.log_text.config(state="disabled")


    @staticmethod
    def _btn(parent, text, color, cmd):
        return tk.Button(
            parent, text=text, command=cmd,
            font=FONT_SMALL, bg=BG_PANEL, fg=color,
            relief="flat", padx=6, pady=2,
            activebackground=BORDER, activeforeground=color,
            cursor="hand2", bd=0,
            highlightthickness=1, highlightbackground=BORDER,
        )

    def _toggle_log(self):
        self.log_open = not self.log_open
        if self.log_open:
            self.log_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            self.log_btn.config(text="LOG ▴")
        else:
            self.log_frame.pack_forget()
            self.log_btn.config(text="LOG ▾")


    def refresh(self):
        try:
            while True:
                line, is_err = self.monitor.log_queue.get_nowait()
                self._append_log(line, is_err)
        except queue.Empty:
            pass

        status = self.monitor.status
        color  = {
            "ok":      GREEN,
            "error":   YELLOW,
            "stopped": RED,
        }[status]
        self.light.config(fg=color)

        self.uptime_label.config(text=self.monitor.uptime_str)

        running = self.monitor.running
        self.start_btn.config(state="disabled" if running else "normal")
        self.stop_btn.config(state="normal" if running else "disabled")
        self.restart_btn.config(state="normal" if running else "disabled")

    def _append_log(self, line: str, is_err: bool):
        self.log_text.config(state="normal")

        tag = "err" if is_err else ("mgr" if line.startswith("[MANAGER]") else "norm")
        ts  = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {line}", tag)

        self._log_lines += 1
        if self._log_lines > self.LOG_MAX_LINES:
            self.log_text.delete("1.0", "50.0")
            self._log_lines -= 50

        self.log_text.see("end")
        self.log_text.config(state="disabled")


class HeckNetManager(tk.Tk):
    TICK_MS = 500   # UI refresh interval

    def __init__(self):
        super().__init__()
        self.title("HeckNet System Manager")
        self.configure(bg=BG)
        self.minsize(720, 400)
        self.geometry("820x620")
        self.resizable(True, True)

        try:
            self.iconbitmap(default="")
        except Exception:
            pass

        self._monitors = [ProcessMonitor(cfg) for cfg in SCRIPTS]
        self._cards    = []
        self._build_ui()
        self._tick()

    def _build_ui(self):
        header = tk.Frame(self, bg=BG, padx=16, pady=12)
        header.pack(fill="x")

        title_line = tk.Frame(header, bg=BG)
        title_line.pack(fill="x")

        tk.Label(title_line, text="◈ HECKNET", font=FONT_TITLE,
                 bg=BG, fg=ACCENT).pack(side="left")
        tk.Label(title_line, text=" SYSTEM MANAGER", font=FONT_TITLE,
                 bg=BG, fg=FG_LABEL).pack(side="left")

        self.clock_label = tk.Label(title_line, text="", font=FONT_SMALL,
                                    bg=BG, fg=FG_DIM)
        self.clock_label.pack(side="right")

        tk.Label(header, text="Process monitor · Start/stop scripts · Live log tails",
                 font=FONT_SMALL, bg=BG, fg=FG_DIM).pack(anchor="w")

        tk.Frame(self, bg=ACCENT_DIM, height=1).pack(fill="x")

        ctrl = tk.Frame(self, bg=BG_PANEL, padx=12, pady=6)
        ctrl.pack(fill="x")

        tk.Label(ctrl, text="ALL PROCESSES:", font=FONT_SMALL,
                 bg=BG_PANEL, fg=FG_DIM).pack(side="left", padx=(0, 8))

        tk.Button(
            ctrl, text="▶ START ALL", font=FONT_SMALL,
            bg=BG_PANEL, fg=GREEN, relief="flat",
            padx=8, pady=2, cursor="hand2",
            activebackground=BORDER, activeforeground=GREEN,
            highlightthickness=1, highlightbackground=BORDER,
            command=self._start_all
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            ctrl, text="■ STOP ALL", font=FONT_SMALL,
            bg=BG_PANEL, fg=RED, relief="flat",
            padx=8, pady=2, cursor="hand2",
            activebackground=BORDER, activeforeground=RED,
            highlightthickness=1, highlightbackground=BORDER,
            command=self._stop_all
        ).pack(side="left")

        self.summary_label = tk.Label(ctrl, text="", font=FONT_SMALL,
                                      bg=BG_PANEL, fg=FG_DIM)
        self.summary_label.pack(side="right")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical",
                                  command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.cards_frame = tk.Frame(canvas, bg=BG)
        self.cards_window = canvas.create_window(
            (0, 0), window=self.cards_frame, anchor="nw"
        )

        def _on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.cards_frame.bind("<Configure>", _on_frame_configure)

        def _on_canvas_configure(e):
            canvas.itemconfig(self.cards_window, width=e.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        for monitor in self._monitors:
            card = ScriptCard(self.cards_frame, monitor)
            card.pack(fill="x", padx=12, pady=(8, 0))
            self._cards.append(card)

        tk.Frame(self.cards_frame, bg=BG, height=12).pack()

        statusbar = tk.Frame(self, bg=BG_PANEL, padx=12, pady=4)
        statusbar.pack(fill="x", side="bottom")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", side="bottom")

        self.statusbar_label = tk.Label(
            statusbar, text="HECKNET MANAGER ONLINE", font=FONT_SMALL,
            bg=BG_PANEL, fg=ACCENT_DIM
        )
        self.statusbar_label.pack(side="left")

        tk.Label(statusbar, text=f"Monitoring {len(SCRIPTS)} processes",
                 font=FONT_SMALL, bg=BG_PANEL, fg=FG_DIM).pack(side="right")


    def _start_all(self):
        for m in self._monitors:
            if not m.running:
                threading.Thread(target=m.start, daemon=True).start()

    def _stop_all(self):
        for m in self._monitors:
            if m.running:
                threading.Thread(target=m.stop, daemon=True).start()


    def _tick(self):
        now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        self.clock_label.config(text=now)

        statuses = [m.status for m in self._monitors]
        n_ok      = statuses.count("ok")
        n_err     = statuses.count("error")
        n_stopped = statuses.count("stopped")

        parts = []
        if n_ok:      parts.append(f"● {n_ok} ok")
        if n_err:     parts.append(f"● {n_err} warn")
        if n_stopped: parts.append(f"● {n_stopped} stopped")
        self.summary_label.config(text="   ".join(parts) if parts else "")

        for card in self._cards:
            card.refresh()

        self.after(self.TICK_MS, self._tick)

    def on_close(self):
        for m in self._monitors:
            try:
                m.stop()
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    app = HeckNetManager()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
