from __future__ import annotations
import os
import sys

# Add parent directory to path to locate the utils package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import timing
from pynput.mouse import Button as MouseButton, Controller as MouseController, Listener as MouseListener
from pynput.keyboard import Controller as KeyboardController, Key, Listener as KeyboardListener
import keyboard

import ctypes
import json
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Any


def _bootstrap_venv() -> None:
    """Re-exec the script with the project .venv Python when launched via the wrong interpreter."""
    if getattr(sys, "frozen", False):
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(script_dir, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        return

    current_python = os.path.abspath(sys.executable).lower()
    target_python = os.path.abspath(venv_python).lower()
    if current_python == target_python:
        return

    script_path = os.path.abspath(__file__)
    args = [venv_python, script_path, *sys.argv[1:]]
    try:
        os.execv(venv_python, args)
    except Exception:
        completed = subprocess.run(args)
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    _bootstrap_venv()


APP_NAME = "Dupe Item"
VERSION = "1.0.0"
ICON_FILE = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "icon.ico")

CONFIG_DIR = os.path.join(os.environ.get("APPDATA", "."), "QuickDupeSlotSwap")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

pynput_keyboard = KeyboardController()
pynput_mouse = MouseController()


class KeyboardHotkeyListener:
    def __init__(self, callback):
        self.callback = callback
        self.handler = None

    def start(self, hotkey_str: str):
        self.stop()
        try:
            # Register using keyboard module
            self.handler = keyboard.add_hotkey(hotkey_str.strip().lower(), self.callback)
            print(f"[HOTKEY] Keyboard hotkey listener registered successfully for: {hotkey_str}")
        except Exception as e:
            print(f"[HOTKEY] Keyboard hotkey listener failed to register: {e}")
            raise e

    def stop(self):
        if self.handler is not None:
            try:
                keyboard.remove_hotkey(self.handler)
            except Exception:
                pass
            self.handler = None


def load_config() -> dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(config: dict[str, Any]) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def _check_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


class SlotSwapToolApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_NAME} {VERSION}")
        self.root.geometry("442x410")
        self.root.resizable(False, False)

        self._configure_window_chrome()

        self.root.bell = lambda: None
        self.root.bind("<Key>", lambda e: None)

        self.colors = {
            "bg": "#1e1e1e",
            "bg_light": "#2d2d2d",
            "accent": "#3c3c3c",
            "text": "#e0e0e0",
            "text_dim": "#808080",
            "highlight": "#e94560",
            "warning": "#ff9f1c",
        }
        self.root.configure(bg=self.colors["bg"])
        self.setup_dark_theme()

        self.config = load_config()

        self.slot_positions = [tuple(p) for p in self.config.get("slot_positions", [])]
        if not self.slot_positions:
            s1 = self.config.get("slot1_pos", [0, 0])
            s2 = self.config.get("slot2_pos", [0, 0])
            if s1 != [0, 0] and s2 != [0, 0]:
                self.slot_positions = [tuple(s1), tuple(s2)]
        self.hotkey_var = tk.StringVar(value=self.config.get("hotkey", ""))
        self.status_var = tk.StringVar(value="Ready")
        self.positions_var = tk.StringVar(value=self._positions_text())

        self.move_left_px_var = tk.IntVar(
            value=int(self.config.get("move_left_px", 600)))
        self.move_steps_var = tk.IntVar(
            value=int(self.config.get("move_steps", 50)))
        self.step_delay_var = tk.IntVar(
            value=int(self.config.get("step_delay", 25)))
        self.settle_delay_var = tk.IntVar(
            value=int(self.config.get("settle_delay", 15)))
        self.speed_var = tk.DoubleVar(
            value=float(self.config.get("speed", 1.0)))
        self.repeat_var = tk.BooleanVar(
            value=bool(self.config.get("repeat", False)))
        self.repeat_count_var = tk.IntVar(
            value=int(self.config.get("repeat_count", 5)))
        self.initial_tab_var = tk.BooleanVar(
            value=bool(self.config.get("initial_tab", False)))

        self.running = False
        self.stop_flag = False
        self.recording_hotkey = False
        self.recording_positions = False
        self.hotkey_registered = None
        self.hotkey_lock = threading.Lock()
        self.cooldown_until = 0
        self._recording_previous_value = ""
        self.hotkey_listener = KeyboardHotkeyListener(lambda: self.root.after(0, self.toggle_macro))
        self._position_esc_listener = None

        self.build_ui()
        self._apply_config_to_ui()
        self.register_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _configure_window_chrome(self) -> None:
        """Hide the default title bar using Windows API, keeping taskbar and focus functionality intact."""
        if os.path.exists(ICON_FILE):
            try:
                self.root.iconbitmap(default=ICON_FILE)
            except Exception:
                pass

        if os.name != "nt":
            return

        try:
            self.root.update_idletasks()
            hwnd = self.root.winfo_id()
            user32 = ctypes.windll.user32
            get_window_long = getattr(
                user32, "GetWindowLongPtrW", user32.GetWindowLongW)
            set_window_long = getattr(
                user32, "SetWindowLongPtrW", user32.SetWindowLongW)

            GWL_STYLE = -16
            WS_CAPTION = 0x00C00000
            
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            SWP_FRAMECHANGED = 0x0020

            # Remove title bar/borders using GWL_STYLE (WS_CAPTION)
            style = get_window_long(hwnd, GWL_STYLE)
            style = int(style) & ~WS_CAPTION
            set_window_long(hwnd, GWL_STYLE, style)

            user32.SetWindowPos(
                hwnd,
                None,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
            )
        except Exception:
            pass

    def setup_dark_theme(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            ".", background=self.colors["bg"], foreground=self.colors["text"])
        style.configure("TFrame", background=self.colors["bg"])
        style.configure(
            "TLabel", background=self.colors["bg"], foreground=self.colors["text"])
        style.configure(
            "TButton",
            background=self.colors["bg_light"],
            foreground=self.colors["text"],
            borderwidth=0,
            relief="flat",
            focuscolor="",
        )
        style.map("TButton", background=[("active", self.colors["highlight"])])
        style.configure(
            "TCheckbutton",
            background=self.colors["bg"],
            foreground=self.colors["text"],
            indicatorbackground=self.colors["bg_light"],
            indicatorforeground=self.colors["text"],
            indicatorsize=16,
        )
        style.configure(
            "TEntry",
            fieldbackground=self.colors["bg_light"],
            foreground=self.colors["text"],
            borderwidth=0,
            relief="flat",
            padding=2,
        )
        style.configure(
            "Header.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["highlight"],
            font=("Arial", 11, "bold"),
        )
        style.configure(
            "Dim.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["text_dim"],
        )

    def build_ui(self):
        # Resize window to accommodate additional controls
        self.root.geometry("442x410")

        title_bar = tk.Frame(self.root, bg=self.colors["bg_light"], height=32)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)

        self._drag_x = 0
        self._drag_y = 0

        def start_drag(event):
            self._drag_x = event.x
            self._drag_y = event.y

        def drag(event):
            x = self.root.winfo_x() + event.x - self._drag_x
            y = self.root.winfo_y() + event.y - self._drag_y
            self.root.geometry(f"+{x}+{y}")

        title_label = tk.Label(
            title_bar,
            text=f"{APP_NAME} {VERSION}",
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            font=("Arial", 10, "bold"),
        )
        title_label.pack(side="left", padx=8)
        title_label.bind("<Button-1>", start_drag)
        title_label.bind("<B1-Motion>", drag)
        title_bar.bind("<Button-1>", start_drag)
        title_bar.bind("<B1-Motion>", drag)

        close_btn = tk.Label(
            title_bar,
            text=" ✕ ",
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            font=("Arial", 12),
            cursor="hand2",
        )
        close_btn.pack(side="right", padx=2)
        close_btn.bind("<Button-1>", lambda e: self.on_close())
        close_btn.bind("<Enter>", lambda e: close_btn.config(
            bg=self.colors["highlight"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(
            bg=self.colors["bg_light"]))

        min_btn = tk.Label(
            title_bar,
            text=" ─ ",
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            font=("Arial", 12),
            cursor="hand2",
        )
        min_btn.pack(side="right", padx=2)
        min_btn.bind("<Button-1>", lambda e: self.minimize_window())
        min_btn.bind("<Enter>", lambda e: min_btn.config(
            bg=self.colors["accent"]))
        min_btn.bind("<Leave>", lambda e: min_btn.config(
            bg=self.colors["bg_light"]))

        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        frame = ttk.Frame(container)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(frame, text="── Dupe Item ──",
                  style="Header.TLabel").pack(pady=(5, 5))

        hk_frame = ttk.Frame(frame)
        hk_frame.pack(fill="x", pady=4)
        ttk.Label(hk_frame, text="Hotkey:").pack(side="left")
        self.hotkey_entry = tk.Entry(
            hk_frame,
            textvariable=self.hotkey_var,
            width=16,
            state="readonly",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            readonlybackground=self.colors["bg_light"],
        )
        self.hotkey_entry.pack(side="left", padx=5)
        self.hotkey_btn = ttk.Button(
            hk_frame, text="Set", width=6, command=self.start_recording_hotkey)
        self.hotkey_btn.pack(side="left")

        pos_frame = ttk.Frame(frame)
        pos_frame.pack(fill="x", pady=4)
        self.pos_btn = ttk.Button(
            pos_frame, text="Record Slots", width=14, command=self.start_recording_positions)
        self.pos_btn.pack(side="left")
        ttk.Label(pos_frame, textvariable=self.positions_var,
                  font=("Consolas", 8)).pack(side="left", padx=6)



        self.create_slider(
            frame, "Move left distance:", self.move_left_px_var, 600, 10, 1000, "px",
            "Der Abstand (in Pixeln), um den die Maus beim Halten von Alt nach links gezogen wird, um das Item temporär aus dem Slot zu bewegen."
        )
        self.create_slider(
            frame, "Move steps:", self.move_steps_var, 50, 1, 150, "",
            "Die Anzahl der Zwischenschritte während der Mausbewegung. Mehr Schritte bedeuten eine flüssigere, natürlichere Bewegung."
        )
        self.create_slider(
            frame, "Step delay:", self.step_delay_var, 25, 0, 100, "ms",
            "Die Verzögerung (in Millisekunden) zwischen den einzelnen Bewegungsschritten. Beeinflusst die Geschwindigkeit des Ziehvorgangs."
        )
        self.create_slider(
            frame, "Settle delay:", self.settle_delay_var, 15, 0, 200, "ms",
            "Die Wartezeit (in Millisekunden) nach Klicks oder Tastenaktionen, damit das Spiel die Aktion sicher verarbeiten kann."
        )
        self.create_slider(
            frame, "Speed factor:", self.speed_var, 1.0, 0.1, 5.0, "x",
            "Ein Multiplikator (z.B. 2.0x), der alle Verzögerungen verkürzt und den gesamten Ablauf beschleunigt."
        )

        chk_frame = ttk.Frame(frame)
        chk_frame.pack(fill="x", pady=4)
        self.tab_chk = ttk.Checkbutton(
            chk_frame,
            text="Initial Tab Press",
            variable=self.initial_tab_var,
            command=self.save_settings,
        )
        self.tab_chk.pack(side="left", padx=5)
        self.repeat_chk = ttk.Checkbutton(
            chk_frame,
            text="Repeat",
            variable=self.repeat_var,
            command=self.save_settings,
        )
        self.repeat_chk.pack(side="left", padx=5)
        ttk.Label(chk_frame, text="Times:").pack(side="left", padx=(5, 2))
        self.repeat_count_entry = tk.Entry(
            chk_frame,
            textvariable=self.repeat_count_var,
            width=4,
            justify="center",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
        )
        self.repeat_count_entry.pack(side="left")
        self.repeat_count_entry.bind("<FocusOut>", lambda e: self.save_settings())
        self.repeat_count_entry.bind("<Return>", lambda e: self.save_settings())

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(8, 4))
        self.toggle_btn = ttk.Button(
            btn_frame, text="Start", width=10, command=self.toggle_macro)
        self.toggle_btn.pack(side="left", padx=3)
        ttk.Button(btn_frame, text="Save", width=8,
                   command=self.save_settings).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="Reset", width=8,
                   command=self.reset_defaults).pack(side="left", padx=3)

        self.status_label = ttk.Label(
            frame, textvariable=self.status_var, style="Dim.TLabel")
        self.status_label.pack(pady=(8, 0))

        footer = ttk.Label(
            frame,
            text="ESC stoppt das laufende Makro.",
            style="Dim.TLabel",
        )
        footer.pack(pady=(10, 0))

    def _add_tooltip(self, widget, text):
        """Add hover tooltip to a widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_attributes("-topmost", True)
            tooltip.configure(bg=self.colors["bg_light"])
            label = tk.Label(
                tooltip,
                text=text,
                justify="left",
                bg=self.colors["bg_light"],
                fg=self.colors["text"],
                relief="solid",
                borderwidth=1,
                padx=8,
                pady=6,
                font=("Segoe UI", 9),
            )
            label.pack()
            tooltip.update_idletasks()

            # Smart positioning - flip to left if near right edge
            tip_width = tooltip.winfo_width()
            screen_width = tooltip.winfo_screenwidth()
            x = event.x_root + 20
            if x + tip_width > screen_width:
                x = event.x_root - tip_width - 10
            tooltip.wm_geometry(f"+{x}+{event.y_root + 20}")
            widget._tooltip = tooltip

        def hide_tooltip(event):
            if hasattr(widget, "_tooltip") and widget._tooltip:
                widget._tooltip.destroy()
                widget._tooltip = None

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def create_slider(self, parent, label, var, default, min_val, max_val, unit, tooltip_text=""):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        
        ttk.Label(row, text=label, width=18, anchor="w").pack(side="left")
        info_lbl = tk.Label(
            row,
            text="ⓘ",
            fg=self.colors["text_dim"],
            bg=self.colors["bg"],
            font=("Arial", 9),
            cursor="hand2",
        )
        info_lbl.pack(side="left", padx=(0, 10))
        if tooltip_text:
            self._add_tooltip(info_lbl, tooltip_text)

        slider = ttk.Scale(
            row,
            from_=min_val,
            to=max_val,
            variable=var,
            orient="horizontal",
            length=100,
            command=lambda _v: self.save_settings(),
        )
        slider.pack(side="left", padx=5)
        entry = tk.Entry(
            row,
            width=5,
            justify="center",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
        )
        entry.pack(side="left")
        
        val = var.get()
        if isinstance(var, tk.DoubleVar):
            entry.insert(0, f"{val:.1f}")
        else:
            entry.insert(0, str(val))

        def on_entry(_event=None):
            try:
                if isinstance(var, tk.DoubleVar):
                    value = float(entry.get())
                else:
                    value = int(entry.get())
                var.set(value)
                self.save_settings()
            except ValueError:
                entry.delete(0, "end")
                val = var.get()
                if isinstance(var, tk.DoubleVar):
                    entry.insert(0, f"{val:.1f}")
                else:
                    entry.insert(0, str(val))

        def on_var(*_args):
            entry.delete(0, "end")
            val = var.get()
            if isinstance(var, tk.DoubleVar):
                entry.insert(0, f"{val:.1f}")
            else:
                entry.insert(0, str(val))

        entry.bind("<Return>", on_entry)
        entry.bind("<FocusOut>", on_entry)
        var.trace_add("write", on_var)
        if unit:
            ttk.Label(row, text=unit).pack(side="left")

    def _positions_text(self) -> str:
        if not self.slot_positions:
            return "No positions"
        pos_strs = [f"S{i+1}:{list(pos)}" for i, pos in enumerate(self.slot_positions[:2])]
        if len(self.slot_positions) > 2:
            pos_strs.append(f"(+{len(self.slot_positions)-2} mehr)")
        return " ".join(pos_strs)

    def save_settings(self):
        self.config["hotkey"] = self.hotkey_var.get()
        self.config["slot_positions"] = self.slot_positions
        self.config["move_left_px"] = self.move_left_px_var.get()
        self.config["move_steps"] = self.move_steps_var.get()
        self.config["step_delay"] = self.step_delay_var.get()
        self.config["settle_delay"] = self.settle_delay_var.get()
        self.config["speed"] = self.speed_var.get()
        self.config["repeat"] = self.repeat_var.get()
        self.config["repeat_count"] = self.repeat_count_var.get()
        self.config["initial_tab"] = self.initial_tab_var.get()
        save_config(self.config)

    def reset_defaults(self):
        self.move_left_px_var.set(600)
        self.move_steps_var.set(50)
        self.step_delay_var.set(25)
        self.settle_delay_var.set(15)
        self.speed_var.set(1.0)
        self.repeat_var.set(False)
        self.repeat_count_var.set(5)
        self.initial_tab_var.set(False)
        self.status_var.set("Defaults restored")
        self.save_settings()

    def _apply_config_to_ui(self):
        self.slot_positions = [tuple(p) for p in self.config.get("slot_positions", [])]
        if not self.slot_positions:
            s1 = self.config.get("slot1_pos", [0, 0])
            s2 = self.config.get("slot2_pos", [0, 0])
            if s1 != [0, 0] and s2 != [0, 0]:
                self.slot_positions = [tuple(s1), tuple(s2)]
        self.positions_var.set(self._positions_text())
        self.hotkey_var.set(self.config.get("hotkey", ""))
        self.move_left_px_var.set(int(self.config.get("move_left_px", 600)))
        self.move_steps_var.set(int(self.config.get("move_steps", 50)))
        self.step_delay_var.set(int(self.config.get("step_delay", 25)))
        self.settle_delay_var.set(int(self.config.get("settle_delay", 15)))
        self.speed_var.set(float(self.config.get("speed", 1.0)))
        self.repeat_var.set(bool(self.config.get("repeat", False)))
        self.repeat_count_var.set(int(self.config.get("repeat_count", 5)))
        self.initial_tab_var.set(bool(self.config.get("initial_tab", False)))

    def minimize_window(self):
        if self.root.winfo_exists():
            self.root.iconify()

    def start_recording_hotkey(self):
        self._recording_previous_value = self.hotkey_var.get()
        self.recording_hotkey = True
        self.hotkey_btn.config(text="...")
        self.hotkey_var.set("Press key...")
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_force()

    def on_key_press(self, event):
        if not self.recording_hotkey:
            return

        key = event.keysym.lower()
        key_map = {
            "next": "page down",
            "prior": "page up",
            "escape": "esc",
            "return": "enter",
            "control_l": "ctrl",
            "control_r": "ctrl",
            "alt_l": "alt",
            "alt_r": "alt",
            "shift_l": "shift",
            "shift_r": "shift",
            "space": "space",
            "tab": "tab",
            "backspace": "backspace",
            "minus": "-",
            "plus": "+",
            "equal": "=",
        }
        key = key_map.get(key, key)

        if key == "esc":
            self.hotkey_var.set(self._recording_previous_value)
            self.hotkey_btn.config(text="Set")
            self.recording_hotkey = False
            self.root.unbind("<KeyPress>")
            self.status_var.set("Hotkey recording cancelled")
            return

        modifier_keys = {
            "ctrl", "alt", "shift", "control_l", "control_r", "alt_l", "alt_r", "shift_l", "shift_r"
        }
        if key not in modifier_keys:
            parts = []
            if keyboard.is_pressed("ctrl"):
                parts.append("ctrl")
            if keyboard.is_pressed("alt"):
                parts.append("alt")
            if keyboard.is_pressed("shift"):
                parts.append("shift")
            parts.append(key)
            hotkey = "+".join(parts)
            self.hotkey_var.set(hotkey)
            self.hotkey_btn.config(text="Set")
            self.recording_hotkey = False
            self.root.unbind("<KeyPress>")
            self.save_settings()
            self.register_hotkeys()
            self.status_var.set(f"Hotkey: {hotkey}")
    def _hotkey_to_pynput(self, hotkey: str) -> str:
        parts = []
        for token in hotkey.split("+"):
            token = token.strip().lower()
            if not token:
                continue
            if token in {"ctrl", "control", "control_l", "control_r"}:
                parts.append("<ctrl>")
            elif token in {"alt", "alt_l", "alt_r"}:
                parts.append("<alt>")
            elif token in {"shift", "shift_l", "shift_r"}:
                parts.append("<shift>")
            elif token in {"esc", "escape"}:
                parts.append("<esc>")
            elif token in {"page up", "page_up"}:
                parts.append("<page_up>")
            elif token in {"page down", "page_down"}:
                parts.append("<page_down>")
            else:
                parts.append(token)
        return "+".join(parts)

    def _stop_hotkey_listener(self):
        try:
            self.hotkey_listener.stop()
        except Exception:
            pass

    def _register_hotkey_callback(self):
        self._stop_hotkey_listener()
        hk = self.hotkey_var.get().strip()
        if not hk or hk in {"Press key...", "..."}:
            return

        try:
            print(f"[HOTKEY] Registering Win32 hotkey for: {hk}")
            self.hotkey_listener.start(hk)
            self.hotkey_registered = hk
            self.status_var.set(f"Hotkey Active: {hk}")
        except Exception as e:
            self.status_var.set(f"Hotkey error: {e}")
            self.hotkey_registered = None
            print(f"[HOTKEY] Hotkey registration failed: {e}")



    def start_recording_positions(self):
        self.recording_positions = True
        self.slot_positions = []
        self.positions_var.set("Klicke Slots... (Enter = Fertig, ESC = Abbruch)")
        self.status_var.set("Aufnahme...")
        self.pos_btn.config(state="disabled")

        # Disable main ESC stop hotkey during recording so it doesn't conflict
        try:
            keyboard.remove_hotkey("esc")
        except Exception:
            pass

        # Global keyboard hooks for Enter and Escape during recording
        try:
            keyboard.add_hotkey("enter", self.finish_recording_positions, suppress=True)
            keyboard.add_hotkey("esc", self.cancel_recording_positions, suppress=True)
        except Exception:
            pass

        def on_click(x, y, button, pressed):
            if pressed and button == MouseButton.left:
                self.slot_positions.append((int(x), int(y)))
                self.root.after(0, lambda: self.positions_var.set(
                    f"Slots: {len(self.slot_positions)} (Enter = Fertig, ESC = Abbruch)"
                ))

        self.mouse_listener = MouseListener(on_click=on_click)
        self.mouse_listener.start()

    def finish_recording_positions(self):
        self._stop_position_recording_listeners()
        if len(self.slot_positions) < 2:
            self.status_var.set("Fehler: Mindestens 2 Slots benötigt")
            self._apply_config_to_ui()
        else:
            self.status_var.set(f"{len(self.slot_positions)} Slots aufgenommen")
            self.save_settings()
        self.pos_btn.config(state="normal")

    def cancel_recording_positions(self):
        self._stop_position_recording_listeners()
        self.status_var.set("Aufnahme abgebrochen")
        self.pos_btn.config(state="normal")
        self._apply_config_to_ui()

    def _stop_position_recording_listeners(self):
        try:
            if hasattr(self, "mouse_listener") and self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
        except Exception:
            pass
        try:
            keyboard.remove_hotkey("enter")
        except Exception:
            pass
        try:
            keyboard.remove_hotkey("esc")
        except Exception:
            pass
        self.register_hotkeys()

    def stop_macro(self):
        if self.running:
            self.stop_flag = True
            self.status_var.set("Stopping...")
            print("[SLOT-SWAP] Macro stop requested via ESC")

    def register_hotkeys(self):
        self._register_hotkey_callback()
        try:
            keyboard.remove_hotkey("esc")
        except Exception:
            pass
        try:
            keyboard.add_hotkey("esc", self.stop_macro)
        except Exception:
            pass

    def toggle_macro(self):
        if not self.hotkey_lock.acquire(blocking=False):
            return
        try:
            if self.running:
                self.stop_flag = True
                self.status_var.set("Stopping...")
                return

            now = int(time.time() * 1000)
            if now < self.cooldown_until:
                return

            if len(self.slot_positions) < 2:
                self.status_var.set("Bitte zuerst Slots aufnehmen (min. 2)")
                return

            self.running = True
            self.stop_flag = False
            self.toggle_btn.config(text="Stop")
            self.status_var.set("RUNNING")
            threading.Thread(target=self.run_macro, daemon=True).start()
        finally:
            self.hotkey_lock.release()

    def _set_mouse_pos(self, pos: tuple[int, int]) -> None:
        x, y = int(pos[0]), int(pos[1])
        try:
            pynput_mouse.position = (x, y)
        except Exception:
            pass
        try:
            ctypes.windll.user32.SetCursorPos(x, y)
        except Exception:
            pass
    def _drag_line(
        self,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        *,
        use_alt: bool,
        move_steps: int,
        step_delay: int,
        settle_delay: int,
    ) -> None:
        if self.stop_flag:
            return

        speed = max(0.01, self.speed_var.get())
        start_x, start_y = int(start_pos[0]), int(start_pos[1])
        end_x, end_y = int(end_pos[0]), int(end_pos[1])

        self._set_mouse_pos((start_x, start_y))
        time.sleep(0.05)

        if self.stop_flag:
            return

        if use_alt:
            try:
                ctypes.windll.user32.keybd_event(0x12, 0x38, 0, 0) # Alt down
            except Exception:
                pynput_keyboard.press(Key.alt)

        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0) # MOUSEEVENTF_LEFTDOWN

        # Scale step delay so total drag duration remains constant relative to the baseline of 12 steps
        actual_step_delay = (step_delay * 12.0) / max(1, move_steps)

        for i in range(1, move_steps + 1):
            if self.stop_flag:
                break
            t = i / move_steps
            x = int(round(start_x + (end_x - start_x) * t))
            y = int(round(start_y + (end_y - start_y) * t))
            self._set_mouse_pos((x, y))
            timing.vsleep(
                max(0, int(actual_step_delay / speed)), stop_check=lambda: self.stop_flag, variance_pct=0)

        # Release mouse and alt regardless of stop_flag (to avoid stuck mouse/alt states), but do it instantly without settle delays if stop_flag is set!
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0) # MOUSEEVENTF_LEFTUP
        
        if use_alt:
            try:
                ctypes.windll.user32.keybd_event(0x12, 0x38, 0x0002, 0) # Alt up
            except Exception:
                pass
            try:
                pynput_keyboard.release(Key.alt)
            except Exception:
                pass

        if self.stop_flag:
            return

        timing.vsleep(
            max(0, int(settle_delay / speed)), stop_check=lambda: self.stop_flag, variance_pct=0)

    def _run_slot_swap_sequence(self, timings: dict[str, Any]) -> None:
        speed = max(0.01, self.speed_var.get())
        move_distance = max(0, int(timings.get("move_left_px", 120)))
        move_steps = max(1, int(timings.get("move_steps", 12)))
        step_delay = max(0, int(timings.get("step_delay", 5)))
        settle_delay = max(0, int(timings.get("settle_delay", 25)))
        between_slots_delay = max(
            0, int(timings.get("between_slots_delay", 40)))

        def _cleanup() -> None:
            try:
                ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0) # MOUSEEVENTF_LEFTUP
            except Exception:
                pass
            try:
                ctypes.windll.user32.keybd_event(0x12, 0x38, 0x0002, 0) # Alt up
            except Exception:
                pass
            try:
                pynput_keyboard.release(Key.alt)
            except Exception:
                pass

        _cleanup()

        # 1) Alt-drag left on all recorded slots
        for i, pos in enumerate(self.slot_positions):
            if self.stop_flag:
                return
            px, py = int(pos[0]), int(pos[1])
            self._drag_line(
                (px, py),
                (px - move_distance, py),
                use_alt=True,
                move_steps=move_steps,
                step_delay=step_delay,
                settle_delay=settle_delay,
            )
            if self.stop_flag:
                return
            if i < len(self.slot_positions) - 1:
                timing.vsleep(max(0, int(between_slots_delay / speed)),
                              stop_check=lambda: self.stop_flag, variance_pct=0)

        if self.stop_flag:
            return
        timing.vsleep(max(0, int(between_slots_delay / speed)),
                      stop_check=lambda: self.stop_flag, variance_pct=0)

        # 2) Drag sequentially from S_i to S_{i+1}
        for i in range(len(self.slot_positions) - 1):
            if self.stop_flag:
                return
            self._drag_line(
                self.slot_positions[i],
                self.slot_positions[i+1],
                use_alt=False,
                move_steps=move_steps,
                step_delay=step_delay,
                settle_delay=settle_delay,
            )
            if self.stop_flag:
                return
            if i < len(self.slot_positions) - 2:
                timing.vsleep(max(0, int(between_slots_delay / speed)),
                              stop_check=lambda: self.stop_flag, variance_pct=0)

        _cleanup()

    def run_macro(self):
        try:
            loop_count = 0
            max_loops = self.repeat_count_var.get() if self.repeat_var.get() else 1

            while True:
                # Perform tab press if enabled on each iteration to reopen inventory if it closed
                if self.initial_tab_var.get() and not self.stop_flag:
                    try:
                        # Try using win32 API keybd_event (extremely reliable for games/directinput)
                        VK_TAB = 0x09
                        SCAN_TAB = 0x0F
                        KEYEVENTF_KEYUP = 0x0002
                        ctypes.windll.user32.keybd_event(VK_TAB, SCAN_TAB, 0, 0)
                        time.sleep(0.15)
                        ctypes.windll.user32.keybd_event(VK_TAB, SCAN_TAB, KEYEVENTF_KEYUP, 0)
                    except Exception:
                        # Fallback to pynput
                        pynput_keyboard.press(Key.tab)
                        time.sleep(0.15)
                        pynput_keyboard.release(Key.tab)
                    time.sleep(0.3)

                timings = {
                    "move_left_px": self.move_left_px_var.get(),
                    "move_steps": self.move_steps_var.get(),
                    "step_delay": self.step_delay_var.get(),
                    "settle_delay": self.settle_delay_var.get(),
                }
                self._run_slot_swap_sequence(timings)

                loop_count += 1
                if self.stop_flag:
                    break
                if max_loops > 0 and loop_count >= max_loops:
                    break

                # Sleep brief interval between repeats scaled by speed (increased minimum to 150ms)
                speed = max(0.01, self.speed_var.get())
                timing.vsleep(max(150, int(300 / speed)), stop_check=lambda: self.stop_flag, variance_pct=0)
        except Exception as e:
            self.status_var.set(f"Fehler: {e}")
            print(f"[SLOT-SWAP] Error: {e}")
        finally:
            self.running = False
            self.stop_flag = False
            self.cooldown_until = int(time.time() * 1000) + 800
            self.root.after(0, lambda: self.toggle_btn.config(text="Start"))
            self.root.after(0, lambda: self.status_var.set("Ready"))



    def vsleep(self, ms):
        timing.vsleep(ms, stop_check=lambda: self.stop_flag, variance_pct=0)

    def on_close(self):
        self.stop_flag = True
        self.save_settings()
        try:
            self._stop_hotkey_listener()
            if self._position_esc_listener is not None:
                self._position_esc_listener.stop()
        except Exception:
            pass
        self.root.destroy()


def main():
    if not _check_admin():
        print("[WARN] Empfehlenswert: als Administrator starten.")
    root = tk.Tk()
    SlotSwapToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
