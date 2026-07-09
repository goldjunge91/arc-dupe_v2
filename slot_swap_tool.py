from __future__ import annotations
from utils import timing
from pynput.mouse import Button as MouseButton, Controller as MouseController
from pynput.keyboard import Controller as KeyboardController, GlobalHotKeys, Key, Listener as KeyboardListener

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


APP_NAME = "Slot Swap Tool"
VERSION = "1.0.0"
ICON_FILE = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "icon.ico")

CONFIG_DIR = os.path.join(os.environ.get("APPDATA", "."), "QuickDupeSlotSwap")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

pynput_keyboard = KeyboardController()
pynput_mouse = MouseController()


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
        self.root.geometry("442x420")
        self.root.resizable(False, False)
        self.root.overrideredirect(True)

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

        self.slot1_pos = tuple(self.config.get("slot1_pos", [0, 0]))
        self.slot2_pos = tuple(self.config.get("slot2_pos", [0, 0]))
        self.hotkey_var = tk.StringVar(value=self.config.get("hotkey", ""))
        self.status_var = tk.StringVar(value="Ready")
        self.positions_var = tk.StringVar(value=self._positions_text())

        self.move_left_px_var = tk.IntVar(
            value=int(self.config.get("move_left_px", 120)))
        self.alt_delay_var = tk.IntVar(
            value=int(self.config.get("alt_delay", 20)))
        self.click_hold_ms_var = tk.IntVar(
            value=int(self.config.get("click_hold_ms", 25)))
        self.move_steps_var = tk.IntVar(
            value=int(self.config.get("move_steps", 12)))
        self.step_delay_var = tk.IntVar(
            value=int(self.config.get("step_delay", 5)))
        self.settle_delay_var = tk.IntVar(
            value=int(self.config.get("settle_delay", 25)))
        self.repeat_count_var = tk.IntVar(
            value=int(self.config.get("repeat_count", 1)))

        self.running = False
        self.stop_flag = False
        self.recording_hotkey = False
        self.recording_positions = False
        self.hotkey_registered = None
        self.hotkey_lock = threading.Lock()
        self.cooldown_until = 0
        self._recording_previous_value = ""
        self._hotkey_listener = None
        self._position_esc_listener = None
        self.macro_json_path = self.config.get("macro_json_path", "")
        self.macro_data: dict[str, Any] | None = None
        self.macro_events: list[dict[str, Any]] = []

        self.build_ui()
        self._apply_config_to_ui()
        self.register_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _configure_window_chrome(self) -> None:
        """Keep the custom title bar but make the window show up in the taskbar."""
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

            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            SWP_FRAMECHANGED = 0x0020

            ex_style = get_window_long(hwnd, GWL_EXSTYLE)
            ex_style = (int(ex_style) | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
            set_window_long(hwnd, GWL_EXSTYLE, ex_style)
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
            # Fallback: the app still works, but may lose the custom taskbar behavior.
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

        ttk.Label(frame, text="── Slot Swap ──",
                  style="Header.TLabel").pack(pady=(5, 5))
        ttk.Label(
            frame,
            text="Standalone tool: Alt + LMB auf Slot 1, dann Slot 2.",
            style="Dim.TLabel",
        ).pack(pady=(0, 8))

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

        macro_frame = ttk.Frame(frame)
        macro_frame.pack(fill="x", pady=4)
        self.load_macro_btn = ttk.Button(
            macro_frame, text="Load Macro JSON", width=16, command=self.load_macro_json)
        self.load_macro_btn.pack(side="left")
        self.macro_file_var = tk.StringVar(
            value=os.path.basename(
                self.macro_json_path) if self.macro_json_path else "No macro loaded"
        )
        ttk.Label(
            macro_frame,
            textvariable=self.macro_file_var,
            font=("Consolas", 8),
        ).pack(side="left", padx=6)

        self.create_slider(frame, "Move left distance:",
                           self.move_left_px_var, 120, 10, 400, "px")
        self.create_slider(frame, "Alt delay:",
                           self.alt_delay_var, 20, 0, 200, "ms")
        self.create_slider(frame, "Click hold:",
                           self.click_hold_ms_var, 25, 0, 200, "ms")
        self.create_slider(frame, "Move steps:",
                           self.move_steps_var, 12, 1, 50, "")
        self.create_slider(frame, "Step delay:",
                           self.step_delay_var, 5, 0, 50, "ms")
        self.create_slider(frame, "Settle delay:",
                           self.settle_delay_var, 25, 0, 200, "ms")
        self.create_slider(frame, "Repeat count:",
                           self.repeat_count_var, 1, 1, 20, "")

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

    def create_slider(self, parent, label, var, default, min_val, max_val, unit):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=20, anchor="w").pack(side="left")
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
        entry.insert(0, str(var.get()))

        def on_entry(_event=None):
            try:
                if unit == "":
                    value = int(entry.get())
                else:
                    value = int(entry.get())
                var.set(value)
                self.save_settings()
            except ValueError:
                entry.delete(0, "end")
                entry.insert(0, str(var.get()))

        def on_var(*_args):
            entry.delete(0, "end")
            entry.insert(0, str(var.get()))

        entry.bind("<Return>", on_entry)
        entry.bind("<FocusOut>", on_entry)
        var.trace_add("write", on_var)
        if unit:
            ttk.Label(row, text=unit).pack(side="left")

    def _positions_text(self) -> str:
        return f"S1:{list(self.slot1_pos)} S2:{list(self.slot2_pos)}"

    def save_settings(self):
        self.config["hotkey"] = self.hotkey_var.get()
        self.config["slot1_pos"] = list(self.slot1_pos)
        self.config["slot2_pos"] = list(self.slot2_pos)
        self.config["macro_json_path"] = self.macro_json_path
        self.config["move_left_px"] = self.move_left_px_var.get()
        self.config["alt_delay"] = self.alt_delay_var.get()
        self.config["click_hold_ms"] = self.click_hold_ms_var.get()
        self.config["move_steps"] = self.move_steps_var.get()
        self.config["step_delay"] = self.step_delay_var.get()
        self.config["settle_delay"] = self.settle_delay_var.get()
        self.config["repeat_count"] = self.repeat_count_var.get()
        save_config(self.config)

    def reset_defaults(self):
        self.move_left_px_var.set(120)
        self.alt_delay_var.set(20)
        self.click_hold_ms_var.set(25)
        self.move_steps_var.set(12)
        self.step_delay_var.set(5)
        self.settle_delay_var.set(25)
        self.repeat_count_var.set(1)
        self.status_var.set("Defaults restored")
        self.save_settings()

    def _apply_config_to_ui(self):
        self.positions_var.set(self._positions_text())
        self.hotkey_var.set(self.config.get("hotkey", ""))
        self.macro_json_path = self.config.get("macro_json_path", "")
        self.macro_file_var.set(
            os.path.basename(
                self.macro_json_path) if self.macro_json_path else "No macro loaded"
        )
        self.move_left_px_var.set(int(self.config.get("move_left_px", 120)))
        self.alt_delay_var.set(int(self.config.get("alt_delay", 20)))
        self.click_hold_ms_var.set(int(self.config.get("click_hold_ms", 25)))
        self.move_steps_var.set(int(self.config.get("move_steps", 12)))
        self.step_delay_var.set(int(self.config.get("step_delay", 5)))
        self.settle_delay_var.set(int(self.config.get("settle_delay", 25)))
        self.repeat_count_var.set(int(self.config.get("repeat_count", 1)))
        if self.macro_json_path and os.path.exists(self.macro_json_path):
            self._load_macro_from_path(self.macro_json_path)

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
            if event.state & 0x4:
                parts.append("ctrl")
            if event.state & 0x8:
                parts.append("alt")
            if event.state & 0x1:
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
        if self._hotkey_listener is not None:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
            self._hotkey_listener = None

    def _register_hotkey_callback(self):
        self._stop_hotkey_listener()
        hk = self.hotkey_var.get().strip()
        if not hk or hk in {"Press key...", "..."}:
            return

        try:
            pynput_hotkey = self._hotkey_to_pynput(hk)

            def trigger_macro() -> None:
                self.root.after(0, self.toggle_macro)

            self._hotkey_listener = GlobalHotKeys(
                {pynput_hotkey: trigger_macro})
            self._hotkey_listener.start()
            self.hotkey_registered = pynput_hotkey
        except Exception as e:
            self.status_var.set(f"Hotkey error: {e}")
            self.hotkey_registered = None

    def _load_macro_from_path(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        events = data.get("events", [])
        if not isinstance(events, list) or not events:
            raise ValueError("JSON contains no events")

        self.macro_data = data
        self.macro_events = events
        self.macro_json_path = path
        self.macro_file_var.set(
            f"{os.path.basename(path)} ({len(events)} events)")
        self.config["macro_json_path"] = path
        save_config(self.config)

    def load_macro_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            self._load_macro_from_path(path)
            self.status_var.set(f"Loaded macro: {os.path.basename(path)}")
        except Exception as e:
            self.status_var.set(f"Load failed: {e}")

    def _start_position_esc_listener(self, cancel_callback):
        if self._position_esc_listener is not None:
            try:
                self._position_esc_listener.stop()
            except Exception:
                pass
            self._position_esc_listener = None

        def on_press(key):
            if key == Key.esc:
                cancel_callback()
                return None

        self._position_esc_listener = KeyboardListener(on_press=on_press)
        self._position_esc_listener.start()

    def start_recording_positions(self):
        from pynput import mouse

        self.recording_positions = True
        self.pos_btn.config(text="Slot 1...")
        self.status_var.set("Click Slot 1, then Slot 2")
        self._slot1_temp = None

        listener_ref: list[Any] = [None]

        def finish_cancel():
            if listener_ref[0]:
                listener_ref[0].stop()
            self.recording_positions = False
            self.pos_btn.config(text="Record Slots")
            self.status_var.set("Position recording cancelled")
            if self._position_esc_listener is not None:
                try:
                    self._position_esc_listener.stop()
                except Exception:
                    pass
                self._position_esc_listener = None

        def on_click(x, y, button, pressed):
            if button != mouse.Button.left or not pressed:
                return
            if self._slot1_temp is None:
                self._slot1_temp = (int(x), int(y))
                self.root.after(
                    0, lambda: self.pos_btn.config(text="Slot 2..."))
                self.root.after(0, lambda: self.status_var.set("Click Slot 2"))
                return

            self.slot1_pos = self._slot1_temp
            self.slot2_pos = (int(x), int(y))
            self.recording_positions = False
            self.config["slot1_pos"] = list(self.slot1_pos)
            self.config["slot2_pos"] = list(self.slot2_pos)
            save_config(self.config)
            self.positions_var.set(self._positions_text())
            self.pos_btn.config(text="Record Slots")
            self.status_var.set("Positions recorded")
            if self._position_esc_listener is not None:
                try:
                    self._position_esc_listener.stop()
                except Exception:
                    pass
                self._position_esc_listener = None
            return False

        listener_ref[0] = mouse.Listener(on_click=on_click)
        listener_ref[0].start()
        self._start_position_esc_listener(finish_cancel)

    def register_hotkeys(self):
        self._register_hotkey_callback()

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

            if self.slot1_pos == (0, 0) or self.slot2_pos == (0, 0):
                self.status_var.set("Bitte zuerst beide Positionen aufnehmen")
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
        move_steps: int,
        step_delay: int,
        settle_delay: int,
        use_alt: bool = False,
    ) -> None:
        start_x, start_y = int(start_pos[0]), int(start_pos[1])
        end_x, end_y = int(end_pos[0]), int(end_pos[1])

        self._set_mouse_pos((start_x, start_y))

        if use_alt:
            pynput_keyboard.press(Key.alt)

        pynput_mouse.press(MouseButton.left)

        for i in range(1, move_steps + 1):
            if self.stop_flag:
                break
            t = i / move_steps
            x = int(round(start_x + (end_x - start_x) * t))
            y = int(round(start_y + (end_y - start_y) * t))
            self._set_mouse_pos((x, y))
            timing.vsleep(
                step_delay, stop_check=lambda: self.stop_flag, variance_pct=0)

        try:
            pynput_mouse.release(MouseButton.left)
        except Exception:
            pass
        timing.vsleep(
            settle_delay, stop_check=lambda: self.stop_flag, variance_pct=0)

        if use_alt:
            try:
                pynput_keyboard.release(Key.alt)
            except Exception:
                pass
        timing.vsleep(
            settle_delay, stop_check=lambda: self.stop_flag, variance_pct=0)

    def _run_slot_swap_sequence(self, timings: dict[str, Any]) -> None:
        move_distance = max(0, int(timings.get("move_left_px", 120)))
        move_steps = max(1, int(timings.get("move_steps", 12)))
        step_delay = max(0, int(timings.get("step_delay", 5)))
        settle_delay = max(0, int(timings.get("settle_delay", 25)))
        repeat_count = max(1, int(timings.get("repeat_count", 1)))
        tab_hold_ms = max(0, int(timings.get("tab_hold_ms", 50)))

        def _cleanup() -> None:
            try:
                pynput_mouse.release(MouseButton.left)
            except Exception:
                pass
            try:
                pynput_keyboard.release(Key.alt)
            except Exception:
                pass

        _cleanup()

        # Open inventory once before the repeated sequence starts.
        pynput_keyboard.press(Key.tab)
        timing.vsleep(
            tab_hold_ms, stop_check=lambda: self.stop_flag, variance_pct=0)
        pynput_keyboard.release(Key.tab)
        timing.vsleep(
            settle_delay, stop_check=lambda: self.stop_flag, variance_pct=0)

        for _ in range(repeat_count):
            if self.stop_flag:
                break

            # 1) Slot 1: hold Alt + LMB and drag to the left.
            slot1_x, slot1_y = int(self.slot1_pos[0]), int(self.slot1_pos[1])
            self._drag_line(
                (slot1_x, slot1_y),
                (slot1_x - move_distance, slot1_y),
                use_alt=True,
                move_steps=move_steps,
                step_delay=step_delay,
                settle_delay=settle_delay,
            )

            if self.stop_flag:
                break

            # 2) Slot 2: hold Alt + LMB and drag to the left.
            slot2_x, slot2_y = int(self.slot2_pos[0]), int(self.slot2_pos[1])
            self._drag_line(
                (slot2_x, slot2_y),
                (slot2_x - move_distance, slot2_y),
                use_alt=True,
                move_steps=move_steps,
                step_delay=step_delay,
                settle_delay=settle_delay,
            )

            if self.stop_flag:
                break

            # 3) Slot 1: plain drag back to slot 2.
            self._drag_line(
                self.slot1_pos,
                self.slot2_pos,
                move_steps=move_steps,
                step_delay=step_delay,
                settle_delay=settle_delay,
                use_alt=False,
            )

            if self.stop_flag:
                break

            timing.vsleep(
                settle_delay, stop_check=lambda: self.stop_flag, variance_pct=0)

        _cleanup()

    def run_macro(self):
        try:
            if self.macro_events:
                self._play_loaded_macro()
            else:
                timings = {
                    "move_left_px": self.move_left_px_var.get(),
                    "move_steps": self.move_steps_var.get(),
                    "step_delay": self.step_delay_var.get(),
                    "settle_delay": self.settle_delay_var.get(),
                    "repeat_count": self.repeat_count_var.get(),
                }
                self._run_slot_swap_sequence(timings)
        except Exception as e:
            self.status_var.set(f"Fehler: {e}")
            print(f"[SLOT-SWAP] Error: {e}")
        finally:
            self.running = False
            self.stop_flag = False
            self.cooldown_until = int(time.time() * 1000) + 800
            self.root.after(0, lambda: self.toggle_btn.config(text="Start"))
            self.root.after(0, lambda: self.status_var.set("Ready"))

    def _play_loaded_macro(self) -> None:
        macro = self.macro_data or {}
        events = self.macro_events
        if not events:
            raise ValueError("No loaded macro events")

        speed = float(macro.get("speed", 1.0) or 1.0)
        keep_timing = bool(macro.get("keep_timing", False))

        key_map = {
            "alt_l": Key.alt_l,
            "alt_r": Key.alt_r,
            "ctrl": Key.ctrl,
            "ctrl_l": Key.ctrl_l,
            "ctrl_r": Key.ctrl_r,
            "shift": Key.shift,
            "shift_l": Key.shift_l,
            "shift_r": Key.shift_r,
            "tab": Key.tab,
            "esc": Key.esc,
            "enter": Key.enter,
            "space": Key.space,
            "page_up": Key.page_up,
            "page_down": Key.page_down,
            "page up": Key.page_up,
            "page down": Key.page_down,
        }

        button_map = {
            "left": MouseButton.left,
            "right": MouseButton.right,
            "middle": MouseButton.middle,
        }

        prev_time = None
        for event in events:
            if self.stop_flag:
                break

            current_time = float(event.get("time", 0.0) or 0.0)
            if prev_time is not None:
                delta_ms = max(0.0, current_time - prev_time)
                if keep_timing:
                    self.vsleep(int(delta_ms / max(speed, 0.0001)))
                else:
                    self.vsleep(int(delta_ms / max(speed, 0.0001)))
            prev_time = current_time

            event_type = event.get("type")
            if event_type == "key":
                key_name = str(event.get("key", "")).lower()
                key_obj = key_map.get(key_name, key_name)
                if bool(event.get("down", True)):
                    pynput_keyboard.press(key_obj)
                else:
                    pynput_keyboard.release(key_obj)
            elif event_type == "click":
                x = int(event.get("x", 0))
                y = int(event.get("y", 0))
                button_name = str(event.get("button", "left")).lower()
                button = button_map.get(button_name, MouseButton.left)
                try:
                    pynput_mouse.position = (x, y)
                except Exception:
                    pass
                try:
                    ctypes.windll.user32.SetCursorPos(x, y)
                except Exception:
                    pass
                if bool(event.get("down", True)):
                    pynput_mouse.press(button)
                else:
                    pynput_mouse.release(button)

        pynput_keyboard.release(Key.alt)
        pynput_keyboard.release(Key.ctrl)
        pynput_keyboard.release(Key.shift)
        pynput_mouse.release(MouseButton.left)

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
